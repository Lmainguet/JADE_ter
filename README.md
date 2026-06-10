### Automate grievance annotation for the [JADE project](https://blogdudroitelectoral.fr/justice-algorithmique-des-elections-jade/)

## Pipeline creation du dataset
Génération du JSON des données annotées

# Mise en place de l'environnement

se placer dans `/grief/stage_2026/code`
creation d'un environnement python une seule fois apres le git clone
```python3 -m venv venv```

installer les librairies une seule fois apres la creation de l'environnement python venv
```
python3 -m pip install --break-system-packages -r ../requirement.txt
pip install pandas
```

# Commande à faire pour lancer le projet

activate python env a chaque fois que vous travaillez sur le projet.
un (venv) doit etre present dans votre terminal
```source venv/bin/activate```
vous devez voir : `(venv) louane@ordinateur:~/arborescence/griefs/stage_2026/code`

taper les commandes suivantes dans l'ordre pour lancer les fichiers python
```
python before_training.py
python recup_label.py
python count_label_occurence.py
```
vous pouvez maintenant recuperer les données à utiliser dans considerants_avec_label.json

## Modele reseau de neurone
## Comment lancer les codes :

# Se placer dans JADE_ter/code
creation d'un environnement python une seule fois apres le git clone
```python3 -m venv venv```
Puis l'activer à chaque utilisation du code
```source venv/bin/activate```

installer les librairies une seule fois apres la creation et l'activation de l'environnement python venv
```pip install -r requirements.txt```

# Se placer dans JADE_ter/code/Modele
Vérifier que le fichier considerants_avec_labels.json existe
Lancer Séparation.py
```python Séparation.py```

Les fichiers utilisés par train_model.py sont désormais créés

Lancer train_model.py
```python train_model.py```

Le modèle est entrainé, on peut donc lancer plot_seuils.py pour voir rappel, précision et f score
```python plot_seuils.py```

Ou lancer predict.py pour faire des précisions sur des nouvelles données
```python predict.py```

Les prédictions sont dans predictions_finales.json

---
# arborescence et explication des fichiers
- before_training.py : recuperation des considerants des xml contenus dans les dossiers AN/*/rejet et AN/*/annulation, creation du json output.json associé
- Bert_model.py : modele d'essaie
- count_label_occurence.py : compte le nombre d'occurence de chaque label dans considerants_avec_labels.json
- recup_label.py : traite output.json et documents/recap_0-8_vérification_humaine_AB_AST complète.ods afin d'attribuer un label aux considerants corrigés. Genere considerants_avec_labels.json qui possede une liste des considerants et les labels corrigés associés.
'''
[
  {
    "id": "CONSTEXT000017665826",
    "considerants": [
      {
        "numero": 1,
        "text": "Considérant qu'en soulevant un moyen tiré de ce que les procès-verbaux de recensement des votes de certains bureaux font apparaître un excédent dans le nombre des enveloppes et bulletins sans enveloppe trouvés dans l'urne par rapport au nombre des émargements, ...",
        "label": [
          "7. operation prealable au scrutin"
        ]
      },   
      {...}
    ]
  },
  {
    "id": "CONSTEXT000017665819",
    "considerants": [
      {
        "numero": 1,
        "text": "",
        "label": []
      }
    ]
  }
]
'''

