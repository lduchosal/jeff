---
id: 305
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-09T22:39:14
updated_at: 2026-05-10T00:20:24
---

# CODE / Refactoring

Attention aux classes trop grosses, cli doit être découpée. Pattern cli / service / domaine.

---

## Résolution

### Architecture
```
cli.py (398 lignes)        ← commandes click, UI uniquement
services/sync.py (154)     ← orchestration sync, writeback URL/genre
services/famille.py (75)   ← liens réciproques, merge listes, affichage
triage.py (96)             ← load/save/format contacts (déjà séparé)
transform.py (395)         ← parsing vCard, rendu frontmatter (domaine)
carddav.py (294)           ← client CardDAV (domaine)
publish.py (174)           ← build site statique (domaine)
```

### Modifications
- **src/jeff/services/sync.py** — extrait `run_sync()`, `_writeback_urls()`, `_writeback_gender()` depuis cli.py
- **src/jeff/services/famille.py** — extrait `reciprocal_updates()`, `merge_list_field()`, `format_existing_links()`
- **src/jeff/cli.py** — réduit de 570 à 398 lignes, ne contient plus que les commandes click
- **tests/unit/test_cli.py** — patches mis à jour vers `jeff.services.sync`

### Garde-fous
- 56 tests passent
- flake8/mypy/refurb clean
