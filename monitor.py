import json
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText

# -------------------
# CONFIGURATION MAIL
# -------------------
SMTP_SERVER = "smtp.example.com"        # serveur SMTP de ton mail
SMTP_PORT = 587                          # port SMTP (souvent 587)
SMTP_USER = "tonmail@example.com"       # ton adresse mail
SMTP_PASSWORD = "tonmotdepasse"         # mot de passe / token
MAIL_TO = "destinataire@example.com"    # mail qui reçoit la notification

def send_mail(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

# -------------------
# URL à surveiller
# -------------------
URL = "https://var.fff.fr/football-animation-et-loisirs/?site_id=6962_6098_10307_27589_23969_4"

# Fichier pour mémoriser l'état précédent
STATE_FILE = "state.json"

# Charger l'état précédent
try:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
except:
    state = {"teams": []}

# -------------------
# Lancer Playwright pour récupérer les noms d'équipes
# -------------------
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_timeout(3000)  # attendre que le JS charge la page
    # Sélecteur CSS exact pour les noms d'équipes sur cette page FFF
    teams = [el.inner_text() for el in page.query_selector_all("div.team-name")]
    browser.close()

# -------------------
# Comparer avec l'état précédent
# -------------------
new_teams = [t for t in teams if t not in state["teams"]]

if new_teams:
    body = "Nouveaux matchs détectés :\n" + "\n".join(new_teams)
    send_mail("Notification FFF - Nouveaux matchs", body)

# -------------------
# Sauvegarder le nouvel état
# -------------------
with open(STATE_FILE, "w") as f:
    json.dump({"teams": teams}, f)
