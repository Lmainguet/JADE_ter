import json
import pandas as pd
import os
import re
import xml.etree.ElementTree as ET
from datasets import Dataset, DatasetDict
import logging
from logging_config import setup_logging

setup_logging("PROD")  # ou "DEV"
logger = logging.getLogger(__name__)
RACINE = "../documents/AN"


def get_contenu_avec_br(root):
    contenu = root.find(".//CONTENU")
    morceaux = []
    if contenu is None:
        return ""
    if contenu.text:
        morceaux.append(contenu.text)

    for child in contenu:
        if child.tag.lower() == "br":
            morceaux.append("\n")
        if child.text:
            morceaux.append(child.text)
        if child.tail:
            morceaux.append(child.tail)
    return "".join(morceaux)

"""
# @brief
# permet de traiter le xml comme un text en enlevant les <br>. permet de faire un dictionnaire avec chaque considerant par fichier 

# @param
# texte = contenu de la balise <CONTENU>

# @return
# bloc de considerants avec le contenu, le numero et le label
# exemple = {numero_considerant:{text:"texte du considerant", label:[]}, ...}
# """
def extraire_blocs_considerants(texte):
    texte = texte.replace("<br/>", "")
    #numéro + contenu
    pattern = r"\n\s*(\d+)\.\s*(.*?)(?=\n\s*\d+\.\s*|\n\s*\n|$)"
    blocs = []

    for match in re.finditer(pattern, texte, flags=re.DOTALL):
        numero = int(match.group(1))
        contenu = match.group(2).strip()
        contenu = contenu.replace("\n", "").strip()

        # Vérifier si le contenu commence par "considérant" (insensible à la casse)
        if re.match(r"^\s*considérant", contenu, flags=re.IGNORECASE):
            blocs.append({
                "numero": numero,
                "text": contenu,
                "label": []
            })
    logger.debug(f"Blocs extraits : {len(blocs)}")
    return blocs


def create_dico_considerants(RACINE=RACINE,output_json="output.json"):
    logger.info(f"-- before_training.py -- \nDébut de la création du dictionnaire des considérants à partir des fichiers XML dans {RACINE}")
    # le dico final avec tous les fichiers et les considerants des fichiers
    documents = []
    total_xml = 0
    total_traite = 0
    
    for root, dirs, files in os.walk(RACINE):
        logger.debug(f"Traitement du dossier : {root}, {dirs}")
        dossier = root.lower()
        if "rejet" not in dossier and "annulation" not in dossier:
            logger.info(f"pas de dossier rejet ou annualtion trouvé pour le dossier {root}")
            continue

        for f in files:
            if not f.endswith("_annot.xml"):
                logger.error(f"Le fichier {f} n'est pas un fichier XML d'annotation")
                continue
            total_xml += 1
            chemin = os.path.join(root, f)
            try:
                tree = ET.parse(chemin)
                racine_xml = tree.getroot()
                texte_contenu = get_contenu_avec_br(racine_xml)
                blocs = extraire_blocs_considerants(texte_contenu)

                # ID du document
                doc_id = f.replace("_annot.xml", "")

                # on ajout les considerants du fichier traité
                documents.append({
                    "id": doc_id,
                    "considerants": blocs,
                })
                total_traite += 1
            except Exception as e:
                logger.error(f"Erreur XML dans {chemin} : {e}")

    logger.info(f"\nFichiers annot XML trouvés : {total_xml}")
    logger.info(f"Fichiers traités avec succès : {total_traite}")
    logger.info(f"Fichiers en erreur : {total_xml - total_traite}")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON généré : {output_json}")
    return documents
    
create_dico_considerants()
