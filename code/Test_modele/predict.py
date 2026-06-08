import json
import torch
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "final_model"
MAX_LENGTH = 128

# Fichier contenant les textes à prédire
INPUT_FILE = BASE_DIR / "../test.json" 

def main():
    if not MODEL_DIR.exists():
        raise FileNotFoundError("Le dossier final_model n'existe pas. Lance d'abord train_model.py.")

    # Chargement des données
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR))
    model.eval()

    id2label = model.config.id2label

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

        print("Texte :", text)
        print("Label prédit :", predicted_label)
        print("Confiance :", round(confidence, 4))
        print("-" * 60)

if __name__ == "__main__":
    main()