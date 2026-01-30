import requests
import hashlib
import json
import os
import smtplib
from email.mime.text import MIMEText

# =====================
# CONFIGURATION
# =====================

URLS = [
    "https://var.fff.fr/football-animation-et-loisirs/?site_id=6962_6098_10307_27589_23969_1",
    "https://var.fff.fr/football-animation-et-loisirs/?site_id=6962_6098_10307_27589_23969_4"
]

STATE_FILE = "state.json"

# ---- EMAIL ----
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "TON_ADRESSE@gmail.com"
SMTP_PASSWORD = "MOT_DE_PASSE_APPLICATION"
MAIL_TO = "TON_ADRESSE@gmail.com"

# =====================
# FONCTIONS
# =====================

def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def send_mail(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


# =====================
# MAIN
# =====================

def main():
    state = load_state()
    changes = []

    for url in URLS:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        html = response.text
        current_hash = hash_content(html)

        previous_hash = state.get(url)

        if previous_hash != current_hash:
            changes.append(url)
            state[url] = current_hash

    if changes:
        body = "🔔 Changement détecté sur les pages suivantes :\n\n"
        body += "\n".join(changes)

        send_mail(
            subject="⚽ Mise à jour détectée sur les scores FFF",
            body=body
        )

    save_state(state)


if __name__ == "__main__":
    main()
