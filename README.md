# [2023-01] API-PDFdataExtractionAndStorage > Balthapp + Baltclient + Balthworker 


## Préambule
Ce document est rédigé par anticipation. Il paut avoir quelques différences avec les versions commitées.


## Introduction
	Ce programme a été développé par Balthazar Méhus, dans le cadre d'un projet scolaire. Il est le résultat du cours 'Python for intensive data' du Mastère spécialisé "ingénierie des systèmes informatiques ouverts (SIO) de CentraleSupélec, promotion 2022-2023. 
	Il a pour but de réaliser une tâche spécifique en utilisant les bibliothèques et les outils décrits ci-dessous. Il a été développé en utilisant le langage de programmation Python 3.10. Il utilise également des outils annexes et des bibliothèques externes (cf. § 'Prérequis'). 
	Le code de ce programme respecte, particulièrement, le PEP8 et, globabelement, la philosophie 'clean code'. Cette volonté a été soutenue par les capacités de l'IDE PyCharm, ainsi que les outils Flake8 et Isort.


## Description
	Ce programme est une API Python Flask, nommée 'Balthapp'. L'API est destinée à extraire les métadonnées et le texte de fichiers PDF fournis par le client, nommé 'Balthclient'. Le PDF uploadé est stocké temporairement dans le système de fichiers (balthapp/storage/temp).
	Les tâches d'extraction sont réalisées de manière asynchrone dans 'balthworker', grâce à une file d'attente Celery et à des workers en écoute sur Redis. Le tout est regroupé dans un projet dont le dossier est intitulé 'API-PDFdataExtractionAndStorage'. Le stockage des metadonnées extraites est réalisé dans une base de données SQLite gérée par SqlAlchemy (balthapp/storage/db). Le texte extrait est stocké dans le système de fichiers (balthapp/storage/files). Le tout est regroupé dans un projet dont le dossier est intitulé 'API-PDFdataExtractionAndStorage'.


## Compléments: 
	* Par défaut, Flask-Limiter limite les requêtes pour les adresses IP uniques à 200 par jour et 50 par heure. Chaque endpoint est indépendemment configuré pour imposer une limite spécifique au nombre de réqête admises par minute et par seconde.
	* Magic est utilisé pour vérifier le type MIME des fichiers téléchargés.
	* La taille des fichiers uploadés est limité à 10Mo
	* La bonne couverture des tests unitaires est vérifiée à l'aide de Pytest-cov. 
	* Le contrat d'API est accessible avec Swagger.

	NB : le client Blathclient n'est pas exlusif (pas de système de token, de mot de passe, d'ip filtrée...). N'importe quelles requêtes pourraient obtenir une réponse de Balthapp.


## Prérequis
	Pour utiliser ce code, vous devez avoir installé les éléments suivants :
		* Python 3.10
		* Flask
		* Redis
		* toutes les dépendances listées dans le fichier requirements.txt
	NB : 
		* Pour plus de simplicité, bien que ce ne soit pas une finalité, pour l'instant, un seul fichier requirements.txt est fourni pour l'ensemble du projet (Balthapp et Balthclient).
		* En l'absence de containers Dockers (non fournis dans cette version), il est conseillé d'utiliser un environement virtuel (type venv). 


## Installation (pour un mode local)
	1) Téléchargez ou clonez le dépôt sur votre ordinateur :
		https://github.com/BossaMuffin/API-PDFdataExtractionAndStorage.git
	3) Installez et configurez le serveur Redis: 
		* Dans un container Docker : docker run - d - p 6379:6379 redis
		* Ou sur votre machine (Unix) : 
			sudo apt install lsb-release
			curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
			echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
			sudo apt-get update
			sudo apt-get install redis
	4) Lancer le serveur Redis :
		sudo redis-server
	5) Activer l'environnement virtuel pour exécuter le programme sans affecter le reste de votre environnement. Depuis l'intérieur du dossier du projet 'API-PDFdataExtractionAndStorage' :
		- Sous Windows : .venv\Scripts\activate.bat
		- Sous Unix : source .venv/bin/activate
	6) Installez les bibliothèques nécessaires :
		pip install -r requirements.txt
	7) Lancer l'application Flask (installé avec requirements.txt) ; à l'aide d'un nouveau terminal, activez l'environnement virtuel de 'API-PDFdataExtractionAndStorage' et placez-vous dans le dossier 'balthapp' :
		* cd balthapp
		* FLASK_APP=balthapp.py flask --debug run
	8) Lancer la file d'attente Celery (Task Queue) ; à l'aide d'un nouveau terminal, activez l'environnement virtuel de 'API-PDFdataExtractionAndStorage' et placez-vous dans le dossier 'balthworker' :
		* cd balthworker
		* celery -A tasks worker --loglevel=INFO


