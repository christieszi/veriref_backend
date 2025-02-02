# importing Flask and other modules
from flask import Flask, request, render_template, jsonify, Response, send_file
from flask_cors import CORS
import asyncio
from utils import *
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
                     r"/launch_source_job/*": {"origins": "*"},
                     r"/launch_sentence_job/*": {"origins": "*"},
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

jobs = {} 
# Example: {"job_id": {"references": [], "sentences": [], "time_submitted": TODO}}
# {"job_id": {"source_text": [], "sources": [], "sentence": str, "claims" : [], "sentence_index": int, "time_submitted": TODO}}
# {"job_id": {"sentence": str, "sources": [], "sentence_index": int, "time_submitted": TODO}}


@app.route('/launch_processing_job/<job_id>')
def launch_processing_job(job_id):
    def generate(doc_references, sentences_with_citations):
        yield ("data: " + json.dumps({
            "messageType": "sentences",
            "sentences": [{"sentence": sentence,"claims": [],"sources": []} for sentence, _ in sentences_with_citations.items()]
        }) + "\n\n")

        for sentence_index, (sentence, source_numbers) in enumerate(sentences_with_citations.items()): 
            source_text = ""
            sources = [] 

            for source_number in source_numbers:
                if source_number and doc_references.get(source_number, None):
                    try:
                        source = doc_references[source_number]
                        source_text += get_source_text_from_link(source)
                        source_text += "\n"
                        sources.append(source)
                    except:
                        source_text = source_text

            yield from process_sentence(None, source_text, sentence, sentence_index)
 
        yield "data: " + json.dumps({"messageType": "end"}) + "\n\n"
        jobs.pop(job_id)

    doc_references = jobs[job_id]["references"]
    sentences_with_citations = jobs[job_id]["sentences"]

    return Response(generate(doc_references, sentences_with_citations), content_type='text/event-stream')

@app.route('/launch_source_job/<job_id>')
def launch_source_job(job_id):
    def generate(source_text, sources, sentence, claims, sentence_index): 
        for source in sources: 
            try:
                source_text += get_source_text_from_link(source)
                source_text += "\n"
            except:
                source_text = source_text

        yield from process_sentence(claims, source_text, sentence, sentence_index)
        yield "data: " + json.dumps({"messageType": "end"}) + "\n\n"

        jobs.pop(job_id)
    
    job = jobs[job_id]
    source_text = job['source_text']
    sources = job['sources']
    sentence = job['sentence']
    claims = job['claims']
    sentence_index = job['sentence_index']

    return Response(generate(source_text, sources, sentence, claims, sentence_index), content_type='text/event-stream')

@app.route('/launch_sentence_job/<job_id>')
def launch_sentence_job(job_id):
    def generate(sentence, sources, sentence_index):
        source_text = ""
        for source in sources: 
            try:
                source_text += get_source_text_from_link(source)
                source_text += "\n"
            except:
                source_text = source_text
        yield from process_sentence(None, source_text, sentence, sentence_index)
 
        yield "data: " + json.dumps({"messageType": "end"}) + "\n\n"
        jobs.pop(job_id)

    sentence = jobs[job_id]["sentence"]
    sources = jobs[job_id]["sources"]
    sentence_index = jobs[job_id]["sentence_index"]

    return Response(generate(sentence, sources, sentence_index), content_type='text/event-stream')


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

    output = asyncio.run(ask(ask_question("Given input text :'" + source_text + "'. Given claim: '" + claim + "'. " + prompt)))
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
    claims = json.loads(request.form.get("claims"))
    sentence_index = json.loads(request.form.get("sentenceIndex"))

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"source_text": source_text, "sources": sources, "sentence": sentence, "claims" : claims, "sentence_index": sentence_index}
    return jsonify({"jobId": job_id})      

@app.route('/analyse_sentence', methods=['POST'])
def analyse_sentence():
    print("I start anaylsing")
    sources = json.loads(request.form.get('sources'))
    sentence = request.form.get('sentence')
    print(sources)
    sentence_index = json.loads(request.form.get("sentenceIndex"))

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"sources": sources, "sentence": sentence, "sentence_index": sentence_index}
    print("created a job")
    return jsonify({"jobId": job_id})     

