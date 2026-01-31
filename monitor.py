import requests
import hashlib
import json
import os
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

URLS = [
    # tes 42 liens ici
]

STATE_FILE = "state.json"

# -----------------------------
# Chargement de l'état précédent
# -----------------------------
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {}

changes = []

# -----------------------------
# Analyse des pages
# -----------------------------
for url in URLS:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # 🔒 Contenu STABLE : texte visible uniquement
        text = soup.get_text(separator=" ", strip=True)

        # Nettoyage anti-bruit
        text = " ".join(text.split())

        current_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        previous_hash = state.get(url)

        if previous_hash and previous_hash != current_hash:
            changes.append(url)

        # ⚠️ ON MET À JOUR APRÈS COMPARAISON
        state[url] = current_hash

    except Exception as e:
        print(f"Erreur sur {url} : {e}")

# -----------------------------
# Envoi mail UNIQUEMENT si changement
# -----------------------------
if changes:
    body = "Changement détecté sur les pages suivantes :\n\n"
    body += "\n".join(changes)

    msg = MIMEText(body)
    msg["Subject"] = "🔔 Changement détecté sur le site surveillé"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["SMTP_USER"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(
            os.environ["SMTP_USER"],
            os.environ["SMTP_PASSWORD"]
        )
        server.send_message(msg)

    print(f"Mail envoyé ({len(changes)} pages)")
else:
    print("Aucun changement détecté")

# -----------------------------
# Sauvegarde de l'état
# -----------------------------
with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)

print("state.json mis à jour")