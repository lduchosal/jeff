---
id: 294
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-09T13:26:25
updated_at: 2026-05-09T20:25:50
---

# CI / Recurrent build

copy kenboard recurrent action to build and publish

---

## Résolution

### Modifications
- **.github/workflows/publish.yml** — ajout de l'étape d'installation des dépendances (pdm install + pdm install -G dev) manquante avant l'exécution de publish.sh

### Comportements obtenus
- Le workflow publish.yml était déjà en place (cron hebdo lundi 9h UTC + dispatch manuel patch/minor/major)
- L'étape manquante d'installation des dépendances dev a été ajoutée, sans quoi les quality gates (mypy, flake8, ruff, etc.) échouaient en CI
- Le workflow utilise publish.sh --ci qui exécute toutes les quality gates puis publie sur PyPI

### Garde-fous
- Workflow aligné avec le pattern kenboard (install deps avant publish.sh)
- Credentials PyPI via secret PYPI_TOKEN
