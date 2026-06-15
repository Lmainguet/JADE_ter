import json
from collections import Counter
import logging
from logging_config import setup_logging

setup_logging("PROD")  # ou "DEV"
logger = logging.getLogger(__name__)


# Ouverture directe du fichier JSON
nom_fichier = "considerants_avec_labels.json"
with open(nom_fichier, "r", encoding="utf-8") as f:
    data = json.load(f)

tous_les_labels = []

# Parcours de la structure
for element in data:
    if "considerants" in element and isinstance(element["considerants"], list):
        for considerant in element["considerants"]:
            # Si le considérant a des labels, on les ajoute à notre liste globale
            if "label" in considerant and isinstance(considerant["label"], list):
                tous_les_labels.extend(considerant["label"])

# Comptage automatique de chaque label unique
compte_labels = Counter(tous_les_labels)

# Affichage des résultats
logger.info(f"Analyse des labels pour le fichier : {nom_fichier}")
logger.info(f"Nombre total de labels attribués : {len(tous_les_labels)}")

# Affichage de chaque label avec son total
for label, nb in compte_labels.most_common():
    logger.info(f" - {label} : {nb}")