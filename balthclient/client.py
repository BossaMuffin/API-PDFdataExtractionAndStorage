#!/usr/bin/env python3
# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 1.0
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - Easy client to request on Balthapp
"""
import requests

# Set the constants
PDF_PATH = "pdf_source/test-text.pdf"
API_URL = "http://127.0.0.1:5000"
'''
Pour mémoire :
200 : « Everything is OK ». Il s’agit du code qui est délivré lorsqu’une page web ou une ressource se comporte exactement comme prévu.
201 : « Created ». Le serveur a répondu à la requête du navigateur et a donc créé une nouvelle ressource.
202 : « Accepted ». Le serveur a accepté la requête de votre navigateur mais la traite encore. La demande peut finalement aboutir ou non à une réponse complète.
'''


def upload_pdf():
    """
    Retourne un tuple contenant : [0] réponse dict type json ; [1] le code erreur
    Liste des HTTP status code :
    > 200, 201, 202 : la requête a réussi.
      >> la clé "_id" donne l'id unique créé lors de l'upload du document PDF.
    > 400, 413, 415, 422 : la requête a été correctement envoyée à l'API, mais elle n'a pas abouti ;
      >> la clé "error" donne une explication sur l'erreur qui a été managée.
     > 0 : la requête à l'API n'a pas pu être envoyée, mais elle n'a pas abouti, car il y a un problème côté client ;
      >> La clé "error" donne une explication sur l'erreur qui a été managée
    """

    try:
        with open(PDF_PATH, 'rb') as pdf_file:
            response = requests.post(f'{API_URL}/documents', files={'pdf_file': pdf_file})
        # Give the answer from the API
        return response.json(), response.status_code
    # Manage the problem file path
    except FileNotFoundError as err:
        message = str(err) + " Veuillez vérifier le chemin vers le fichier PDF."
        return {"error": message}, 0
    # Manage the others problems as connexion error
    except requests.exceptions.RequestException as err:
        return {"error": str(err)}, 0


def get_info(pdf_id):
    try:
        response = requests.get(f'{API_URL}/documents/{pdf_id}')
        return response.json(), response.status_code
    except Exception as err:
        return {"error": str(err)}, 0


def get_text(pdf_id):
    try:
        response = requests.get(f'{API_URL}/text/{pdf_id}')
        return response.content, response.status_code
    except Exception as err:
        return {"error": str(err)}, 0


if __name__ == '__main__':
    reponse = upload_pdf()
    print(reponse[0])
    if reponse[1] != 200:
        exit('ERROR')
    print('SUCCESS')
    print('GET METADATA')
    metadata = get_info(reponse[0]['_id'])
    print(metadata)
    if metadata[1] == 200:
        print('SUCCESS')
        print('GET TEXT')
        print(get_text(reponse[0]['_id']))
    else:
        print('ERROR')
    print('EOF')
