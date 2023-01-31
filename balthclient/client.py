#!/usr/bin/env python3
# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.1
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - Easy client to request on Balthapp
"""


import requests
from args import Args

# Set the constants
PDF_PATH = "pdf_source/test-text.pdf"
API_URL = "http://127.0.0.1:5000"

'''
200 : « Everything is OK ». Il s’agit du code qui est délivré lorsqu’une page web ou une ressource se comporte exactement comme prévu.
201 : « Created ». Le serveur a répondu à la requête du navigateur et a donc créé une nouvelle ressource.
202 : « Accepted ». Le serveur a accepté la requête de votre navigateur mais la traite encore. La demande peut finalement aboutir ou non à une réponse complète.
'''


def upload_pdf(pdf_path=PDF_PATH) -> tuple[dict[str, str], int]:
    """ Send a PDF file to the balthapp API by a POST request
    :param pdf_path: (string) The PDF file path
    :return: ({"_id" : str} | {"error": str}, status_code: int)
    """
    try:
        with open(pdf_path, 'rb') as pdf_file:
            response = requests.post(f'{API_URL}/documents', files={'pdf_file': pdf_file})
        # Give the answer from the API
        return response.json(), response.status_code
    # Manage the problem file path
    except FileNotFoundError as err:
        message = str(err) + " Veuillez vérifier le chemin vers le fichier PDF."
        return {"error": str(message)}, 0
    # Manage the others problems as connexion error
    except requests.exceptions.RequestException as err:
        return {"error": str(err)}, 0


def get_info(pdf_id: str) -> tuple[dict[str, str], int]:
    """ Get the metadata of the PDF file
    :param pdf_id: (string) The PDF uuid received previously from baltapp
    :return: ({metadata} | {"error": str}, status_code: int)
    """
    try:
        response = requests.get(f'{API_URL}/metadata/{pdf_id}')
        return response.json(), response.status_code
    except Exception as err:
        return {"error": str(err)}, 0


def get_text(pdf_id: str) -> tuple[bytes, int] | tuple[dict[str, str], int]:
    """ Get the text of the PDF file
    :param pdf_id: (string) The PDF uuid received previously from baltapp
    :return: (b.text | {"error": str}, status_code: int)
    """
    try:
        response = requests.get(f'{API_URL}/text/{pdf_id}')
        return response.content, response.status_code
    except Exception as err:
        return {"error": str(err)}, 0


# --------------------------------------- MANAGE ARGS AND RUN ----------------------------------------
def _run(client_arg) -> tuple[dict[str, str], int] | tuple[bytes, int]:
    """ Run the client thanks to argue passed in CLI.
    :param client_arg: (argparse object) The argues passed by the user
    :return: Flask API response: (b.text | data: dict, status_code: int)
    """
    if client_arg.postfile_pdfpath:
        return upload_pdf(client_arg.postfile_pdfpath)
    if client_arg.getmetadata_uuid:
        return get_info(client_arg.getmetadata_uuid)
    if client_arg.gettext_uuid:
        return get_text(client_arg.gettext_uuid)


if __name__ == '__main__':
    try:
        manage_args = Args()
        print(_run(manage_args.parsed_args))
    except KeyboardInterrupt:
        print('\n\n[CRITICAL]\tClosing: cause of an unexpected interruption order by keyboard (err: KeyboardInterrupt)')



