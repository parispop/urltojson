import os
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
from bs4 import BeautifulSoup

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
    elif file_extension == '.docx':
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    else:
        raise ValueError("Unsupported file format")
    
    return text

@app.route('/extract', methods=['POST'])
def extract_text_from_url():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        response = requests.get(url)
        response.raise_for_status()

        filename = secure_filename(os.path.basename(url))
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        with open(file_path, 'wb') as file:
            file.write(response.content)

        if not allowed_file(filename):
            os.remove(file_path)
            return jsonify({"error": "Unsupported file format"}), 400

        extracted_text = extract_text(file_path)
        os.remove(file_path)

        return jsonify({"text": extracted_text})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@app.route('/htmlextract', methods=['GET', 'POST'])
def extract_content():
    if request.method == 'POST':
        url = request.json.get('url')
    else:  # GET method
        url = request.args.get('url')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the HTML content
        html_content = str(soup)

        # Return the content in a JSON object
        return jsonify({"page_content": html_content})

    except requests.RequestException as e:
        return jsonify({"error": f"Error fetching URL: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
