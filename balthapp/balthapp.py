# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 1.0
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - API endpoints and controller
"""

# From the flask_app folder:
# Activate the virtual environnement :
# >> source venv/bin/activate
# Run Flask server :
# >> FLASK_APP=balthapp.py flask --debug run


import os
from uuid import uuid4

import service
from flask import Flask, request, send_file
from markupsafe import escape
from werkzeug.utils import secure_filename

# Crate an instance of our Flask API
flask_app = Flask(__name__)
flask_app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Fixe la taille maximale des PDF téléchargé à 10MO
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
# The path to the folder where are uploaded the PDFs
PDF_FOLDER_PATH = "storage/temp"
TXT_FOLDER_PATH = "storage/files"
PDF_EXT = '.pdf'
TXT_EXT = '.txt'


@flask_app.route('/')
def hello():
    return "Welcome on the Balth Mehus PDF API :)"


@flask_app.route('/documents', methods=['POST'])
def upload_pdf():
    # -------------------- CHECKIN -------------------------
    # Verify the post payload
    try:
        # Get the file in the request
        pdf_file = request.files['pdf_file']
    except KeyError:
        return {"error": "Invalid payload, only POST on 'pdf_file' key."}, 422

    # Verify that the document post is not empty
    if not service.file_provided(file=pdf_file):
        return {"error": "No pdf file provided."}, 400
    # Verify that the file has the .pdf extension
    if not service.valid_file_ext(file=pdf_file, ext=PDF_EXT):
        return {"error": "Invalid file EXT. Please upload a '" + PDF_EXT + "' file."}, 415
    # Verify that file is PDF MIMETYPE
    if not service.valid_file_mimetype(file=pdf_file, mimetype='PDF'):
        return {"error": "Invalid file type. Please upload a PDF file."}, 415
    # Verify the document size
    if not service.valid_file_size(file=pdf_file, max_size=MAX_FILE_SIZE):
        return {"error": "File size exceeded the maximum limit (" + str(MAX_FILE_SIZE_MB) + " mb)."}, 413
    # -------------------- TREATMENT -------------------------
    # Create a unique ID to identify the pdf document
    pdf_id = str(uuid4())
    pdf_path = os.path.join(PDF_FOLDER_PATH, pdf_id + PDF_EXT)
    txt_path = os.path.join(TXT_FOLDER_PATH, pdf_id + TXT_EXT)
    txt_link = str(os.path.join(request.url_root, txt_path))
    try:
        # Temporary save the PDF file in our storage to extract its contents further
        pdf_file.save(pdf_path)
        # Extraction of the metadata and the text of the PDF file
        extract = service.extract_data(pdf_id + PDF_EXT)
        # -------------------- STORING -------------------------
        # Prepare the data to be stored in the DB
        data_to_store = {
            'id': str(pdf_id),
            'name': str(secure_filename(pdf_file.filename)),
            'data': str(extract['metadata']),
            'link': str(txt_link),
            'state': 'SUCCESS'
        }
        # Create a new entry in our pdf table
        service.insert_pdf_info_in_db(data_to_store)
        # The process is definitively achieved
        # Save the txt extracted from PDF in a file txt
        with open(txt_path, "w") as txt_file:
            txt_file.write(extract['pdf_text'])
        # -------------------- CLEANING -------------------------
        # Remove the PDF from storage when extraction is completed
        os.remove(pdf_path)
    except Exception as err:
        # Remove the PDF from storage
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        # Remove the PDF entry from DB
        if service.get_pdf_info_in_db(pdf_id):
            service.delete_pdf_in_db(pdf_id)
        return {"error": err}, 500
    return {"_id": pdf_id}, 200


@flask_app.route('/documents/<pdf_id>', methods=['GET'])
def get_info(pdf_id):
    pdf_id = escape(pdf_id)
    # Get pdf info in DB with pdf_id
    pdf = service.get_pdf_info_in_db(pdf_id)
    # Check if the pdf entry exists in the DB
    if pdf:
        # Update the state because the customer get the result
        # Useful in order to improve the code later with a cleaner system
        service.update_pdf_task_state_in_db(str(pdf_id), "GET")
        # Initialize data to return
        return {
            "_id": pdf.id,
            "name": pdf.name,
            "link": pdf.link,
            "data": pdf.data,
            "created_at": str(pdf.created_at)
            }, 200
    else:
        return {"error": "PDF not found. Thanks to verify the id."}, 204


@flask_app.route('/text/<pdf_id>')
def get_text(pdf_id):
    pdf_id = escape(pdf_id)
    txt_path = os.path.join(TXT_FOLDER_PATH, pdf_id + TXT_EXT)
    # If exists, we return the content of the text extracted from the pdf
    if service.check_id(txt_path):
        return send_file(txt_path, as_attachment=True, mimetype='text/plain'), 200
    return {"error": "Invalid ID ; No text file corresponding."}, 404


if __name__ == '__main__':
    flask_app.run()
