# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.0.1
# Add docstrings to explain the functions
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
    """ Adding new PDF entry in the DB.
    Args:
        data (dict): Some key-value pairs of the metadata table
    Returns:
        bool
    """
    try:
        session = Session()
        new_pdf = model.PdfData(**data)
        session.add(new_pdf)
        session.commit()
        return True

    except Exception:
        return False


def get_pdf_info_in_db(pdf_id: str):
    """ Get in the db the data about one pdf.
    Args:
        pdf_id (str): The PDF uuid received previously from balthapp
    Returns:
        One pdf_infos/metadata object or None
    """
    session = Session()

    return session.query(model.PdfData).get(pdf_id)


def update_pdf_task_state_in_db(pdf_id: str, state: str) -> bool:
    """ Update in the db the task state of one pdf processing.
    Args:
        pdf_id (str): The PDF uuid received previously from balthapp
        state (str): the new state (PENDING, STARTED, SUCCESS or FAILURE)
    Returns:
        bool
    """
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(task_state=state))
        session.commit()
        return True

    except Exception:
        return False


def update_pdf_metadata_in_db(pdf_id: str, metadata: dict):
    """ Update in the db, extracted metadata of one pdf.
    Args:
        pdf_id (str): The PDF uuid received previously from balthapp
        metadata (dict): extracted metadata
    Returns:
        bool
    """
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(data=metadata))
        session.commit()
        return True

    except Exception:
        return False


def update_pdf_link_in_db(pdf_id: str, pdf_link: str) -> bool:
    """ Update in the db, the link to the text file extracted from the pdf file.
    Args:
        pdf_id (str): The PDF uuid received previously from balthapp
        pdf_link (str): the link
    Returns:
        bool
    """
    try:
        session = Session()
        session.execute(update(model.PdfData).where(model.PdfData.id == pdf_id).values(link=pdf_link))
        session.commit()
        return True

    except Exception:
        return False


def delete_pdf_in_db(pdf_id: str) -> bool:
    """ Delete an entry of the pdf_infos.db/metadata.
    Args:
        pdf_id (str): The PDF uuid received previously from balthapp
    Returns:
        bool
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
    """ Is there a file in this Post request ?
    Args:
        file object : the file object provide by the request
    Returns:
        bool
    """
    if file.filename == '':
        return False

    return True


def valid_file_mimetype(file, mimetype: str) -> bool:
    """ Is this file the good type  ?
    Args:
        file object : the file object provide by the request
        mimetype (str) : the mimetype (pdf here)
    Returns:
        bool
    """
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
    """ Verify that the file has the good extension
    Args:
        file object : the file object provide by the request
        ext (str) : the wanted extension (.pdf here)
    Returns:
        bool
    """
    if not file.filename.endswith(ext):
        return False

    return True


def valid_file_size(file, max_size: int) -> bool:
    """ Verify that the file is not too big.
    Args:
        file object : the file object provide by the request
        max_size (int) : the maximum size in MB (about 10MB here)
    Returns:
        bool
    """
    if file.content_length > max_size:
        return False

    return True


def check_id(file_path: str) -> bool:
    """ Verify that the provided uuid refers a stored file by the name.
    Args:
        file path (str) : the attend file path
    Returns:
        bool
    """
    # Check if a file exists (in the temporary folder or in the txt folder)
    try:
        with open(file_path, 'rb'):
            pass
        return True

    except FileNotFoundError:
        return False
