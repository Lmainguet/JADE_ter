import json
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit
from collections import Counter
import logging
from logging_config import setup_logging

setup_logging("PROD")  # ou "DEV"
logger = logging.getLogger(__name__)

# Chargement 
try :
    with open("considerants_avec_labels.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except : 
    logger.info("Le fichier considerants_avec_labels.json n'existe pas")

# Filtrage
EXCLURE = ["1. irrecevabilite","1. procedure", "None", None]
dataset = [
    {"doc_id": d["id"], "numero": c["numero"], "text": c["text"], "label": c["label"]}
    for d in data for c in d.get("considerants", [])
    if c.get("label") and c["label"][0] not in EXCLURE
]

# S'ocuper du label qui n'a que 3 occurences
X = np.array([i for i in dataset if i["label"][0] != "2. operation prealable au scrutin"])
rare = [i for i in dataset if i["label"][0] == "2. operation prealable au scrutin"]
y = [i["label"][0] for i in X]

# Découpage
tr_idx, reste_idx = next(StratifiedShuffleSplit(n_splits=1, test_size=0.30, random_state=42).split(X, y))
dev_idx, ts_idx = next(StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=42).split(X[reste_idx], [y[i] for i in reste_idx]))

# Sauvegarde
for nom, idx in [("train.json", tr_idx), ("dev.json", reste_idx[dev_idx]), ("test.json", reste_idx[ts_idx])]:
    with open(nom, "w", encoding="utf-8") as f:
        donnees = X[idx].tolist() + (rare if nom == "train.json" else [])
        json.dump(donnees, f, ensure_ascii=False, indent=2)

#Extraction et sauvegarde des textes vides
data_a_predire = [
    {"doc_id": d["id"], "numero": c["numero"], "text": c["text"]}
    for d in data for c in d.get("considerants", [])
    if not c.get("label") or c["label"][0] in EXCLURE or not c["label"]
]

with open("data_a_predire.json", "w", encoding="utf-8") as f:
    json.dump(data_a_predire, f, ensure_ascii=False, indent=2)

# Comptage
for nom in ["train.json", "dev.json", "test.json"]:
    with open(nom, "r", encoding="utf-8") as f:
        contenu = json.load(f)
    logger.info(f"\n--- {nom} ({len(contenu)} éléments) ---")
    for label, nb in Counter([c["label"][0] for c in contenu]).most_common():
        logger.info(f"  - {label} : {nb}")