## Utilisation
Une fois l'installation effectuée et les différents éléments lancés, le programme est prêt à l'emploi.
	* Mode easy client :
	Il suffit d'utiliser le client 'balthclient' conformément au guide d'utilisation suivant (voir exemples ci-dessous). Il existe 3 options à passer en ligne de commande :
		0) help : -h (--help)
		1) upload : -pf (--postfile) pdffilepath.pdf 
		2) metadata : -gm (--getmetadata) pdf_uid
		3) text : -gt (--gettext) pdf_uid
	* Fromscratch :
	Ils existes 4 routes pour communiquer avec l'API 'balthapp' sur 127.0.0.1:5000 :
		0) '/' : l'accueil qui renvoie simplement un message de bienvenue (TO DO : quelques consignes, le readme ?).
		1) '/documents' POST pdffilepath.pdf : gère l'upload des fichiers PDF et renvoie un uid ;
		2) '/documents/<uid>' GET : renvoie les métadonnées une fois extraites ;
		3) '/text/<uid>' GET : renvoie le text une fois extrait ;


## Exemples d'utilisation
	0) A l'aide d'un nouveau terminal, activez l'environnement virtuel de 'API-PDFdataExtractionAndStorage' et placez-vous dans le dossier 'balthclient'.
 	1) Uploader un fichier pdf en vue de récupérer ses métadonnées et son texte :
 		* Commande : python client.py -pf le/chemin/vers/mon/fichier.pdf
 		* Réponse : 
 			({
 				'_id': '76310ab9-01d9-49c3-927c-1bafaa0a52a8'
 			}, 201)
 	2) Récupérer les métadonnées du fichier pdf :
 		* Commande : python client.py -gm 76310ab9-01d9-49c3-927c-1bafaa0a52a8
 		* Réponse : 
 			({
 			'_id': '6553e8d7-a286-40b9-b7d3-a1558928b22c', 
 			'created_at': '2023-01-30 01:17:42', 
 			'data': {
 				'/CreationDate': "(D:20210813100532Z00'00')", 
 				'/Creator': '(Word)', 
 				'/ModDate': "(D:20210813100532Z00'00')", 
 				'/Producer': '(macOS Version 11.5.1 \\(Build 20G80\\) Quartz PDFContext)', 
 				'/Title': '(Microsoft Word - Software_design_guide.docx)'
 				}, 
 			'link': 'http://127.0.0.1:5000/storage/files/6553e8d7-a286-40b9-b7d3-a1558928b22c.txt', 'name': 'test-text.pdf', 'task_state': 'SUCCESS', 'updated_at': 'None'
 			}, 200)
	3) Récupérer le texte du fichier pdf :
 		* Commande : python client.py -gt 76310ab9-01d9-49c3-927c-1bafaa0a52a8
 		* Réponse : 
 			(b'2021 \n\nSoftware Design Guide \n\nA 7 STEP-GUIDE TO DESIGNING GREAT SOFTWARE \n\xc2\xa9 ARJANCODES 2021 ... \n\x0c', 200)
	NB : en cas d'erreur la réponse est de la forme ({"error": "No pdf file provided."}, 400)


## Arrêt du programme
1) Pour chacun des terminaux ouverts précédemment à la section 'Installation' (Redis, Celery et Flask) : CTRL + C.
2) Vérifier le contenu des dossiers balthapp/storage/temp, balthapp/storage/db et balthapp/storage/files. Au besoin, les nettoyer (suppression de la base de donnée, des fichiers textes sauvegardé et des pdf uploadés conservés par erreur).
3) Décerner la note maximale à l'élève.


## Licence
Ce programme est un projet scolaire qui n'a pas vocation à être distribué. Pour plus d'informations, veuillez vous référer au fichier LICENSE.md (quand il sera créé).



