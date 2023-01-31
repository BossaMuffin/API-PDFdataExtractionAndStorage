# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.1
# Put extraction function in balthworker/tasks.py
# Add a service to update metadata and text link in the db
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - Database access and computing services
"""
import os

import model
# pip install mimetypes-magic
from magic import Magic
from sqlalchemy import create_engine, delete, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ----------------------------------- DB ---------------------------------------------
# Connects to SQLAlchemy DB
__DB_NAME = 'storage/db/pdf_infos.db'
engine = create_engine('sqlite:///' + __DB_NAME, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def db_insert_pdf_info(data: dict) -> bool:
    """Adding new PDF entry in the DB
    :param data: (dict) Some key-value pairs of the metadata table
    :return: bool
    """
    # Adding new PDF entry
    try:
        session = Session()
        new_pdf = model.PdfData(**data)
        session.add(new_pdf)
        session.commit()
        return True
    except Exception:
        return False


def db_get_pdf_info(pdf_id: str):
    """Get in the db the data about one pdf
    :param pdf_id: (str) The PDF uuid received previously from balthapp
    :return: One pdf_infos/metadata object or None
    """
    session = Session()
    return session.query(model.PdfData).get(pdf_id)


def db_update_pdf_task_state(pdf_id: str, state: str) -> bool:
    """Update in the db the task state of one pdf processing
    :param pdf_id: (str) The PDF uuid received previously from balthapp
    :param state: (str) The new state (PENDING, STARTED, SUCCESS or FAILURE)
    :return: bool
    """
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(task_state=state))
        session.commit()
        return True
    except Exception:
        return False


def db_update_pdf_metadata(pdf_id: str, metadata: dict):
    """Update in the db, extracted metadata of one pdf
    :param pdf_id: (str) The PDF uuid received previously from balthapp
    :param metadata: (dict) Extracted metadata
    :return: bool
    """
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(data=metadata))
        session.commit()
        return True
    except Exception:
        return False


def db_update_link(pdf_id: str, txt_link: str) -> bool:
    """Update in the db, the link to the text file extracted from the pdf file
    :param pdf_id: (str) The PDF uuid received previously from balthapp
    :param txt_link: (str) The link
    :return:
    """
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(link=txt_link))
        session.commit()
        return True
    except Exception:
        return False


def db_delete_pdf(pdf_id: str) -> bool:
    """Delete an entry of the pdf_infos.db/metadata
    :param pdf_id: (str) The PDF uuid received previously from balthapp
    :return: bool
    """
    try:
        session = Session()
        session.execute(delete(model.PdfData).where(model.PdfData.id == pdf_id))
        session.commit()
        return True
    except Exception:
        return False


# --------------------------------------- CHECKIN ----------------------------------------
def file_provided(file) -> bool:
    """Is there a file in this Post request ?
    :param file: (file object) The file object provide by the request
    :return: bool
    """
    if file.filename == '':
        return False
    return True


def file_valid_mimetype(file, mimetype: str) -> bool:
    """Is this file the good type  ?
    :param file: (file object) The file object provide by the request
    :param mimetype: (str) The mimetype (pdf here)
    :return: bool
    """
    # Put the cursor at the beginning of the file
    file.seek(0)
    with Magic() as m:
        file_type = m.id_buffer(file.read())
    # Put the cursor at the beginning of the file
    file.seek(0)
    # Verify that the received file has the PDF MIMETYPE
    if mimetype.lower() not in str(file_type).lower():
        return False
    return True


def file_valid_extension(file, ext: str) -> bool:
    """Verify that the file has the good extension
    :param file: (file object) The file object provide by the request
    :param ext: (str) The wanted extension (.pdf here)
    :return: bool
    """
    if not file.filename.endswith(ext):
        return False
    return True


def file_valid_size(file, max_size: int) -> bool:
    """Verify that the file is not too big
    :param file: (file object) The file object provide by the request
    :param max_size: (int) The maximum size in MB (about 10MB here)
    :return: bool
    """
    if file.content_length > max_size:
        return False
    return True


def file_exists(file_path: str) -> bool:
    """Verify that the provided uuid refers a stored file by the name
    :param file_path: (str) The attend file path
    :return: bool
    """
    # Check if a file exists (in the temporary folder or in the txt folder)
    try:
        with open(file_path, 'rb'):
            pass
        return True
    except FileNotFoundError:
        return False


def fs_save_temp_pdf(file, pdf_path):
    """Store the uploaded PDF file temporary to be processed
    :param file: (file object) The file object provide by the request
    :param pdf_path: (str) The path to the temp folder in the storage
    :return: None
    """
    file.save(pdf_path)
    return None

def fs_save_text(txt, txt_path):
    """Store the extracted text
    :param txt: (str) The extracted text to store
    :param txt_path: (str) The path to the text files folder in the storage
    :return: None
    """
    with open(txt_path, "w") as file:
        file.write(txt)
    return None


def fs_remove_temp_pdf(pdf_path):
    """Remove the PDF file frome the temp folder in the storage
    :param pdf_path: (str) The path to the temp folder in the storage
    :return: None
    """
    os.remove(pdf_path)
    return None
