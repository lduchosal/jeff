---
id: 291
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-09T08:07:12
updated_at: 2026-05-09T20:25:53
---

# PYPI / Publish

run publish.sh and fix issues

---

## Résolution

### Modifications
- **.flake8** — ajout config flake8 réutilisée de kenboard (max-line-length=125, ignores DCO)
- **vulture_whitelist.py** — fichier créé (manquant, requis par vulture)
- **src/jeff/urlback.py** — supprimé import `re` inutilisé (F401), renommé variable `l` -> `line` (E741), utilisé `extend` (FURB113)
- **src/jeff/transform.py** — corrigé import E402 (déplacé au top-level), utilisé `extend` (FURB113)
- **src/jeff/publish.py** — corrigé imports E402, supprimé variable inutilisée `bundled` (F841)
- **src/jeff/carddav.py** — ajout docstring __init__ (D107), noqa FURB184 pour annotation mypy
- **tests/** — auto-formatés par isort/ruff/black (imports inutilisés, line length)

### Comportements obtenus
- publish.sh passe les 16 quality gates (clean → tests) sans erreur
- Étape 20 (pdm publish) échoue car pas de credentials PyPI configurés (non un bug code)

### Garde-fous
- flake8: 0 erreur
- mypy: 0 erreur (8 fichiers)
- refurb: 0 erreur
- ruff: 0 erreur
- vulture: 0 erreur
- interrogate: 100% docstring coverage
- pytest: 48 passed
