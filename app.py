# importing Flask and other modules
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import asyncio
from utils import mistral_stream, mistral, ask_question
import PyPDF2
import os
from bs4 import BeautifulSoup
import requests
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
import re
 
# Flask constructor
app = Flask(__name__)   
CORS(app)

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
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text()
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
    source_file = request.files.get("file")
    source_text = request.form.get("sourceTextInput")
    text_to_verify = request.form.get("toVerify")

    if source_file:
        filename = secure_filename(source_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        source_file.save(filepath)

        # Extract text from PDF
        input_data = extract_text_from_pdf(filepath)

        # Delete the file after processing
        try:
            os.remove(filepath)
        except Exception as e:
            return render_template('upload.html', error=f"Error deleting file: {e}")
    elif source_text:
        source_text = source_text.strip()
        if urlparse(source_text).scheme:
            response = requests.get(source_text)
            response.raise_for_status()
            input_data = BeautifulSoup(response.content, "html.parser").get_text()
        else:
            input_data = source_text
    else:
        input_data = None

    short_answer = asyncio.run(ask(ask_question("Given the fact that " + input_data + ". Is it true that" + text_to_verify + "? Reply with 'Correct, 'Incorrect', or 'Cannot say', please")))
    output = asyncio.run(ask(ask_question("Identify all the separate claims or facts in the following text '" + text_to_verify + "'. Output only enumerated claims and facts without any extra information.")))
    claims = extract_list_elements(output)
    claims_output = []
    for claim in claims: 
        answer = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' say whether the following claim '" + claim + "' is true or false? Reply with 'Correct', 'Incorrect', or 'Cannot Say'.")))
        answer = answer.lstrip()
        if answer == "Correct" or "Correct" in answer: 
            explanation = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' explain why the following claim '" + claim + "' is correct.")))
            sentences = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' which specific setences support the following claim '" + claim + "'? Output only enumerated sentences without any extra information.")))
            sentences = (extract_sentences_elements(sentences))

        elif answer == "Incorrect" or "Incorrect" in answer:
            explanation = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' explain why the following claim '" + claim + "' is incorrect.")))
            sentences = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' give specific setences which contradict the following claim '" + claim + "'. Output only enumerated sentences without any extra information.")))
            sentences = (extract_sentences_elements(sentences))       
        else:
            explanation = asyncio.run(ask(ask_question("Based only on the following text '" + input_data + "' explain why it is impossible to say whether following claim '" + claim + "' is correct or incorrect.")))    
            sentences = []

        claims_output.append([claim, answer, explanation, sentences])

    # Return extracted text along with processed second input
    return jsonify({"shortAnswer": f"{short_answer}", "explanation": f"{output}", "claims": claims_output})
 
if __name__=='__main__':
   app.run()