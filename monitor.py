import requests
import hashlib
import os
from datetime import datetime

def hash_content(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

os.makedirs("data", exist_ok=True)

with open("urls.txt") as f:
    urls = [line.strip() for line in f if line.strip()]

changed = False
report = []

for url in urls:
    try:
        r = requests.get(url, timeout=20)
        # On n’arrête plus le script si la page n’est pas accessible
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
        # Au lieu de planter, on note l’erreur et on continue
        report.append(f"⚠️ Erreur sur {url}: {e}")

if report:
    print("\n".join(report))
else:
    print("Aucun changement", datetime.now())
