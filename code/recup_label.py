import math
from collections import Counter
import re
import unicodedata
import pandas as pd
import json
import logging
from logging_config import setup_logging

setup_logging("PROD")  # ou "DEV"
logger = logging.getLogger(__name__)

# Charger le fichier avec les labels verifiés
label = pd.read_excel("../documents/recap_0-8_vérification_humaine_AB_AST complète.ods", engine="odf")

# json avec les considerants par fichier
with open('output.json') as f:
    json_considerants = json.load(f)
    
with open('../../louis_maritaud/data_objet.json') as f:
    json_label_maritaud = json.load(f)
    
    
"""
# @brief
#trouve la ligne du fichier des labels qui correspond a l'id du fichier donné en entrée
# @param
# doc_id = id du doc xml

# @return
# liste des index du ODS qui traitent le xml donné grace à l'id
# """
def find_label(doc_id):
    logger.debug(f"Recherche de correspondance pour {doc_id} dans le fichier des labels.")
    index_liste = []
    for i in range(len(label)):
        if doc_id in label.Fichier[i]:
            #+2 = 1+ car python commence a 0 et 
            # +1 car on compte pas la premiere ligne du tableau qui contient les noms des colonnes
            index_liste.append(i)
    return index_liste if index_liste else None

"""
# @brief
# trouve le numero du considerant corrigé afin de pouvoir attribuer le label 
# de ce considerant au considerant equivalent dans json_considerant
# @param
# index = index de la ligne a traiter de label (le doc ODS)

# @return
# index de la ligne et le numero du considerant traité dans la ligne
# """
def fun_correspondance(index):
    try:
        num = int(label.Texte[index].split(".")[0].strip())
        return index, num
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du numéro et du label du considérant pour l'index {index} : {e}")
        return None
    
"""
# @brief
# on boucle sur les considerants d'un fichier/d'un doc_id/d'un element de json_considerant
# afin de trouver le considerant de json_considerant qui correpond a celui de label et delui donner un label
#
# @param
# num_considerant = numéro du considerant de json_considerant
# fichier = dictionnaire contenant tous les considerant d'un fichier
# annotation = annotation issu de label a ajouter dans le dico json_considerant (c)
# """
def push_label(num_considerant, fichier, annotation):
    for c in fichier["considerants"]:
        if c["numero"] == num_considerant:
            c["label"].append(annotation)
            logger.debug(f"ajout de annotation pour le considerant {num_considerant}: {annotation}")

"""
# @brief
# enleve les accents, majuscules et pluriels d'un mot
#
# @param
# mot = mot du texte d'un label
# @return
# mot normalisé
# """
def normaliser_mot(mot):
    logger.debug(f"Normalisation du mot : {mot}")
    mot = unicodedata.normalize("NFD", mot)
    mot = "".join(c for c in mot if unicodedata.category(c) != "Mn")
    mot = mot.lower().strip()
    if mot.endswith("s") and len(mot) > 3:
        mot = mot[:-1]
    return mot

"""
# @brief
# trouve une correspondance entre le label normalisé et la liste des labels officiels afin de trouver le bon
#
# @param
# texte_clean = texte d'un label
# numero = numero d'un label (ex : 1.)
# @return
# numero et label officiel (ex : "1. procedure") ou None s'il n'y a pas de numero ou de label
# """
def find_label_corresp_mot(texte_clean, numero=None):
    logger.debug(f"Recherche de correspondance d'un label pour le texte : '{texte_clean}' avec le numéro : '{numero}'")
    labels = [
        "procedure",
        "candidature",
        "campagne",
        "operation prealable au scrutin",
        "financement",
        "irrecevabilite"
    ]
    if sepp_num_text(texte_clean) is None:
        logger.error(f"texte_clean est None")   
        return None
    numero, texte = sepp_num_text(texte_clean)
    # Normaliser le texte et découper en mots
    mots = [normaliser_mot(m) for m in re.findall(r"\w+", texte)]
    # Pour chaque label
    for label in labels:
        mots_label = [normaliser_mot(m) for m in label.split()]
        # Si au moins un mot du texte correspond à un mot du label
        if any(mot in mots for mot in mots_label):
            # Cas particuliers Campagne
            if label == "campagne":
                if numero == "5.":
                    return numero+" "+"campagne : pressions et manœuvres"
                if numero == "4.":
                    return numero+" "+"campagne : propagande"
            if label == "operation prealable au scrutin":
                if numero == "7.":
                    return numero+" "+"operation"
                else : 
                    return numero+" "+label
            return numero+" "+label
    # Aucun label trouvé → renvoyer texte normalisé
    return numero+" "+texte

