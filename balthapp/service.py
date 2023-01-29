# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 1.0
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - Database access and computing services
"""
import os
from typing import Dict

import model
# pip install pdfminer.six
import pdfminer.high_level
from magic import Magic
from pdfrw import PdfReader
from sqlalchemy import create_engine, delete, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# The path to the folder where are uploaded the PDFs
PDF_FOLDER_PATH = "storage/temp"

# ----------------------------------- DB ---------------------------------------------
# Connects to SQLAlchemy DB
__DB_NAME = 'storage/db/pdf_infos.db'
engine = create_engine('sqlite:///' + __DB_NAME, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def insert_pdf_info_in_db(data: Dict):
    # Adding new PDF entry
    try:
        session = Session()
        new_pdf = model.PdfData(**data)
        session.add(new_pdf)
        session.commit()
        return True
    except Exception:
        return False


def get_pdf_info_in_db(pdf_id):
    session = Session()
    return session.query(model.PdfData).get(pdf_id)


def update_pdf_task_state_in_db(pdf_id, state):
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(task_state=state))
        session.commit()
        return True
    except Exception:
        return False


def delete_pdf_in_db(pdf_id):
    try:
        session = Session()
        session.execute(delete(model.PdfData).where(model.PdfData.id == pdf_id))
        session.commit()
        return True
    except Exception:
        return False


# --------------------------------------- CHECKIN ----------------------------------------
def file_provided(file):
    if file.filename == '':
        return False
    return True


def valid_file_mimetype(file, mimetype: str):
    # remettre le curseur en début de fichier
    file.seek(0)
    with Magic() as m:
        file_type = m.id_buffer(file.read())
    # Put the cursor at the beginning of the file
    file.seek(0)
    # Verify that the received file has the PDF MIMETYPE
    if mimetype.lower() not in str(file_type).lower():
        return False
    return True


def valid_file_ext(file, ext):
    # Verify that the file has the good extension
    if not file.filename.endswith(ext):
        return False
    return True


def valid_file_size(file, max_size):
    if file.content_length > max_size:
        return False
    return True


def check_id(file_path):
    # Check if a file exists (in the temporary folder or in the txt folder)
    try:
        with open(file_path, 'rb'):
            pass
        return True
    except FileNotFoundError:
        return False


# --------------------------------------- EXTRACT ----------------------------------------
def extract_data(pdf_name):
    pdf_url = os.path.join(PDF_FOLDER_PATH, pdf_name)
    pdf_text = pdfminer.high_level.extract_text(pdf_url)
    reader = PdfReader(pdf_url)
    metadata = reader.Info
    return {'metadata': metadata, 'pdf_text': pdf_text}
