# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.1
# fix a bad drop of metadata entry in db
# remove the field updated_at
# change endpoint documentatio metadata
# add openApi contract
# add a route to download contract
# add a route to download text
# add a dataclass for pdf_infos in balthapp.py
# move functions (save file and remove) from balthapp.py to service.py
# update the api contract
# add the architecture design in README.md
# Fix a storage issue about saving/removing file and updating db
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - API endpoints and controller
"""

import os
from dataclasses import dataclass
from uuid import uuid4

import service
from celery import Celery
from flask import (Flask, Response, jsonify, request, send_file,
                   send_from_directory)
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from flask_limiter.util import get_remote_address
from markupsafe import escape
from werkzeug.utils import secure_filename

# Crate an instance of our Flask API
flask_app = Flask(__name__)
flask_app.config['JSONIFY_PRETTYPRINT_REGULAR']: bool = True

# Our redis server
redis_uri = "redis://localhost:6379"

# Set a limit to unique IP connexions
limiter = Limiter(
    get_remote_address,
    app=flask_app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=redis_uri,
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
)

# Set Celery queue and connect it to redis workers
celery_app = Celery('balthworker',
                    broker=redis_uri,
                    backend=redis_uri + '/0')

# Fixe la taille maximale des PDF téléchargé à 10MO
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
# The path to the folder where are uploaded the PDFs
PDF_FOLDER_PATH = "storage/temp"
TXT_FOLDER_PATH = "storage/files"
CONTRACT_PATH = "static"

PDF_EXT = '.pdf'
TXT_EXT = '.txt'


# TODO: add a config system
# TODO: add a logger system
# TODO: to avoid flooding, add a cron job each hour
#  to clean balthapp/storage/files and balthapp/storage/temp from oldest files

@dataclass
class PdfInfos:
    uid: str = ''
    name: str = ''
    data: str = ''
    link: str = ''
    task_id: str = ''
    task_state: str = ''
    pdf_path: str = ''
    txt_path: str = ''
    txt: str = ''

    def set_uid(self, pdf_id):
        uid = escape(pdf_id)
        self.uid = str(uid)

    def set_name(self, filename):
        self.name = str(secure_filename(filename))

    def set_data(self, metadata):
        self.data = str(metadata)

    def set_link(self, root):
        self.link = os.path.join(root, self.txt_path)

    def set_task_id(self, task_id):
        self.task_id = str(task_id)

    def set_task_state(self, task_state):
        self.task_state = str(task_state)

    def set_pdf_path(self, uid):
        filename = uid + PDF_EXT
        self.pdf_path = os.path.join(PDF_FOLDER_PATH, filename)

    def set_txt_path(self, uid):
        self.txt_path = os.path.join(TXT_FOLDER_PATH, uid + TXT_EXT)

    def set_txt(self, text):
        self.txt = str(text)


@flask_app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    response = jsonify(error="Too many requests, please try again later (README for more details).")
    response.status_code = 429
    return response


@flask_app.route('/')
def hello():
    """Home page : it presents the API
    ---
    responses:
        200:
        description: Returns the welcome string
    """
    return "Welcome on the Balth Mehus PDF API :) Download the api contract on /contract ", 200


@flask_app.route('/contract')
@limiter.limit("2/minute, 1/second", override_defaults=False)
def download_contract():
    """API contract : see the Openapi contract
    ---
    responses:
        200:
        description: Download le fichier api-contract.yaml
    """
    return send_from_directory(CONTRACT_PATH, 'api-contract.yaml'), 200


@flask_app.route('/documents', methods=['POST'])
@limiter.limit("10/minute, 1/second", override_defaults=False)
def upload_pdf() -> tuple[dict[str, str], int]:
    """Upload a PDF file for processing.
    Post PDF files in order to get metadata and text.
    ---
    requestBody:
        name: pdf_file
        description: The PDF file to upload
        required: true
    responses:
        201:
          summary: PDF uploaded successfully.
          description: Returns an uuid (str) which identifies the uploaded pdf file.
    """
    pdf_infos = PdfInfos()
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
    if not service.file_valid_extension(file=pdf_file, ext=PDF_EXT):
        return {"error": "Invalid file EXT. Please upload a '" + PDF_EXT + "' file."}, 415
    # Verify that file is PDF MIMETYPE
    if not service.file_valid_mimetype(file=pdf_file, mimetype='PDF'):
        return {"error": "Invalid file type. Please upload a PDF file."}, 415
    # Verify the document size
    if not service.file_valid_size(file=pdf_file, max_size=MAX_FILE_SIZE):
        return {"error": "File size exceeded the maximum limit (" + str(MAX_FILE_SIZE_MB) + " mb)."}, 413

    # -------------------- TREATMENT -------------------------
    # Create a unique ID to identify the pdf document
    pdf_id = str(uuid4())
    pdf_infos.set_uid(pdf_id)
    pdf_infos.set_pdf_path(pdf_infos.uid)

    try:
        # Temporary save the PDF file in our storage to extract its contents further
        service.fs_save_temp_pdf(pdf_file, pdf_infos.pdf_path)

        flask_app.logger.info("Invoking asynchronous method")
        # Asynchronous extraction of the metadata and the text of the PDF file
        async_task = celery_app.send_task('tasks.extract_data', args=[pdf_infos.uid + PDF_EXT])
        flask_app.logger.info(async_task.backend)
        # -------------------- STORAGE -------------------------
        pdf_infos.set_name(pdf_file.filename)
        pdf_infos.set_task_id(async_task.id)
        # Prepare the data to be stored in the DB
        data_to_store = {
            'id': pdf_infos.uid,
            'name': pdf_infos.name,
            'task_id': pdf_infos.task_id
        }
        # Create a new entry in our pdf table
        service.db_insert_pdf_info(data_to_store)
    except Exception as err:
        # -------------------- CLEANING -------------------------
        # Remove the PDF from storage
        if os.path.exists(pdf_infos.pdf_path):
            service.fs_remove_temp_pdf(pdf_infos.pdf_path)
        return {"error": str(err)}, 500
    return {"_id": pdf_infos.uid}, 201


@flask_app.route('/metadata/<pdf_id>', methods=['GET'])
@limiter.limit("20/minute, 1/second", override_defaults=False)
def get_info(pdf_id: str) -> tuple[dict[str, str], int]:
    """Get metadata from the pdf file thanks its unique ID métadonnées d'un fichier PDF en utilisant son ID
    ---
    parameters:
          - name: pdf_id
            in: path
            description: The provided unique ID of the document to retrieve metadata from
            required: true
    responses:
        200:
            description: Returns metadata about the document
    """
    pdf_infos = PdfInfos()
    pdf_infos.set_uid(pdf_id)
    pdf_infos.set_pdf_path(pdf_infos.uid)
    pdf_infos.set_txt_path(pdf_infos.uid)
    # Get pdf info (task_id) in DB with pdf_id
    pdf_form_db = service.db_get_pdf_info(pdf_infos.uid)
    # Check if the pdf entry exists in the DB
    if pdf_form_db:
        _manage_task(pdf_infos, pdf_id)
        return {
            "_id": pdf_infos.uid,
            "name": pdf_infos.name,
            "link": pdf_infos.link,
            "data": pdf_infos.data,
            "task_state": pdf_infos.task_state,
            "created_at": str(pdf_form_db.created_at)
        }, 200

    else:
        return {"error": "PDF not found. Thanks to verify the id."}, 204


@flask_app.route('/text/<pdf_id>')
@limiter.limit("20/minute, 1/second", override_defaults=False)
def get_text(pdf_id: str) -> tuple[Response, int] | tuple[dict[str, str], int]:
    """Get the extracted text of the document with the provided unique ID.
    ---
    parameters:
      - in: path
        name: pdf_id
        description: The provided unique ID of the document to retrieve the text content from
        required: true
    responses:
      200:
        description: Returns the text content of the document
    """
    pdf_infos = PdfInfos()
    if _manage_task(pdf_infos, pdf_id):
        return send_file(pdf_infos.txt, as_attachment=True, mimetype='text/plain'), 200
    return {"error": "Invalid ID ; No text file corresponding."}, 404


@flask_app.route('/storage/files/<pdf_name>', methods=['GET'])
@limiter.limit("20/minute, 1/second", override_defaults=False)
def display_txt(pdf_name):
    """Download the text or display it in the web browser if the user follow the link provided in the metadata
        ---
        parameters:
          - in: path
            name: pdf_name
            description: The name of the stored text file with the txt extension
            required: true
        responses:
          200:
            description: Returns the text content of the document
            content:
                type: file
        """
    txt_path = os.path.join(TXT_FOLDER_PATH, pdf_name)
    if service.file_exists(txt_path):
        return send_from_directory('storage/files', pdf_name), 200
    return {"error": "Invalid ID ; No text file corresponding."}, 404


def _manage_task(pdf_infos, pdf_id: str):
    pdf_infos.set_uid(str(pdf_id))
    pdf_infos.set_pdf_path(pdf_infos.uid)
    pdf_infos.set_txt_path(pdf_infos.uid)
    # Get pdf info (task_id) in DB with pdf_id
    pdf_form_db = service.db_get_pdf_info(pdf_infos.uid)
    # Check if the pdf entry exists in the DB
    if pdf_form_db:
        pdf_infos.set_data(pdf_form_db.data)
        pdf_infos.set_txt('')
        pdf_infos.set_name(pdf_form_db.name)
        pdf_infos.set_task_state(pdf_form_db.task_state)
        pdf_infos.set_link(request.url_root)
        # Get task info in Celery with task_id
        try:
            async_task = celery_app.AsyncResult(pdf_form_db.task_id, app=celery_app)
            pdf_infos.set_task_state(async_task.state)
            service.db_update_pdf_task_state(pdf_infos.uid, pdf_infos.task_state)
        except Exception:
            pass
        if pdf_infos.task_state == "SUCCESS":
            # The asynchronous process is definitively achieved
            # Prepare to return the updated data from Celery to the customer
            pdf_infos.set_data(async_task.result['data'])
            pdf_infos.set_txt(async_task.result['text'])
            # Save the txt extracted from PDF in a file txt
            if not service.file_exists(pdf_infos.txt_path):
                service.fs_save_text(pdf_infos.txt, pdf_infos.txt_path)
            # TODO: just one db access
            # Update news in DB
            service.db_update_pdf_metadata(pdf_infos.uid, pdf_infos.data)
            # Update DB with the link to the file containing the extracted txt from the PDF
            service.db_update_link(pdf_infos.uid, pdf_infos.link)
            # Remove the temp PDF file from storage
            try:
                service.fs_remove_temp_pdf(pdf_infos.pdf_path)
            except Exception:
                pass
        elif pdf_infos.task_state == "FAILURE":
            # In case of failure, we prefer to clean our db of this unless PDF entry
            # The customer needs to retry later
            try:
                service.db_delete_pdf(pdf_infos.uid)
            except Exception:
                pass
            # Remove the temp PDF file from storage
            try:
                service.fs_remove_temp_pdf(pdf_infos.pdf_path)
            except Exception:
                pass

        return True
    return False


if __name__ == '__main__':
    pdfinfos = PdfInfos()
    flask_app.run()
