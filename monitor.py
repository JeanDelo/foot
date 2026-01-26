import requests
import hashlib
import os
from datetime import datetime
import sys

def hash_content(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

# Crée le dossier data si nécessaire
os.makedirs("data", exist_ok=True)

# Lire toutes les URLs depuis urls.txt
with open("urls.txt") as f:
    urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

changed = False
report = []

for url in urls:
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            report.append(f"⚠️ Impossible d’accéder à {url} (status {r.status_code})")
            continue

        text = r.text
        h = hash_content(text)

        filename = "data/" + hashlib.md5(url.encode()).hexdigest() + ".txt"

        if os.path.exists(filename):
            with open(filename) as old:
                if old.read() != h:
                    changed = True
                    report.append(f"🔔 Changement détecté : {url}")
        else:
            report.append(f"🆕 Page suivie : {url}")
            changed = True

        with open(filename, "w") as f:
            f.write(h)

    except Exception as e:
        report.append(f"⚠️ Erreur sur {url}: {e}")

# Affichage final
if report:
    print("\n".join(report))
else:
    print("Aucun changement", datetime.now())

# Toujours exit 0 pour que le workflow GitHub ne marque pas d’erreur
sys.exit(0)
