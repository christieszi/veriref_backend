# importing Flask and other modules
from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from flask_cors import CORS
import asyncio
from utils import mistral_stream, mistral, ask_question
import PyPDF2
import os
from bs4 import BeautifulSoup
import requests
from werkzeug.utils import secure_filename
 
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

# async def ask(prompt,stream=False):

#     sampling_params = {
#         "max_tokens": 200,
#         "temperature":1,
#     }
#     if stream:
        
#         async for line in mistral_stream(prompt=prompt,sampling_params=sampling_params,stream=True):
#             text=line.decode('utf-8')
#             print(text,end='',flush=True)
#     else:
#         result = await mistral(prompt,sampling_params=sampling_params)
#         return result['text']
 
# # A decorator used to tell the application
# # which URL is associated function
# @app.route('/standard', methods =["GET", "POST"])
# def standard():
#     if request.method == "POST":
#        input_data = str(request.form.get("data"))
#        statement = str(request.form.get("statement"))
#        output = asyncio.run(ask(ask_question("Given the fact that " + input_data + ". Is it true that" + statement + "?")))
#        return render_template("form.html", output=output)
#     return render_template("form.html", output='')

# @app.route('/', methods=['GET', 'POST'])
# def upload_or_input():
#     if request.method == 'POST':
#         if request.form.get('reset'):
#             session.clear() 
#             return redirect(url_for('upload_or_input'))

#         input_data = None
#         source_text = None
#         if 'source_file' in request.files and request.files['source_file'].filename != '':

#         elif 'source_url' in request.form and request.form['source_url'].strip() != '':
#             source_url = request.form['source_url']
#             session['source_url'] = source_url
#             response = requests.get(source_url)
#             response.raise_for_status()
#             input_data = BeautifulSoup(response.content, "html.parser").get_text()

#         elif 'source_text' in request.form and request.form['source_text'].strip() != '':
#             source_text = request.form['source_text']
#             input_data = source_text


#         # Form 2: Mandatory Text Input
#         to_verify = request.form.get('to_verify')
#         if not to_verify.strip():
#             return render_template('upload.html', error="Please enter text in the second form.")
        
#         session['source_text'] = source_text
#         session['to_verify'] = to_verify

#         short_answer = asyncio.run(ask(ask_question("Given the fact that " + input_data + ". Is it true that" + to_verify + "? Reply with 'Yes', 'No', or 'Cannot say', please")))
#         output = asyncio.run(ask(ask_question("Given the fact that " + input_data + ". Why is it true or not that" + to_verify + "?")))

#         return render_template('upload.html', short_answer=short_answer, output=output, source_url=source_url, source_text=source_text, to_verify=to_verify)
    
#     source_url = session.get('source_url', None)
#     source_text = session.get('source_text', None)
#     to_verify = session.get('to_verify', None)

#     return render_template('upload.html', source_url=source_url, source_text=source_text, to_verify=to_verify)

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

@app.route('/process', methods=['POST'])
def process_inputs():
    # Handle file upload
    source_file = request.files.get("sourceFile")
    source_text = request.form.get("sourceTextInput")
    text_to_verify = request.form.get("toVerify")

    if source_file:
        filename = secure_filename(source_file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        source_file.save(file_path)  # Save the file temporarily

        # Simulate extracting text from the PDF
        extracted_text = f"Simulated text from {filename}"  # Replace with real extraction logic
        print(f"Uploaded file saved to: {file_path}")

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Extract text from PDF
        input_data = extract_text_from_pdf(filepath)

        # Delete the file after processing
        try:
            os.remove(filepath)
        except Exception as e:
            return render_template('upload.html', error=f"Error deleting file: {e}")
        
    elif source_text:
        input_data = source_text
    else:
            file = request.files['source_file']
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Extract text from PDF
            input_data = extract_text_from_pdf(filepath)

            # Delete the file after processing
            try:
                os.remove(filepath)
            except Exception as e:
                return render_template('upload.html', error=f"Error deleting file: {e}") = "No file or source uploaded uploaded."

    # Return extracted text along with processed second input
    return jsonify({"processedText": f"{input_data} | Additional Input: {text_to_verify}"})
 
if __name__=='__main__':
   app.run()