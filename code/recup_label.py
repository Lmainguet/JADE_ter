import math
from operator import index
import re
import unicodedata
import pandas as pd
import json

MODE = "PROD"   # ou "DEV"

# Charger le fichier avec les labels verifiés
label = pd.read_excel("../documents/recap_0-8_vérification_humaine_AB_AST complète.ods", engine="odf")
# json avec les considerants par fichier
with open('output.json') as f:
    json_considerants = json.load(f)
    
with open('data_objet.json') as f:
    json_label = json.load(f)
    
"""
# @brief
#avoir les commentaires et etapes de dev 
# @param
# *arg = "explication"
# **kwargs = "fichier" : fichier.json

# @return
# print
# """
def log(*args, step=None):
    if MODE == "DEV":
        print(step, *args)


"""
# @brief
#trouve la ligne du fichier des labels qui correspond a l'id du fichier donné en entrée
# @param
# doc_id = id du doc xml

# @return
# liste des index du ODS qui traitent le xml donné grace à l'id
# """
def find_label(doc_id):
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
    except Exception:
        return None
    
"""
# @brief
# on boucle sur les considerants d'un fichier/d'un doc_id/d'un element de json_considerant
# afin de trouver le considerant de json_considerant qui correpond a celui de label et delui donner un label

# @param
# num_considerant = numéro du considerant de json_considerant
# fichier = dictionnaire contenant tous les considerant d'un fichier
# annotation = annotation issu de label a ajouter dans le dico json_considerant (c)
# """
def push_label(num_considerant, fichier, annotation):
    for c in fichier["considerants"]:
        if c["numero"] == num_considerant:
            c["label"].append(annotation)
            log(f"ajout de annotation pour le considerant {num_considerant}: {annotation}", step="push_label()")

import re
import unicodedata

def clean_annot(annotation):
    liste_mots = ["procedure", "candidature", "campagne", "operations", "financement", "prealable", "irrecevabilite"]
    chaine = annotation.strip()

    # Regex : capture "12." + texte
    match = re.match(r"^\s*(\d+)\.\s*(.*)$", chaine)
    if not match:
        return "error"

    numero = match.group(1) + "."
    texte = match.group(2)
    # Nettoyage : enlever accents + minuscule
    texte_sans_accents = unicodedata.normalize("NFD", texte)
    texte_sans_accents = "".join(
        c for c in texte_sans_accents if unicodedata.category(c) != "Mn"
    )
    texte_clean = texte_sans_accents.lower()

    # Découpe le texte en mots
    mots = re.findall(r"\w+", texte_clean)
    # Comparer avec la liste
    for mot in mots:
        if mot in liste_mots:
            #probleme d'ecriture de campagne, parfois campagne tout seul parfois avec plusiuers num diff
            if mot.startswith("campagne") and numero == "5.":
                return numero+" "+"campagne : pressions et manœuvres"
            if mot.startswith("campagne") and numero == "4.":
                return numero+" "+"campagne : propagande"
            return numero+" "+mot
    return numero+texte_clean

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
    
    if liste_correspondance is not None:
        log("correspondance pour", f"{j}: {liste_correspondance}", step="find_and_push()")
        if label["Vérification humaine"][liste_correspondance[0]]=="Non":
            annotation = "error"
        else:
            annotation = label["Annotation"][liste_correspondance[0]]
            if annot_propose[liste_correspondance[0]]is not None and not (isinstance(annot_propose[liste_correspondance[0]], float) and math.isnan(annot_propose[liste_correspondance[0]])):
                annotation2 = clean_annot(annot_propose[liste_correspondance[0]])
                print("annotation2", annotation2, j, i)
            annotation = clean_annot(annotation)
            if annotation is None:
                annotation = "error"
        log("correspondance annotation", f'{j}: {annotation}', step="find_and_push()")
        push_label(liste_correspondance[1], i, annotation)

def label_super_object(texte):
    for i in json_label_maritaud:
        print(i)

#print(label_super_object("Considérant qu'il résulte de ce qui précède que la diffusion de ces tracts"))
"""
# @brief
# on boucle sur un element de json_considerant
# on trouve si il y a des label corrigés pour les considerant de cet element de json_considerant
# et si oui on ajoute les labels corrigés dans json_considerant

# @return
# fichierconsiderants_avec_labels.json : json_considerant avec les labels corrigés ajoutés
# """
def main() :
    print("Début de l'extraction des labels pour les considerants ...")
    for i in json_considerants:
        # traitement des output.json
        #liste des index 
        index_considerant = find_label(i["id"]) # ex : [2, 3]
        log("-------------\n index_considerant pour", f"{i['id']}: {index_considerant}", step="main()")
        if index_considerant is not None:
            
            if len(index_considerant) > 1:
                for j in index_considerant:
                    liste_correspondance = fun_correspondance(j)
                    find_and_push(liste_correspondance, j, i)
            else:
                j = index_considerant[0]
                liste_correspondance = fun_correspondance(index_considerant[0])
                find_and_push(liste_correspondance, j, i)
        else:
            log("Aucune correspondance trouvée pour ", f"{i['id']}", "dans le fichier des labels.", step="main()")
        
        # traitement de super_object.json 
        
    with open("considerants_avec_labels.json", "w", encoding="utf-8") as f:
        json.dump(json_considerants, f, ensure_ascii=False, indent=2)
    return json_considerants

main()
