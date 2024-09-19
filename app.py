from flask import Flask, request, jsonify
import requests
import tempfile
import os
from PyPDF2 import PdfReader
from docx import Document
import magic  # We'll use python-magic for better file type detection

app = Flask(__name__)

def download_file(url):
    response = requests.get(url)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1]) as temp_file:
            temp_file.write(response.content)
            return temp_file.name
    return None

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

@app.route('/extract', methods=['POST'])
def extract_text():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    file_path = download_file(url)
    if not file_path:
        return jsonify({"error": "Failed to download file"}), 400

    try:
        # Use python-magic to detect file type
        file_type = magic.from_file(file_path, mime=True)
        
        if file_type == 'application/pdf':
            text = extract_text_from_pdf(file_path)
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            text = extract_text_from_docx(file_path)
        else:
            return jsonify({"error": f"Unsupported file format: {file_type}"}), 400

        os.unlink(file_path)  # Delete the temporary file
        return jsonify({"text": text})
    except Exception as e:
        os.unlink(file_path)  # Delete the temporary file
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
