---
id: 300
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-09T20:35:51
updated_at: 2026-05-09T22:09:48
---

# AGENT / CLI jeff triage interactive

Créer une commande jeff triage interactive.

---

## Résolution

### Modifications
- **src/jeff/triage.py** — module avec load_contact, save_triage, needs_triage, format_summary
- **src/jeff/cli.py** — commande `jeff triage` qui affiche chaque contact non trié et prompt pour status/relation/priorité

### Usage
```
jeff triage        # contacts non triés uniquement
jeff triage --all  # tous les contacts
```

Commandes : a=actif r=archivé s=skip q=quit
Exemple : `a a h` = actif, ami, haute priorité

### Comportements obtenus
- Affiche nom, tags, note, adresse, email, téléphone
- Sauvegarde immédiate dans le frontmatter YAML
- Reprend là où on s'est arrêté (skip les déjà triés)
- 50 tests passent, refurb/flake8/mypy clean
