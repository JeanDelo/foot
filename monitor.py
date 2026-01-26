import requests
import json
import os
import difflib
from datetime import datetime
import pytz  # Pour heure de Paris

STATE_FILE = "last_state.json"
URLS_FILE = "urls.txt"

GITHUB_REPO = os.environ["GITHUB_REPOSITORY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- fonctions utilitaires ---

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def visible_text(html):
    """Extraire les lignes visibles de la page (simple, robuste)"""
    return "\n".join(line.strip() for line in html.splitlines() if line.strip())

def make_diff(old, new, max_lines=20):
    """Créer un diff lisible entre deux textes"""
    diff = list(difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        lineterm=""
    ))
    return "\n".join(diff[:max_lines])

def create_issue(title, body):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    requests.post(url, headers=HEADERS, json={
        "title": title,
        "body": body
    })

# --- chargement état précédent ---
state = load_state()
new_state = {}

current_group = "Sans catégorie"

# --- lecture des URLs ---
with open(URLS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            current_group = line.replace("#", "").strip()
            continue

        url = line

        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            text = visible_text(response.text)
        except Exception as e:
            create_issue(
                f"⚠️ Erreur d’accès ({current_group})",
                f"URL : {url}\n\nErreur : {e}"
            )
            continue

        old_text = state.get(url)

        if old_text and old_text != text:
            diff = make_diff(old_text, text)

            # heure Paris
            tz = pytz.timezone("Europe/Paris")
            paris_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M')

            create_issue(
                f"🔔 Score modifié – {current_group}",
                f"""La page a changé.

URL :
{url}

CHANGEMENT DÉTECTÉ :
```diff
{diff}
