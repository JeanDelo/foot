import requests
import json
import os
import difflib
from datetime import datetime

# --- fichiers ---
STATE_FILE = "last_state.json"
URLS_FILE = "urls.txt"

# --- variables GitHub ---
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Vérification des variables
if not GITHUB_REPOSITORY or not GITHUB_TOKEN:
    raise ValueError("⚠️ GITHUB_REPOSITORY ou GITHUB_TOKEN non défini !")

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
        json.dump(state, f, ensure_ascii=False, indent=2)

def fetch_url(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Erreur fetch {url}: {e}")
        return None

def create_issue(title, body):
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues"
    data = {"title": title, "body": body}
    r = requests.post(url, headers=HEADERS, json=data)
    if r.status_code == 201:
        print(f"Issue créée: {title}")
    else:
        print(f"Erreur création issue {r.status_code}: {r.text}")

# --- logique principale ---
def main():
    state = load_state()
    urls = []

    with open(URLS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    for url in urls:
        content = fetch_url(url)
        if content is None:
            continue

        old_content = state.get(url)
        if old_content != content:
            # calcul diff
            diff = "\n".join(difflib.unified_diff(
                old_content.splitlines() if old_content else [],
                content.splitlines(),
                fromfile='Avant',
                tofile='Après',
                lineterm=''
            ))
            # horodatage UTC
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            issue_title = f"Modification détectée sur {url} à {now}"
            issue_body = f"Diff AVANT/APRÈS :\n```\n{diff}\n```"
            create_issue(issue_title, issue_body)

            # mettre à jour l'état
            state[url] = content

    save_state(state)

if __name__ == "__main__":
    main()
