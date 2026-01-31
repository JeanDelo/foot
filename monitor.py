import requests
import hashlib
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from bs4 import BeautifulSoup

# =====================
# CONFIG
# =====================

URLS_FILE = "urls.txt"
STATE_FILE = "state.json"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_TO = SMTP_USER

# =====================
# UTILS
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
        json.dump(state, f, indent=2, ensure_ascii=False)

def send_mail(subject, body):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.sendmail(SMTP_USER, MAIL_TO, msg.as_string())
    server.quit()

def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    # Supprimer scripts et styles
    for tag in soup(["script", "style"]):
        tag.decompose()
    # Récupérer le texte visible
    text = soup.get_text(separator=" ", strip=True)
    # Normaliser les espaces
    text = " ".join(text.split())
    return text

# =====================
# MAIN
# =====================

def main():
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER ou SMTP_PASSWORD manquant (secrets GitHub)")

    state = load_state()
    new_state = {}

    changes = []

    with open(URLS_FILE, "r", encoding="utf-8") as f:
        urls = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]

    for url in urls:
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()

            content_text = extract_visible_text(r.text)
            content_hash = hash_content(content_text)
            new_state[url] = content_hash

            if url not in state:
                changes.append(f"[NOUVELLE PAGE]\n{url}\n")
            elif state[url] != content_hash:
                changes.append(f"[CHANGEMENT RÉEL DÉTECTÉ]\n{url}\n")

        except Exception as e:
            changes.append(f"[ERREUR]\n{url}\n{e}\n")

    if changes:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        body = f"Changements détectés ({now})\n\n" + "\n".join(changes)
        send_mail("Web Monitor – changement détecté", body)

    save_state(new_state)

if __name__ == "__main__":
    main()