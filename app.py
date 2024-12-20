# importing Flask and other modules
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import asyncio
from utils import mistral_stream, mistral, ask_question, extract_references
import fitz
import os
from bs4 import BeautifulSoup
import requests
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
import re
 
# Flask constructor
app = Flask(__name__)   
CORS(app, resources={r"/process": {"origins": "http://localhost:3000"}})

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure secret key for session
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

@app.route('/process', methods=['POST'])
def process_inputs():
    # Handle file upload
    file = request.files.get("file")
    # source_text = request.form.get("sourceTextInput")
    text_input = request.form.get("textInput")

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Extract text from PDF
        text_to_verify = extract_text_from_pdf(filepath)

        try:
            os.remove(filepath)
        except Exception as e:
            return render_template('upload.html', error=f"Error deleting file: {e}")
    else:
        text_to_verify = text_input

    references, sentences_with_citations = extract_references(text_to_verify)

    sentences_processed = [] 
    for sentence, source_numbers in sentences_with_citations.items(): 
        source_text = ""
        claims_processed = []

        for source_number in source_numbers:
            if source_number and references.get(source_number):
                try:
                    response = requests.get(references[source_number])
                    response.raise_for_status()
                    input_data = BeautifulSoup(response.content, "html.parser").get_text()
                    source_text += (input_data)
                    source_text += "\n"
                except:
                    source_text = source_text

        if len(source_text) == 0: 
            claim_dict = {
                "claim": sentence,
                "answer": "Could not check",
                "type": 3,
                "explanation": "Could not access source",
                "references": []
            }
            claims_processed.append(claim_dict)
        else:
            claims = asyncio.run(ask(ask_question("Identify all the separate claims or facts in the following sentence '" + sentence + "'. Output only enumerated claims and facts without any extra information.")))
            claims = extract_list_elements(claims)
            for claim in claims: 
                answer = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' say whether the following claim '" + claim + "' is true or false? Reply with 'Correct', 'Incorrect', or 'Cannot Say'.")))
                answer = answer.lstrip()
                if answer == "Correct" or "Correct" in answer: 
                    classification = 1
                    explanation = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' explain why the following claim '" + claim + "' is correct.")))
                    references = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' which specific setences from this text support the following claim '" + claim + "'? Output only enumerated sentences without any extra information.")))
                elif answer == "Incorrect" or "Incorrect" in answer:
                    classification = 2
                    explanation = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' explain why the following claim '" + claim + "' is incorrect.")))
                    references = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' give specific setences from the text which contradict the following claim '" + claim + "'. Output only enumerated sentences without any extra information.")))     
                else:
                    classification = 3
                    explanation = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' explain why it is impossible to say whether following claim '" + claim + "' is correct or incorrect.")))    
                    references = []
                claim_dict = {
                    "claim": claim,
                    "answer": answer,
                    "type": classification,
                    "explanation": explanation,
                    "references": references
                }
                claims_processed.append(claim_dict)

        sentences_processed.append({
            "sentence": sentence,
            "claims": claims_processed
        })

    return jsonify({"sentences": sentences_processed})
 
if __name__=='__main__':
   app.run()