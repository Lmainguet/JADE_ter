import math
from operator import index
import pandas as pd
import json

# Charger le fichier avec les labels verifiés
label = pd.read_excel("documents/recap_0-8_vérification_humaine_AB_AST complète.ods", engine="odf")
# json avec les considerants par fichier
with open('code/output.json') as f:
    json_considerants = json.load(f)
    
with open('code/data_objet.json') as f:
    json_label = json.load(f)
    

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

def main() :
    for i in json_considerants:
        index_considerant = find_label(i["id"]) # ex : [2, 3]
        #print(f"index_considerant pour {i['id']} : {index_considerant}")
        annot_propose = label["Annotation alternative proposée"]
        if index_considerant is not None:
            
            if len(index_considerant) > 1:
                for j in index_considerant:
                    liste_correspondance = fun_correspondance(j)
                    if liste_correspondance is not None:
                        annotation = label["Annotation"][liste_correspondance[0]]
                        if annot_propose[liste_correspondance[0]]is not None and not (isinstance(annot_propose[liste_correspondance[0]], float) and math.isnan(annot_propose[liste_correspondance[0]])):
                            annotation = annot_propose[liste_correspondance[0]]
                        for c in i["considerants"]:
                            if c["numero"] == liste_correspondance[1]:
                                c["label"].append(annotation) 
            else:
                liste_correspondance = fun_correspondance(index_considerant[0])
                if liste_correspondance is None:
                    continue
                annotation = label["Annotation"][liste_correspondance[0]]
                if annot_propose[liste_correspondance[0]]is not None and not (isinstance(annot_propose[liste_correspondance[0]], float) and math.isnan(annot_propose[liste_correspondance[0]])):
                    annotation = annot_propose[liste_correspondance[0]]

                for c in i["considerants"]:
                    if c["numero"] == liste_correspondance[1]:
                        c["label"].append(annotation)
        else:
            print(f"Aucune correspondance trouvée pour {i['id']} dans le fichier des labels.", index_considerant)
    with open("considerants_avec_labels.json", "w", encoding="utf-8") as f:
        json.dump(json_considerants, f, ensure_ascii=False, indent=2)
    return json_considerants

main()
