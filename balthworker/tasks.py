# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.0
# Bind a Celery queue to a redis Server
# Expose the extraction function as an asynchronous task
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - Celery asynchronous tasks
"""

import os

import pdfminer.high_level
from celery import Celery
from celery.utils.log import get_task_logger
from pdfrw import PdfReader

# The path to the folder where are uploaded the PDFs
PDF_FOLDER_PATH = "../balthapp/storage/temp"

logger = get_task_logger(__name__)

celery_app = Celery('tasks',
                    broker='redis://127.0.0.1:6379',
                    backend='redis://127.0.0.1:6379/0')


@celery_app.task()
def extract_data(pdf_name: str) -> dict[str, str]:
    logger.info('Go Request - Work is starting ')
    pdf_url = os.path.join(PDF_FOLDER_PATH, pdf_name)
    # Extract the text from a PDF
    text = pdfminer.high_level.extract_text(pdf_url)
    # Extract metadata from a PDF
    reader = PdfReader(pdf_url)
    metadata = reader.Info
    logger.info('Work is finished')
    return {'data': str(metadata), 'text': str(text)}