"""
# @brief
# s'eppare le numero du texte d'une annotation
#
# @param
# annotation = numero et texte d'une annotation. (ex : 3.Candidature)
# @return
# numero et texte separes. exemple : ("3.", "Candidature")
# """
def sepp_num_text(annotation):
    logger.debug(f"Séparation du numéro et du texte pour l'annotation : '{annotation}'")
    chaine = annotation.strip()
    # s'eppare "12." + texte
    match = re.match(r"^\s*(\d+)\.\s*(.*)$", chaine)
    if not match:
        logger.error(f"Le format de l'annotation '{annotation}' est incorrect. Impossible de séparer le numéro et le texte.")
        return None

    numero = match.group(1) + "."
    texte = match.group(2)
    return numero, texte

"""
# @brief
# on boucle sur les considerants d'un fichier/d'un doc_id/d'un element de json_considerant
# afin de trouver le considerant de json_considerant qui correpond a celui de label et delui donner un label

# @param
# num_considerant = numéro du considerant de json_considerant
# fichier = dictionnaire contenant tous les considerant d'un fichier
# annotation = annotation issu de label a ajouter dans le dico json_considerant (c)
# """
def find_and_push(liste_correspondance, j, i):
    #colonne de ods avec les annotations proposées car le nom etait trop long
    annot_propose = label["Annotation alternative proposée"]
    annotation = None
    if liste_correspondance is not None:
        logger.debug(f"Correspondance trouvée pour {j}: {liste_correspondance}")
        if label["Vérification humaine"][liste_correspondance[0]]=="Non":
            if annot_propose[liste_correspondance[0]]is not None and not (isinstance(annot_propose[liste_correspondance[0]], float) and math.isnan(annot_propose[liste_correspondance[0]])):
                annotation = find_label_corresp_mot(annot_propose[liste_correspondance[0]])
        else:
            annotation = find_label_corresp_mot(label["Annotation"][liste_correspondance[0]])
        push_label(liste_correspondance[1], i, annotation)
    logger.debug(f" {liste_correspondance}{i['id']} n'a pas trouvé d'annotation corrigée")


"""
# @brief
# on boucle sur un element de json_considerant
# on trouve si il y a des label corrigés pour les considerant de cet element de json_considerant
# et si oui on ajoute les labels corrigés dans json_considerant

# @return
# fichierconsiderants_avec_labels.json : json_considerant avec les labels corrigés ajoutés
# """
def main() :
    logger.info(" --  recup_label.py -- \nDébut de l'extraction des labels pour les considerants ...")
    for i in json_considerants:
        # traitement des output.json
        #liste des index 
        index_considerant = find_label(i["id"]) # ex : [2, 3]
        logger.debug(f"-------------\n index_considerant pour {i['id']}: {index_considerant}")
        if index_considerant is not None:
            
            if len(index_considerant) > 1:
                for j in index_considerant:
                    liste_correspondance = fun_correspondance(j)
                    find_and_push(liste_correspondance, j, i)
            else:
                liste_correspondance = fun_correspondance(index_considerant[0])
                find_and_push(liste_correspondance, j, i)
        else:
            logger.debug(f"{i['id']} : pas de considerant trouvé")
    with open("considerants_avec_labels.json", "w", encoding="utf-8") as f:
        json.dump(json_considerants, f, ensure_ascii=False, indent=2)
        logger.info("JSON généré : considerants_avec_labels.json")
    return json_considerants

main()
