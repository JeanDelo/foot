#!/usr/bin/env python3
"""
Monitor v2 - Surveillance des résultats U11 District du Var
Détecte les changements sur les pages web, génère des diffs et archive les snapshots.
"""

import requests
import hashlib
import json
import os
import smtplib
import difflib
from datetime import datetime
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# Configuration
STATE_FILE = "state.json"
URLS_FILE = "urls.txt"
ARCHIVES_DIR = "archives"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# -----------------------------
# Fonctions utilitaires
# -----------------------------

def load_urls(filepath):
    """Charge les URLs depuis un fichier (ignore lignes vides et commentaires #)."""
    urls = []
    if not os.path.exists(filepath):
        print(f"ERREUR: Fichier {filepath} introuvable")
        return urls

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def load_state(filepath):
    """Charge l'état précédent et migre l'ancien format si nécessaire."""
    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Migration de l'ancien format (string hash) vers le nouveau format (dict)
    migrated = {}
    for url, data in state.items():
        if isinstance(data, str):
            # Ancien format : juste le hash
            migrated[url] = {
                "hash": data,
                "text": "",
                "scores": "",
                "last_check": ""
            }
        else:
            # Nouveau format : dict complet
            migrated[url] = data

    return migrated


def save_state(state, filepath):
    """Sauvegarde l'état dans le fichier JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def extract_text(html):
    """Extrait le texte visible en supprimant les balises non pertinentes."""
    soup = BeautifulSoup(html, "lxml")

    # Supprimer les balises non pertinentes
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # Extraire le texte
    text = soup.get_text(separator="\n", strip=True)

    # Nettoyer les lignes multiples vides
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def extract_scores(html):
    """Extrait les tableaux HTML (scores) de la page."""
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")

    if not tables:
        return ""

    scores_text = []
    for i, table in enumerate(tables):
        rows = table.find_all("tr")
        table_text = []
        for row in rows:
            cells = row.find_all(["td", "th"])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            if any(cell_texts):  # Ignorer les lignes vides
                table_text.append(" | ".join(cell_texts))
        if table_text:
            scores_text.append(f"=== Tableau {i+1} ===\n" + "\n".join(table_text))

    return "\n\n".join(scores_text)


def generate_diff(old_text, new_text, url):
    """Génère un diff unifié entre l'ancien et le nouveau contenu."""
    old_lines = old_text.split("\n") if old_text else []
    new_lines = new_text.split("\n") if new_text else []

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="Avant",
        tofile="Après",
        lineterm=""
    )
    return "\n".join(diff)


def archive_snapshot(url, text, scores, hash_value):
    """Archive un snapshot dans le dossier archives/."""
    os.makedirs(ARCHIVES_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Créer un nom de fichier sûr à partir de l'URL
    safe_name = hashlib.md5(url.encode()).hexdigest()[:12]
    filename = f"{timestamp}_{safe_name}.txt"
    filepath = os.path.join(ARCHIVES_DIR, filename)

    content = f"""URL: {url}
Date: {datetime.now().isoformat()}
Hash: {hash_value}

=== SCORES ===
{scores if scores else "(aucun tableau détecté)"}

=== CONTENU COMPLET ===
{text}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def send_email(subject, body):
    """Envoie un email de notification."""
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    notify_email = os.environ.get("NOTIFY_EMAIL", smtp_user)

    if not smtp_user or not smtp_password:
        print("ERREUR: Variables SMTP_USER et SMTP_PASSWORD requises")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = notify_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"ERREUR envoi mail: {e}")
        return False


# -----------------------------
# Programme principal
# -----------------------------

def main():
    print(f"=== Monitor v2 - {datetime.now().isoformat()} ===\n")

    # Charger les URLs et l'état
    urls = load_urls(URLS_FILE)
    if not urls:
        print("Aucune URL à surveiller")
        return

    state = load_state(STATE_FILE)

    # Statistiques
    total = len(urls)
    changes = []
    errors = []

    # Headers HTTP
    headers = {"User-Agent": USER_AGENT}

    # Analyser chaque URL
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{total}] {url[:60]}...", end=" ")

        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            html = response.text
            current_text = extract_text(html)
            current_scores = extract_scores(html)
            current_hash = hashlib.sha256(current_text.encode("utf-8")).hexdigest()

            # Récupérer l'état précédent
            previous = state.get(url, {})
            previous_hash = previous.get("hash", "") if isinstance(previous, dict) else previous
            previous_text = previous.get("text", "") if isinstance(previous, dict) else ""
            previous_scores = previous.get("scores", "") if isinstance(previous, dict) else ""

            # Détecter les changements
            if previous_hash and previous_hash != current_hash:
                print("→ CHANGEMENT DÉTECTÉ")

                # Générer le diff
                diff = generate_diff(previous_text, current_text, url)

                # Archiver le snapshot
                archive_path = archive_snapshot(url, current_text, current_scores, current_hash)

                changes.append({
                    "url": url,
                    "diff": diff,
                    "old_scores": previous_scores,
                    "new_scores": current_scores,
                    "archive": archive_path
                })
            elif not previous_hash:
                print("→ Première analyse")
            else:
                print("→ Pas de changement")

            # Mettre à jour l'état
            state[url] = {
                "hash": current_hash,
                "text": current_text,
                "scores": current_scores,
                "last_check": datetime.now().isoformat()
            }

        except requests.exceptions.Timeout:
            print("→ ERREUR: Timeout")
            errors.append({"url": url, "error": "Timeout"})
        except requests.exceptions.HTTPError as e:
            print(f"→ ERREUR HTTP: {e.response.status_code}")
            errors.append({"url": url, "error": f"HTTP {e.response.status_code}"})
        except Exception as e:
            print(f"→ ERREUR: {e}")
            errors.append({"url": url, "error": str(e)})

    # Résumé
    print(f"\n=== RÉSUMÉ ===")
    print(f"URLs analysées: {total}")
    print(f"Changements détectés: {len(changes)}")
    print(f"Erreurs: {len(errors)}")

    # Envoyer le mail si des changements sont détectés
    if changes:
        subject = f"🔔 {len(changes)} changement(s) détecté(s) - Résultats U11"

        body_parts = ["Changements détectés sur les pages suivantes:\n"]

        for change in changes:
            body_parts.append(f"\n{'='*60}")
            body_parts.append(f"URL: {change['url']}\n")

            if change['old_scores'] or change['new_scores']:
                body_parts.append("\n--- SCORES AVANT ---")
                body_parts.append(change['old_scores'] if change['old_scores'] else "(aucun)")
                body_parts.append("\n--- SCORES APRÈS ---")
                body_parts.append(change['new_scores'] if change['new_scores'] else "(aucun)")

            body_parts.append("\n--- DIFF ---")
            body_parts.append(change['diff'] if change['diff'] else "(diff non disponible - première capture du contenu)")

        if errors:
            body_parts.append(f"\n\n{'='*60}")
            body_parts.append(f"⚠️ {len(errors)} erreur(s) rencontrée(s):")
            for err in errors:
                body_parts.append(f"  - {err['url']}: {err['error']}")

        body = "\n".join(body_parts)

        if send_email(subject, body):
            print(f"Mail envoyé ({len(changes)} changement(s))")
        else:
            print("Échec envoi mail")
    else:
        print("Aucun changement détecté - pas de mail envoyé")

    # Sauvegarder l'état
    save_state(state, STATE_FILE)
    print(f"\n{STATE_FILE} mis à jour")


if __name__ == "__main__":
    main()
