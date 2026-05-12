# etre connecté au serveur P:\CRJ\RECHERCHE\PROJET_JADE et au vpn cisco
import pandas as pd

chemin = r"P:\CRJ\RECHERCHE\PROJET_JADE\JADE_COMMUN\Annotation\Annotation_automatique_Maritaud\Technologie_light\Super-catégories-objets_0,8\recap_0-8_vérification_humaine_AB_AST complète.ods"
df = pd.read_excel(chemin, engine="odf")
print(df.head())
