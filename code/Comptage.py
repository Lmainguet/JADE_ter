import json
from collections import Counter


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
print(f"Analyse des labels pour le fichier : {nom_fichier}")
print(f"Nombre total de labels attribués : {len(tous_les_labels)}")

# Affichage de chaque label avec son total
for label, nb in compte_labels.most_common():
    print(f" - {label} : {nb}")