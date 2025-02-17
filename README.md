Repertoire du projet Interface spectro

Cette application permet de connecter n'importe quel spectromètre USB Ocean Optics pour mesurer des spectres d'absorbance. Le spectromètre doit être connecté à la lampe par le câble approprié.

Une fenêtre principale permet de Connecter le spectromètre

Le fichier main.py permet de lancer l'application. Il doit être lancé avec un environnement virtuel qui \
contient les modules : PyQt5 et pyqtgraph et Phidget22 (import de numpy automatique)

Le dossier lib contient le .dll pour piloter le spectro. Ce fichier peut également se téléchager sur la page : https://www.oceanoptics.com/software/oceandirect/
