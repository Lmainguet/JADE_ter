import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
STATS_DIR = BASE_DIR / "stats_predictions"

def main():
    #Chargement des scores du modèle
    try:
        logits = np.load(STATS_DIR / "logits.npy")
        vrais_labels = np.load(STATS_DIR / "vrais_labels.npy")
    except FileNotFoundError:
        print("Erreur : relance d'abord le fichier train_model.py !")
        return

    # Récupération des prédictions et de leur score de confiance
    probs = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
    pred_ids = np.argmax(probs, axis=1)
    confiances = np.max(probs, axis=1)

    #Test des différents seuils
    seuils = np.arange(0, 1, 0.05)
    precisions, rappels = [], []
    f_scores = []

    print(f"{'Seuil':<6} | {'Précision':<10} | {'Rappel':<10} | {'F-score':<10} | {'Vides':<15}")
    print("-" * 65)

    for s in seuils:
        indices_valides = [i for i in range(len(probs)) if confiances[i] >= s]
        nb_vides = len(probs) - len(indices_valides)
        
        # Précision
        if len(indices_valides) > 0:
            justes = sum([1 for i in indices_valides if pred_ids[i] == vrais_labels[i]])
            p = justes / len(indices_valides)
        else:
            p = 1.0
            
        # Rappel
        justes_total = sum([1 for i in range(len(probs)) if confiances[i] >= s and pred_ids[i] == vrais_labels[i]])
        r = justes_total / len(vrais_labels)
        
        # F-score
        f = 2 * (p * r) / (p + r)
        
        precisions.append(p)
        rappels.append(r)
        f_scores.append(f)
        
        print(f"{s:.2f}   | {p:.4f}     | {r:.4f}     | {f:.4f}    | {nb_vides} / {len(vrais_labels)}")

    #Tracé du graphique
    plt.figure(figsize=(8, 6))
    plt.plot(seuils, precisions, label="Précision", color="blue", marker="o")
    plt.plot(seuils, rappels, label="Rappel", color="orange", marker="s")
    plt.plot(seuils, f_scores, label="F-score", color="green", marker="^")
    
    plt.title("Optimisation du Seuil de Confiance")
    plt.xlabel("Seuil")
    plt.ylabel("Score")
    plt.ylim(-0.05, 1.05)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    
    plt.savefig(BASE_DIR / "courbe_seuils.png")
    plt.show()

if __name__ == "__main__":
    main()