import json
import sys
from flask import Flask, request, redirect, url_for, render_template
import os

def resource_path(relative_path):
    """
    Retourne un chemin vers un fichier situé dans ../documents/
    """
    if getattr(sys, 'frozen', False):
        # Dossier du .exe
        exe_dir = os.path.dirname(sys.executable)
        # Dossier parent (site_annotation/)
        parent_dir = os.path.dirname(exe_dir)
        # On construit le chemin vers documents/
        base_path = os.path.join(parent_dir, "../documents")
    else:
        # dossier du script
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.join(BASE_DIR, "../documents")

    return os.path.join(base_path, relative_path)

config = resource_path("considerants_avec_labels.json")
with open(config, "r", encoding="utf-8") as f:
    data = json.load(f)


__prg_version__ = "0.0.1"
__prg_name__ = "annotate_considerants"

print(">>> Flask démarre...")

app = Flask(__name__)
app.config["VERSION"] = __prg_version__
app.config['APP_NAME'] = os.environ.get('NAME', 'APP')

LABELS = ["1. irrecevabilite","2. operation prealable au scrutin","3. candidature","4. campagne : propagande","5. campagne : pressions et manœuvres","6. financement","7. operation", "8. Autres"]


@app.route("/")
def index():
    app.logger.debug("route /")
    d = int(request.args.get("decision", 0))
    c = int(request.args.get("cons", 0))
    app.logger.debug(f"decision={request.args.get('decision')}, cons={request.args.get('cons')}")
    if d >= len(data):
        return redirect(url_for("save_json"))

    decision = data[d]
    considerants = decision["considerants"]

    if c >= len(considerants):
        return redirect(url_for("index", decision=d+1, cons=0))

    cons = considerants[c]
    if not cons.get("label"):
        app.logger.debug(f"pas de label donné donc pas besoin de corriger,  decision={d}, cons={c} (label vide)")
        return redirect(url_for("index", decision=d, cons=c+1))
    try : 
        return render_template(
            "index.html",
            decision_id=d,
            cons_id=c,
            text=cons["text"],
            labels=LABELS
        )
    except Exception as e:
        app.logger.error(f"Erreur lors du rendu de la page : {e}")
        return f"<h2>Erreur lors du rendu de la page</h2>"


@app.route("/label", methods=["POST"])
def set_label():
    app.logger.debug("route /label")
    d = int(request.form["decision"])
    c = int(request.form["cons"])
    label = request.form["label"]
    data[d]["considerants"][c]["label_corrige"] = label
    return redirect(url_for("index", decision=d, cons=c+1))


@app.route("/save_json")
def save_json():
    app.logger.debug("route /save_json")
    output_path = resource_path("considerants_annotes.json")

    try : 
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.error(f"Erreur lors de la sauvegarde du JSON : {e}")
        return f"<h2>Erreur lors de la sauvegarde du JSON</h2>"

    return f"<h2>JSON sauvegardé dans {output_path}</h2>"


import webbrowser
import threading

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run()
