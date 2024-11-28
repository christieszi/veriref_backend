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

@app.route("/")
def index():
    return "Hello World!"

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

    short_answer = asyncio.run(ask(ask_question("Given the fact that " + input_data + ". Is it true that" + text_to_verify + "? Reply with a short answer: 'Correct, 'Incorrect', or 'Cannot say', please")))
    output = asyncio.run(ask(ask_question("Given the fact that " + input_data + ". Why is it true or not that" + text_to_verify + "? Explain how you arrived to the answers in steps.")))

    # Return extracted text along with processed second input
    return jsonify({"shortAnswer": f"{short_answer}", "explanation": f"{output}"})
 
if __name__=='__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)