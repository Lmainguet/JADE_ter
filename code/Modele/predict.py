import json
import torch
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "final_model"
MAX_LENGTH = 128

INPUT_FILE = BASE_DIR / "data_a_predire.json"
OUTPUT_FILE = BASE_DIR / "predictions_finales.json"

def main():
    if not MODEL_DIR.exists():
        raise FileNotFoundError("Le dossier final_model n'existe pas.")
    if not INPUT_FILE.exists():
        raise FileNotFoundError("Le dossier data_a_predire.json n'existe pas.")

    # Chargement des données
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
    model.eval()

    id2label = model.config.id2label
    resultats = []

    print(f"Lancement des prédictions sur {len(data)} éléments...")

    # Boucle sur les données 
    for item in data:
        text = item["text"] 

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=MAX_LENGTH
        )

        with torch.no_grad():
            outputs = model(**inputs)

        # Récupération des prédictions et du score de confiance
        probabilities = torch.softmax(outputs.logits, dim=1)[0]
        predicted_id = int(torch.argmax(probabilities).item())
        predicted_label = id2label[predicted_id]
        confidence = float(probabilities[predicted_id])

        # Infos de base et prédiction + confiance
        item_predit = {
            "doc_id": item.get("doc_id"),
            "numero": item.get("numero"),
            "text": text,
            "pred_label": predicted_label,
            "confiance": round(confidence, 4)
        }
        resultats.append(item_predit)

    # Sauvegarde dans le nouveau fichier JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    print(f"Terminé ! Les prédictions ont été sauvegardées dans {OUTPUT_FILE.name}")

if __name__ == "__main__":
    main()