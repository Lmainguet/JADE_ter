import inspect
import json
from pathlib import Path
import numpy as np
import pandas as pd
from datasets import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments, TrainerCallback
import logging
from logging_config import setup_logging

setup_logging("PROD")  # ou "DEV"
logger = logging.getLogger(__name__)

# Chemins des données et modèles
BASE_DIR = Path(__file__).resolve().parent
TRAIN_FILE = BASE_DIR / "train.json"
DEV_FILE = BASE_DIR / "dev.json"
TEST_FILE = BASE_DIR / "test.json"

MODEL_NAME = "almanach/camembert-base"
OUTPUT_DIR = BASE_DIR / "bert_text_classifier"
FINAL_MODEL_DIR = BASE_DIR / "final_model"

# Paramètres du modèle
NUM_EPOCHS = 3
BATCH_SIZE = 8
MAX_LENGTH = 128

# Fonction callback pour afficher proprement les scores pendant l'entraînement
class AffichagePrecisionCallback(TrainerCallback):
    def on_evaluate(self, args, state, control, metrics, **kwargs):
        epoch = int(state.epoch) if state.epoch is not None else 0
        accuracy = metrics.get("eval_accuracy")
        precision = metrics.get("eval_precision")
        
        if accuracy is not None and precision is not None:
            logger.info(f"\n--- Époque {epoch} ---")
            logger.info(f"Accuracy : {accuracy:.4f} | Précision : {precision:.4f}")
            logger.info("-" * 20)

def make_training_arguments():
    params = {
        "output_dir": str(OUTPUT_DIR),
        "save_strategy": "epoch",
        "learning_rate": 2e-5,
        "per_device_train_batch_size": BATCH_SIZE,
        "per_device_eval_batch_size": BATCH_SIZE,
        "num_train_epochs": NUM_EPOCHS,
        "weight_decay": 0.01,
        "logging_dir": str(BASE_DIR / "logs"),
        "logging_steps": 50,
        "load_best_model_at_end": True,
        "save_total_limit": 2
    }
    
    # Gestion des versions de transformers
    signature = inspect.signature(TrainingArguments.__init__)
    if "eval_strategy" in signature.parameters:
        params["eval_strategy"] = "epoch"
    else:
        params["evaluation_strategy"] = "epoch"

    return TrainingArguments(**params)

# Calcul des métriques classiques
def compute_metrics(pred):
    logits, true_labels = pred
    predicted_labels = np.argmax(logits, axis=1)

    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels, predicted_labels, average="weighted", zero_division=0
    )
    accuracy = accuracy_score(true_labels, predicted_labels)

    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}

def main():
    #Chargement des fichiers
    print("Chargement des données...")
    with open(TRAIN_FILE, "r", encoding="utf-8") as f: train_data = json.load(f)
    with open(DEV_FILE, "r", encoding="utf-8") as f: dev_data = json.load(f)
    with open(TEST_FILE, "r", encoding="utf-8") as f: test_data = json.load(f)

    train_df = pd.DataFrame(train_data)
    dev_df = pd.DataFrame(dev_data)
    test_df = pd.DataFrame(test_data)

    # Nettoyage si les labels sont dans des listes
    train_df["label"] = train_df["label"].apply(lambda x: x[0] if isinstance(x, list) else x)
    dev_df["label"] = dev_df["label"].apply(lambda x: x[0] if isinstance(x, list) else x)
    test_df["label"] = test_df["label"].apply(lambda x: x[0] if isinstance(x, list) else x)

    # Mapping des labels textuels en identifiants numériques
    all_labels = sorted(pd.concat([train_df["label"], dev_df["label"], test_df["label"]]).unique())
    label2id = {label: index for index, label in enumerate(all_labels)}
    id2label = {index: label for label, index in label2id.items()}

    train_df["label"] = train_df["label"].map(label2id)
    dev_df["label"] = dev_df["label"].map(label2id)
    test_df["label"] = test_df["label"].map(label2id)

    # Conversion pour Hugging Face
    train_dataset = Dataset.from_pandas(train_df.reset_index(drop=True))
    dev_dataset = Dataset.from_pandas(dev_df.reset_index(drop=True))
    test_dataset = Dataset.from_pandas(test_df.reset_index(drop=True))

    #Tokenisation avec CamemBERT
    print("Tokenisation...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_function(batch):
        return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=MAX_LENGTH)

    train_dataset = train_dataset.map(tokenize_function, batched=True)
    dev_dataset = dev_dataset.map(tokenize_function, batched=True)
    test_dataset = test_dataset.map(tokenize_function, batched=True)

    # Suppression des colonnes inutiles pour le modèle
    cols_to_remove = [c for c in train_dataset.column_names if c not in ["input_ids", "attention_mask", "label"]]
    train_dataset = train_dataset.remove_columns(cols_to_remove)
    dev_dataset = dev_dataset.remove_columns(cols_to_remove)
    test_dataset = test_dataset.remove_columns(cols_to_remove)

    train_dataset.set_format("torch")
    dev_dataset.set_format("torch")
    test_dataset.set_format("torch")

    #Initialisation du modèle CamemBERT
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=len(all_labels), label2id=label2id, id2label=id2label
    )

    training_args = make_training_arguments()

    trainer_params = {
        "model": model,
        "args": training_args,
        "train_dataset": train_dataset,
        "eval_dataset": dev_dataset, 
        "compute_metrics": compute_metrics
    }

    # Compatibilité du tokenizer selon la version installée
    trainer_signature = inspect.signature(Trainer.__init__)
    if "processing_class" in trainer_signature.parameters:
        trainer_params["processing_class"] = tokenizer
    elif "tokenizer" in trainer_signature.parameters:
        trainer_params["tokenizer"] = tokenizer

    trainer = Trainer(**trainer_params)
    trainer.add_callback(AffichagePrecisionCallback())

    #Entraînement
    print("Début de l'entraînement...")
    trainer.train()

    #Sauvegarde des logits de test pour faire les courbes de seuil après
    print("Sauvegarde des prédictions brutes pour les courbes de seuils...")
    logits = trainer.predict(test_dataset).predictions
    vrais_labels = np.array(test_dataset["label"])

    stats_dir = BASE_DIR / "stats_predictions"
    stats_dir.mkdir(exist_ok=True)
    np.save(stats_dir / "logits.npy", logits)
    np.save(stats_dir / "vrais_labels.npy", vrais_labels)

    # Sauvegarde finale du modèle entraîné
    trainer.save_model(str(FINAL_MODEL_DIR))
    tokenizer.save_pretrained(str(FINAL_MODEL_DIR))

    with open(FINAL_MODEL_DIR / "labels.json", "w", encoding="utf-8") as file:
        json.dump({"labels": all_labels, "label2id": label2id, "id2label": id2label}, file, ensure_ascii=False, indent=2)

    print("Modèle entraîné et sauvegardé avec succès.")

if __name__ == "__main__":
    main()