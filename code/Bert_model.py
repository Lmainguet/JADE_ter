import torch
from datasets import load_dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, BertTokenizerFast, BertForSequenceClassification, CamembertForSequenceClassification, CamembertTokenizerFast
from torch.utils.data import DataLoader, TensorDataset
from torch.optim import AdamW
from sklearn.metrics import classification_report

import random
import numpy as np
import torch

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

set_seed(42)


# -------------------------
# 1. Charger dataset
# -------------------------
ds = load_dataset("ahmadSiddiqi/sentiments_fr")

train_texts = list(ds["train"]["text"])
train_labels = list(ds["train"]["label"])

test_texts = list(ds["validation"]["text"])
test_labels = list(ds["validation"]["label"])

# -------------------------
# 2. Tokenizer
# -------------------------
tokenizer = CamembertTokenizerFast.from_pretrained("camembert-base")


def encode(texts, labels):
    enc = tokenizer(
        texts,
        truncation=True,
        padding="max_length",
        max_length=64,
        return_tensors="pt"
    )
    return TensorDataset(
        enc["input_ids"],
        enc["attention_mask"],
        torch.tensor(labels)
    )

train_ds = encode(train_texts, train_labels)
test_ds = encode(test_texts, test_labels)

train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
test_loader = DataLoader(test_ds, batch_size=16)

# -------------------------
# 3. Modèle
# -------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = CamembertForSequenceClassification.from_pretrained(
    "camembert-base",
    num_labels=3
).to(device)

optimizer = AdamW(model.parameters(), lr=2e-5)

# -------------------------
# 4. Entraînement simple
# -------------------------
model.train()
for epoch in range(2):
    total_loss = 0
    for input_ids, attention_mask, labels in train_loader:
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        labels = labels.to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

        total_loss += loss.item()

    print(f"Epoch {epoch+1} - Loss: {total_loss/len(train_loader):.4f}")

# -------------------------
# 5. Évaluation
# -------------------------
model.eval()
preds = []
labels_all = []

with torch.no_grad():
    for input_ids, attention_mask, labels in test_loader:
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        labels = labels.to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        logits = outputs.logits
        preds.extend(torch.argmax(logits, dim=-1).cpu().numpy())
        labels_all.extend(labels.cpu().numpy())

print(classification_report(labels_all, preds, target_names=["positive", "neutral", "negative"]))