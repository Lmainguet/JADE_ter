import pandas as pd
import json

# Charger le fichier avec les labels verifiés
label = pd.read_excel("../documents/recap_0-8_vérification_humaine_AB_AST complète.ods", engine="odf")
# json avec les considerants par fichier
with open('output.json') as f:
    json_considerants = json.load(f)    
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
    for i in range(len(label.Fichier)):
        if doc_id in label.Fichier[i]:
            index_liste.append(i)
    return index_liste if index_liste else None

def fun_correspondance(index):#[49]
    for i in index : 
        num = int(label.Texte[i].split(".")[0].strip()) #extrait le numéro du fichier
    return i, num


for i in json_considerants:
    #liste des index 
    index_considerant = find_label(i["id"])
    #colonne de ODS
    annot_propose = label["Annotation alternative proposée"]
    
    if index_considerant is not None:
        if len(index_considerant) > 1:
            print(f"Attention : plusieurs correspondances trouvées pour {i['id']} : {index_considerant}")
        else:
            liste_correspondance = fun_correspondance(index_considerant)
            print(liste_correspondance)
            for i in liste_correspondance:
                annotation = label["Annotation"][liste_correspondance[0]]
                if annot_propose[liste_correspondance[0]]:
                    annotation = annot_propose[liste_correspondance[0]]
                print(json_considerants)
                for cons in json_considerants["considerants"]:
                    if cons["numero"] == liste_correspondance[1]:
                        cons["label"].append(annotation)
            print(json_considerants)
    else:
        print(f"Aucune correspondance trouvée pour {i['id']} dans le fichier des labels.")
                
