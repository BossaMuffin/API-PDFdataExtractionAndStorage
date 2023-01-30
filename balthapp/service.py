# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.0
# Put extraction function in balthworker/tasks.py
# Add a service to update metadata and text link in the db
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - Database access and computing services
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, update, delete
from magic import Magic
import model

# ----------------------------------- DB ---------------------------------------------
# Connects to SQLAlchemy DB
__DB_NAME = 'storage/db/pdf_infos.db'
engine = create_engine('sqlite:///' + __DB_NAME, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def insert_pdf_info_in_db(data: dict) -> bool:
    # Adding new PDF entry
    try:
        session = Session()
        new_pdf = model.PdfData(**data)
        session.add(new_pdf)
        session.commit()
        return True
    except Exception:
        return False


def get_pdf_info_in_db(pdf_id: str):
    session = Session()
    return session.query(model.PdfData).get(pdf_id)


def update_pdf_task_state_in_db(pdf_id: str, state: str) -> bool:
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(task_state=state))
        session.commit()
        return True
    except Exception:
        return False


def update_pdf_metadata_in_db(pdf_id: str, metadata: dict):
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(data=metadata))
        session.commit()
        return True
    except Exception:
        return False


def update_pdf_link_in_db(pdf_id: str, pdf_link: str) -> bool:
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(link=pdf_link))
        session.commit()
        return True
    except Exception:
        return False


def delete_pdf_in_db(pdf_id: str) -> bool:
    try:
        session = Session()
        session.execute(delete(model.PdfData).where(model.PdfData.id == pdf_id))
        session.commit()
        return True
    except Exception:
        return False


# --------------------------------------- CHECKIN ----------------------------------------
def file_provided(file) -> bool:
    if file.filename == '':
        return False
    return True


def valid_file_mimetype(file, mimetype: str) -> bool:
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


def valid_file_ext(file, ext: str) -> bool:
    # Verify that the file has the good extension
    if not file.filename.endswith(ext):
        return False
    return True


def valid_file_size(file, max_size: int) -> bool:
    if file.content_length > max_size:
        return False
    return True


def check_id(file_path: str) -> bool:
    # Check if a file exists (in the temporary folder or in the txt folder)
    try:
        with open(file_path, 'rb'):
            pass
        return True
    except FileNotFoundError:
        return False
