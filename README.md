# Monitor Résultats U11 — District du Var

Surveillance automatique des pages de résultats de football U11 du District du Var (FFF). Le script détecte les changements sur les pages web et envoie une notification par email avec le détail des modifications.

## Fonctionnement

1. **Scan automatique** : GitHub Actions exécute le script toutes les heures
2. **Détection des changements** : Comparaison du contenu textuel via hash SHA-256
3. **Notification par email** : En cas de changement, un mail est envoyé avec :
   - Le diff détaillé (lignes ajoutées/supprimées)
   - Les scores avant/après (extraction des tableaux HTML)
   - La liste des URLs modifiées
4. **Archivage** : Chaque modification est sauvegardée dans le dossier `archives/`

## Configuration des secrets GitHub

Dans **Settings > Secrets and variables > Actions**, ajoutez :

| Secret | Description | Obligatoire |
|--------|-------------|-------------|
| `SMTP_USER` | Adresse Gmail pour l'envoi | Oui |
| `SMTP_PASSWORD` | Mot de passe d'application Gmail | Oui |
| `NOTIFY_EMAIL` | Adresse de réception (si différente de SMTP_USER) | Non |

### Obtenir un mot de passe d'application Gmail

1. Activez la validation en 2 étapes sur votre compte Google
2. Allez sur https://myaccount.google.com/apppasswords
3. Créez un mot de passe pour "Mail" / "Autre"
4. Utilisez ce mot de passe (16 caractères) comme `SMTP_PASSWORD`

## Gestion des URLs

Les URLs à surveiller sont listées dans le fichier `urls.txt` :

```
# Ceci est un commentaire (ignoré)
https://example.com/page1
https://example.com/page2

# Les lignes vides sont ignorées
https://example.com/page3
```

Pour ajouter/supprimer des URLs :
1. Éditez le fichier `urls.txt`
2. Ajoutez une URL par ligne
3. Utilisez `#` pour les commentaires
4. Commitez et pushez vos modifications

## Structure des fichiers

```
foot/
├── monitor.py          # Script principal v2
├── urls.txt            # Liste des URLs à surveiller
├── state.json          # État actuel (hash + contenu + scores)
├── archives/           # Snapshots horodatés des changements
├── README.md
└── .github/
    └── workflows/
        └── monitor.yml # Configuration GitHub Actions
```

## Lancement manuel

Pour exécuter le workflow manuellement :
1. Allez dans l'onglet **Actions** du repo
2. Sélectionnez **Web Monitor**
3. Cliquez sur **Run workflow**

## Format de state.json

```json
{
  "https://...": {
    "hash": "sha256...",
    "text": "contenu textuel complet",
    "scores": "tableaux extraits",
    "last_check": "2025-01-15T10:30:00"
  }
}
```

Le script est rétrocompatible avec l'ancien format (hash simple).
