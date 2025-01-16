# importing Flask and other modules
from flask import Flask, request, render_template, jsonify, Response, send_file
from flask_cors import CORS
import asyncio
from utils import mistral_stream, mistral, ask_question, extract_references, get_source_text_from_link, extract_url
import fitz
import os
import re
from werkzeug.utils import secure_filename
import json
import uuid
from fpdf import FPDF
 
app = Flask(__name__)   
CORS(app, resources={r"/process": {"origins": "*"}, 
                     r"/prompt": {"origins": "*"}, 
                     r"/add_source": {"origins": "*"},
                     r"/analyse_sentence": {"origins": "*"},
                     r"/launch_processing_job/*": {"origins": "*"},
                     r"/stream": {"origins": "*"},
                     r"/generate_pdf": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24)

async def ask(prompt,stream=False):

    sampling_params = {
        "max_tokens": 200,
        "temperature":1,
    }
    if stream:
        
        async for line in mistral_stream(prompt=prompt,sampling_params=sampling_params,stream=True):
            text=line.decode('utf-8')
            print(text,end='',flush=True)
    else:
        result = await mistral(prompt,sampling_params=sampling_params)
        return result['text']

def extract_text_from_pdf(pdf_path):
    text = ''
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:    
            text += page.get_text()    
    except Exception as e:
        text = f"Error reading PDF: {e}"
    return text

def extract_list_elements(text):
    pattern = r'\d+\.\s(.*?)(?=\s\d+\.\s|$)'
    matches = re.findall(pattern, text)
    return matches

def extract_sentences_elements(text):
    pattern = r'\d+\.\s+"(.*?)"'
    matches = re.findall(pattern, text)
    return matches

jobs = {} # Example: {"job_id": {"references": [], "sentences": [], "time_submitted": TODO}}

@app.route('/launch_processing_job/<job_id>')
def launch_processing_job(job_id):
    def generate(doc_references, sentences_with_citations):
        yield ("data: " + json.dumps({
            "messageType": "sentences",
            "sentences": [{"sentence": sentence,"claims": [],"sources": []} for sentence, _ in sentences_with_citations.items()]
        }) + "\n\n")

        sentences_processed = [] 
        for i, (sentence, source_numbers) in enumerate(sentences_with_citations.items()): 
            source_text = ""
            claims_processed = []
            sources = [] 

            for source_number in source_numbers:
                if source_number and doc_references[source_number]:
                    try:
                        source = doc_references[source_number]
                        source_text += get_source_text_from_link(source)
                        source_text += "\n"
                        sources.append(source)
                    except:
                        source_text = source_text

            if len(source_text) == 0: 
                claim_dict = {
                    "claim": sentence,
                    "answer": "Could not check",
                    "type": 4,
                    "explanation": "Could not access source",
                    "references": None
                }
                yield ("data: " + json.dumps({
                    "messageType": "claimNoResource",
                    "claim": claim_dict,
                    "sentenceIndex": i
                }) + "\n\n")

            else:
                claims = asyncio.run(ask(ask_question("Identify all the separate claims or facts in the following sentence '" + sentence + "'. Output only enumerated claims and facts without any extra information.")))
                claims = extract_list_elements(claims)
                yield ("data: " + json.dumps({
                    "messageType": "claims",
                    "claims": ([{
                    "claim": claim,
                    "answer": None,
                    "type": 5,
                    "explanation": None,
                    "references": []} for claim in claims]),
                    "sentenceIndex": i
                }) + "\n\n")

                for j, claim in enumerate(claims): 
                    answer = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' say whether the following claim '" + claim + "' is true or false? Reply with 'Correct', 'Incorrect', or 'Cannot Say'.")))
                    answer = answer.lstrip()
                    claim_dict = {
                        "claim": claim,
                        "answer": answer,
                        "type": None,
                        "explanation": None,
                        "references": None,
                    }
                    if answer == "Correct" or "Correct" in answer: 
                        claim_dict['type'] = 1
                        yield ("data: " + json.dumps({
                            "messageType": "claimAnswer",
                            "claim": claim_dict,
                            "sentenceIndex": i,
                            "claimIndex": j
                        }) + "\n\n")                  
                        explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why the following claim '" + claim + "' is correct.")))
                        claim_dict['explanation'] = explanation
                        yield ("data: " + json.dumps({
                            "messageType": "claimExplanation",
                            "claim": claim_dict,
                            "sentenceIndex": i,
                            "claimIndex": j
                        }) + "\n\n")                            
                        references = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' which specific setences from this text support the following claim '" + claim + "'? Output only enumerated sentences without any extra information.")))
                        claim_dict['references'] = references
                        yield ("data: " + json.dumps({
                            "messageType": "claimReferences",
                            "claim": claim_dict,
                            "sentenceIndex": i,
                            "claimIndex": j
                        }) + "\n\n")   
                    elif answer == "Incorrect" or "Incorrect" in answer:
                        claim_dict['type'] = 2
                        yield ("data: " + json.dumps({
                            "messageType": "claimAnswer",
                            "claim": claim_dict,
                            "sentenceIndex": i,
                            "claimIndex": j
                        }) + "\n\n")                           
                        explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why the following claim '" + claim + "' is incorrect.")))
                        claim_dict['explanation'] = explanation
                        yield ("data: " + json.dumps({
                            "messageType": "claimExplanation",
                            "claim": claim_dict,
                            "sentenceIndex": i,
                            "claimIndex": j
                        }) + "\n\n")   
                        references = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' give specific setences from the text which contradict the following claim '" + claim + "'. Output only enumerated sentences without any extra information.")))  
                        claim_dict['references'] = references
                        yield ("data: " + json.dumps({
                            "messageType": "claimReferences",
                            "claim": claim_dict,
                            "sentenceIndex": i,
                            "claimIndex": j
                        }) + "\n\n")     
                    else:
                        claim_dict['type'] = 3
                        yield ("data: " + json.dumps({
                            "messageType": "claimAnswer",
                            "claim": claim_dict,
                            "sentenceIndex": i,
                            "claimIndex": j
                        }) + "\n\n")    
                        explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why it is impossible to say whether following claim '" + claim + "' is correct or incorrect.")))
                        claim_dict['explanation'] = explanation
                        claim_dict['references'] = []
                        yield ("data: " + json.dumps({
                            "messageType": "claimExplanation",
                            "claim": claim_dict,
                            "sentenceIndex": i,
                            "claimIndex": j
                        }) + "\n\n")       


            sentences_processed.append({
                "sentence": sentence,
                "claims": claims_processed,
                "sources": sources
            })

        yield "data: " + json.dumps({"messageType": "end"}) + "\n\n"
        jobs.pop(job_id)

    doc_references = jobs[job_id]["references"]
    sentences_with_citations = jobs[job_id]["sentences"]

    return Response(generate(doc_references, sentences_with_citations), content_type='text/event-stream')

@app.route('/process', methods=['POST'])
def process_inputs():
    file = request.files.get("file")
    text_input = request.form.get("textInput")

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        text_to_verify = extract_text_from_pdf(filepath)
        try:
            os.remove(filepath)
        except Exception as e:
            return render_template('upload.html', error=f"Error deleting file: {e}")
    else:
        text_to_verify = text_input

    doc_references, sentences_with_citations = extract_references(text_to_verify)
    job_id = str(uuid.uuid4())

    jobs[job_id] = {"references": doc_references, "sentences": sentences_with_citations}
    return jsonify({"jobId": job_id})
 
@app.route('/prompt', methods=['POST'])
def process_prompt():
    sources = request.json['sources']
    source_text = ""
    for source in sources:
        source_text += get_source_text_from_link(source)
        source_text += "\n"

    claim = request.json['claim']['claim']
    prompt = request.json['prompt']

    output = asyncio.run(ask(ask_question("Given input text :'" + source_text + "'. And given claim: '" + claim + "'. " + prompt)))
    return jsonify({"output": output})

@app.route('/add_source', methods=['POST'])
def add_source():
    file = request.files.get("file")
    text_input = request.form.get("textInput")

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        source_text = extract_text_from_pdf(filepath)
        try:
            os.remove(filepath)
        except Exception as e:
            return render_template('upload.html', error=f"Error deleting file: {e}")
    else:
        link = extract_url(text_input)
        if link:
            source_text = get_source_text_from_link(link)
        else: 
            source_text = text_input

    sources = json.loads(request.form.get('sources'))
    sentence = request.form.get('sentence')
    for source in sources: 
        try:
            source_text += get_source_text_from_link(source)
            source_text += "\n"
        except:
            source_text = source_text

    claims = json.loads(request.form.get("claims"))
    claims_processed = [] 
    if len(source_text) == 0: 
        claim_dict = {
            "claim": sentence,
            "answer": "Could not check",
            "type": 4,
            "explanation": "Could not access source",
            "references": []
        }
        claims_processed.append(claim_dict)
    else:
        if claims[0]['type'] == 4:
            new_claims = asyncio.run(ask(ask_question("Identify all the separate claims or facts in the following sentence '" + sentence + "'. Output only enumerated claims and facts without any extra information.")))
            new_claims = extract_list_elements(new_claims)
        else:
            new_claims = [claim['claim'] for claim in claims]

        for claim in new_claims:
            answer = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' say whether the following claim '" + claim + "' is true or false? Reply with 'Correct', 'Incorrect', or 'Cannot Say'.")))
            answer = answer.lstrip()
            if answer == "Correct" or "Correct" in answer: 
                classification = 1
                explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why the following claim '" + claim + "' is correct.")))
                references = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' which specific setences from this text support the following claim '" + claim + "'? Output only enumerated sentences without any extra information.")))
            elif answer == "Incorrect" or "Incorrect" in answer:
                classification = 2
                explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why the following claim '" + claim + "' is incorrect.")))
                references = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' give specific setences from the text which contradict the following claim '" + claim + "'. Output only enumerated sentences without any extra information.")))     
            else:
                classification = 3
                explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why it is impossible to say whether following claim '" + claim + "' is correct or incorrect.")))    
                references = []
            claim_dict = {
                "claim": claim,
                "answer": answer,
                "type": classification,
                "explanation": explanation,
                "references": references
            }
            claims_processed.append(claim_dict)            

    return jsonify({"claims": claims_processed})

@app.route('/analyse_sentence', methods=['POST'])
def analyse_sentence():
    try:
        sentence = request.json['sentence'] 
        sources = request.json['sources']  
        source_text = ""
        for source in sources: 
            try:
                source_text += get_source_text_from_link(source)
                source_text += "\n"
            except:
                source_text = source_text

        claims_processed = []
        if len(source_text) == 0: 
            claim_dict = {
                "claim": sentence,
                "answer": "Could not check",
                "type": 4,
                "explanation": "Could not access source",
                "references": []
            }
            claims_processed.append(claim_dict)
        else:
            claims = asyncio.run(ask(ask_question("Identify all the separate claims or facts in the following sentence '" + sentence + "'. Output only enumerated claims and facts without any extra information.")))
            claims = extract_list_elements(claims)
            for claim in claims:
                answer = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' say whether the following claim '" + claim + "' is true or false? Reply with 'Correct', 'Incorrect', or 'Cannot Say'.")))
                answer = answer.lstrip()
                if answer == "Correct" or "Correct" in answer: 
                    classification = 1
                    explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why the following claim '" + claim + "' is correct.")))
                    references = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' which specific setences from this text support the following claim '" + claim + "'? Output only enumerated sentences without any extra information.")))
                elif answer == "Incorrect" or "Incorrect" in answer:
                    classification = 2
                    explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why the following claim '" + claim + "' is incorrect.")))
                    references = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' give specific setences from the text which contradict the following claim '" + claim + "'. Output only enumerated sentences without any extra information.")))     
                else:
                    classification = 3
                    explanation = asyncio.run(ask(ask_question("Based only on the following text '" + source_text + "' explain why it is impossible to say whether following claim '" + claim + "' is correct or incorrect.")))    
                    references = []
                claim_dict = {
                    "claim": claim,
                    "answer": answer,
                    "type": classification,
                    "explanation": explanation,
                    "references": references
                }
                claims_processed.append(claim_dict)         
        return jsonify({"claims": claims_processed})
    except Exception as e:
        return jsonify({"claims": request.json['claims']})

@app.route('/generate_pdf', methods=['POST'])
def upload():
    file_input = request.files.get("file")
    text_input = request.form.get("textInput")

    print(text_input)
    if file_input:
        # Handle PDF file upload
        filename = secure_filename(file_input.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_input.save(filepath)
        return send_file(filepath, as_attachment=True)

    elif text_input:
        print("whatafauck")
        # Handle text input and convert to PDF using Fitz

        pdf_path = 'output.pdf'

        # Create PDF using FPDF
        pdf = FPDF()
        pdf.add_page()

        # Set font and size
        pdf.set_font('Arial', size=12)

        # Set the width of the multi_cell (page width minus margin)
        page_width = pdf.w - 2 * pdf.l_margin
        pdf.multi_cell(page_width, 10, text_input)

        # Save the PDF
        pdf.output(pdf_path)
        return send_file(pdf_path, as_attachment=True)

    # return 'No file or text provided.', 401

if __name__=='__main__':
   app.run()