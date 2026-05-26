import json
import pandas as pd
import os
import re
import xml.etree.ElementTree as ET
from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split


RACINE = "../documents/AN/1958"

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
    return blocs


def create_dico_considerants(RACINE=RACINE,output_json="output.json"):
    # le dico final avec tous les fichiers et les considerants des fichiers
    documents = []
    
    for root, dirs, files in os.walk(RACINE):
        dossier = root.lower()
        if "rejet" not in dossier and "annulation" not in dossier:
            #print("pas de dossier rejet ou annualtion trouvé")
            continue

        for f in files:
            if not f.endswith("_annot.xml"):
                #print(f"Le fichier {f} n'est pas un fichier XML d'annotation")
                continue

            chemin = os.path.join(root, f)
            #print(f"\n {chemin}")
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
                print(documents)
            except Exception as e:
                print(f"Erreur XML dans {chemin} : {e}")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"JSON généré : {output_json}")
    return documents


def dict_to_datasetdict(data_dict, test_size=0.15, seed=42):
    # Convertir le dict en liste d'exemples
    texts = []
    labels = []

    for item in data_dict.values():
        #print(item)
        texts.append(item["text"])
        labels.append(item.get("label", []))

    # Split train / validation
    train_idx, val_idx = train_test_split(
        range(len(texts)),
        test_size=test_size,
        random_state=seed,
        shuffle=True
    )

    # Construire les datasets
    train_dataset = Dataset.from_dict({
        "text": [texts[i] for i in train_idx],
        "label": [labels[i] for i in train_idx],
    })

    val_dataset = Dataset.from_dict({
        "text": [texts[i] for i in val_idx],
        "label": [labels[i] for i in val_idx],
    })

    return DatasetDict({
        "train": train_dataset,
        "validation": val_dataset
    })
    
print(create_dico_considerants())
