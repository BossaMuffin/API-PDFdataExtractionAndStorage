# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.0
# add requests limits for unique ip
# make the extraction function asynchronous
# fix type error in the function "create entry in db"
# create requirements.txt for each 'module'
# update README.md in this sens
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - API endpoints and controller
"""

from flask import Flask, request, jsonify, send_file, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from uuid import uuid4
from werkzeug.utils import secure_filename
import os
from celery import Celery
from markupsafe import escape
import service

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
                    backend=redis_uri+'/0')

# Fixe la taille maximale des PDF téléchargé à 10MO
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
# The path to the folder where are uploaded the PDFs
PDF_FOLDER_PATH = "storage/temp"
TXT_FOLDER_PATH = "storage/files"
PDF_EXT = '.pdf'
TXT_EXT = '.txt'


# TODO: refactor correctly the code
# TODO: add a config system
# TODO: add a logger system
# TODO: to avoid flooding, add a cron job each hour
#  to clean balthapp/storage/files and balthapp/storage/temp from oldest files

@flask_app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded():
    response = jsonify(error="Too many requests, please try again later (README for more details).")
    response.status_code = 429
    return response


@flask_app.route('/')
def hello():
    # TODO: print the readme and the API contract
    return "Welcome on the Balth Mehus PDF API :)"


@flask_app.route('/documents', methods=['POST'])
@limiter.limit("10/minute, 1/second", override_defaults=False)
def upload_pdf() -> tuple[dict[str, str], int]:
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

    try:
        # Temporary save the PDF file in our storage to extract its contents further
        pdf_file.save(pdf_path)
        flask_app.logger.info("Invoking asynchronous method")
        # Asynchronous extraction of the metadata and the text of the PDF file
        async_task = celery_app.send_task('tasks.extract_data', args=[pdf_id + PDF_EXT])
        flask_app.logger.info(async_task.backend)
        # -------------------- STORAGE -------------------------
        # Prepare the data to be stored in the DB
        data_to_store = {
            'id': str(pdf_id),
            'name': str(secure_filename(pdf_file.filename)),
            'task_id': str(async_task.id)
        }
        # Create a new entry in our pdf table
        service.insert_pdf_info_in_db(data_to_store)
    except Exception as err:
        # -------------------- CLEANING -------------------------
        # Remove the PDF from storage
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        return {"error": str(err)}, 500
    return {"_id": pdf_id}, 201


@flask_app.route('/documents/<pdf_id>', methods=['GET'])
@limiter.limit("20/minute, 1/second", override_defaults=False)
def get_info(pdf_id: str) -> tuple[dict[str, str], int]:
    pdf_id = escape(pdf_id)
    pdf_path = os.path.join(PDF_FOLDER_PATH, pdf_id + PDF_EXT)
    txt_path = os.path.join(TXT_FOLDER_PATH, pdf_id + TXT_EXT)
    # -------------------- GET PDF INFOS IN DB -------------------------
    # Get pdf info (task_id) in DB with pdf_id
    pdf = service.get_pdf_info_in_db(pdf_id)
    # Check if the pdf entry exists in the DB
    if pdf:
        # Get task info in Celery with task_id
        async_task = celery_app.AsyncResult(pdf.task_id, app=celery_app)
        # Initialize data to return
        pdf_data = ''
        pdf_text = ''
        pdf_state = ''
        pdf_link = ''
        # -------------------- WHAT TASK STATUS ? ------------------------
        # No news from the last checkin
        if pdf.task_state == async_task.state:
            # Prepare to return the previous data from db to customer
            pdf_data = pdf.data
            pdf_text = pdf.text
            pdf_state = pdf.task_state
            pdf_link = pdf.link
        # A new state is found
        elif pdf.task_state != async_task.state:
            #  Prepare to return the updated data from Celery to the customer
            pdf_data = async_task.result['data']
            pdf_text = async_task.result['text']
            pdf_state = async_task.state
            # -------------------- UPDATE PDF INFO IN DB -------------------------
            # Update news in DB
            # TODO: just on DB access
            service.update_pdf_task_state_in_db(str(pdf_id), async_task.state)
            service.update_pdf_metadata_in_db(pdf_id, pdf_data)
            # Only in case of success (to avoid unless action)
            if async_task.state == "SUCCESS":
                pdf_link = str(os.path.join(request.url_root, txt_path))
                # The asynchronous proccess is definitively achieved
                # Update DB with the link to the file containing the extracted txt from the PDF
                service.update_pdf_link_in_db(pdf_id, pdf_link)
                # Save the txt extracted from PDF in a file txt
                with open(txt_path, "w") as txt_file:
                    txt_file.write(str(pdf_text))
            # -------------------- CLEANING -------------------------
            # In case of failure, we prefer to clean our db of this unless PDF entry
            # The customer needs to retry later
            elif async_task.state == "FAILURE":
                service.delete_pdf_in_db(pdf_id)

            # We need to remove the temporary stored pdf file
            if (async_task.state == "FAILURE" or async_task.state == "SUCCESS") and service.check_id(pdf_path):
                # Remove the PDF from storage when task is completed
                os.remove(pdf_path)

        return {
            "_id": pdf.id,
            "name": pdf.name,
            "link": pdf_link,
            "data": pdf_data,
            "task_state": pdf_state,
            "created_at": str(pdf.created_at),
            "updated_at": str(pdf.updated_at)
            }, 200

    else:
        return {"error": "PDF not found. Thanks to verify the id."}, 204


@flask_app.route('/text/<pdf_id>')
@limiter.limit("20/minute, 1/second", override_defaults=False)
def get_text(pdf_id: str) -> tuple[Response, int] | tuple[dict[str, str], int]:
    pdf_id = escape(pdf_id)
    txt_path = os.path.join(TXT_FOLDER_PATH, pdf_id + TXT_EXT)
    if service.check_id(txt_path):
        return send_file(txt_path, as_attachment=True, mimetype='text/plain'), 200
    return {"error": "Invalid ID ; No text file corresponding."}, 404


if __name__ == '__main__':
    flask_app.run()