@app.route('/generate_pdf', methods=['POST'])
def upload():
    file_input = request.files.get("file")
    text_input = request.form.get("textInput")
    sentences = json.loads(request.form.get("sentences")) 

    file_path = None
    if file_input:
        # Handle PDF file upload
        filename = secure_filename(file_input.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_input.save(file_path)
        # return send_file(filepath, as_attachment=True)

    elif text_input:
        # Handle text input and convert to PDF using Fitz

        file_path = 'output.pdf'

        # Create PDF using FPDF
        pdf = FPDF()
        pdf.add_page()

        # Set font and size
        pdf.set_font('Arial', size=12)

        # Set the width of the multi_cell (page width minus margin)
        page_width = pdf.w - 2 * pdf.l_margin
        pdf.multi_cell(page_width, 10, text_input)

        # Save the PDF
        pdf.output(file_path)
        # return send_file(pdf_path, as_attachment=True)
    
    def get_sentence_classification(sentence_json): 
        comment = "The sentence can be split into the following claims: \n\n"
        sentence = sentence_json['sentence']
        classification =  0
        claims = sentence_json['claims']
        claims_mappings = []
        for claim_json in claims:
            claim = claim_json['claim']
            claim_type = claim_json['type'] 
            claim_parts = claim_json['sentenceParts']
            explanation = claim_json['explanation']
            if classification == 2 or claim_type == 2: 
                comment += claim 
                comment += " - INCORRECT \n" 
                comment += claim_json['explanation'] 
                comment += " + " + str(claim_parts)
                comment += "\n\n"
                classification = 2 
            elif classification == 3 or claim_type == 3 or claim_type == 4: 
                comment += claim 
                comment += " - COULD NOT CHECK \n" 
                comment += claim_json['explanation']
                comment += " + " + str(claim_parts)
                comment += "\n\n"
                classification = 3 
            elif claim_type == 1:
                classification = 1 
                comment += claim 
                comment += " - CORRECT \n" 
                comment += claim_json['explanation']
                comment += " + " + str(claim_parts)
                comment += "\n\n"
            claims_mappings.append((claim, claim_type, explanation, claim_parts))

        # return sentence, classification, comment
        return sentence, claims_mappings

    processed_sentences = [get_sentence_classification(sentence_json) for sentence_json in sentences]

    doc = fitz.open(file_path)

    for page_num in range(doc.page_count):
        sentenceNotFound = False 

        while (not sentenceNotFound) and len(processed_sentences) > 0:

            page = doc.load_page(page_num)

            cur_sentence, subs_to_claim_mappings = processed_sentences[0]

            text_instances = page.search_for(cur_sentence)
            
            if text_instances:
                for text_instance in text_instances:
                    sentence_rect = text_instance
                    # Highlight specific words within the sentence's bounding box
                    for (claim, claim_type, explanation, parts) in subs_to_claim_mappings:
                        if isinstance(parts, str): 
                            word = parts 
                            word_instances = page.search_for(word)  # Search for the word
                            if word_instances is None: 
                                print("WHY?")
                                print(claim)
                                print(word)
                            else:
                                for word_inst in word_instances:
                                    if (word_inst.intersects(sentence_rect)):
                                        word_highlight = page.add_highlight_annot(word_inst)
                                        if claim_type == 1:
                                            word_highlight.set_colors(stroke=(0.6, 1, 0.6))  # Light yellow highlight
                                            answer = "CORRECT"
                                            colour = (0.6, 1, 0.6)
                                        elif claim_type == 2:
                                            word_highlight.set_colors(stroke=(1, 0.6, 0.6))
                                            answer = "INCORRECT"
                                            colour = (1, 0.6, 0.6)
                                        else:
                                            word_highlight.set_colors(stroke=(1, 1, 0.6))
                                            answer = "COULD NOT VERIFY"
                                            colour = (1, 1, 0.6)
                                        word_highlight.update()
                                        comment_position = fitz.Rect(word_inst.x0, word_inst.y0, word_inst.x1, word_inst.y1)
                                        comment = claim
                                        comment += "\n"
                                        comment += answer 
                                        comment += "\n"
                                        comment += explanation

                                        page.add_freetext_annot(comment_position, comment, fill_color = colour, fontsize=12)
                        else:
                            for word in parts:
                                word_instances = page.search_for(word)  # Search for the word
                                for word_inst in word_instances:
                                    if (word_inst.intersects(sentence_rect)):
                                        word_highlight = page.add_highlight_annot(word_inst)
                                        if claim_type == 1:
                                            word_highlight.set_colors(stroke=(0.6, 1, 0.6))  # Light yellow highlight
                                            answer = "CORRECT"
                                            colour = (0.6, 1, 0.6)
                                        elif claim_type == 2:
                                            word_highlight.set_colors(stroke=(1, 0.6, 0.6))
                                            answer = "INCORRECT"
                                            colour = (1, 0.6, 0.6)
                                        else:
                                            word_highlight.set_colors(stroke=(1, 1, 0.6))
                                            answer = "COULD NOT VERIFY"
                                            colour = (1, 1, 0.6)
                                        word_highlight.update()
                                        comment_position = fitz.Rect(word_inst.x0, word_inst.y0, word_inst.x1, word_inst.y1)
                                        comment = claim
                                        comment += "\n"
                                        comment += answer 
                                        comment += "\n"
                                        comment += explanation

                                        page.add_freetext_annot(comment_position, comment, fill_color = colour, fontsize=12)

                del processed_sentences[0]
            else: 
                sentenceNotFound = True

    # Save the modified PDF
    doc.save("highlighted_output.pdf")
    return send_file("highlighted_output.pdf", as_attachment=True)
    # return 'No file or text provided.', 401

if __name__=='__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)