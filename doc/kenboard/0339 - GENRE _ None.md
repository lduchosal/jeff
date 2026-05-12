---
id: 339
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-10T18:49:09
updated_at: 2026-05-10T19:04:46
---

# GENRE / None

Ajouter N=none comme option de genre pour les entreprises.

---

## Résolution
- **services/genre.py** — ajout `n: none` dans GENRE_MAP
- **cli.py** — aide mise à jour : H=homme F=femme N=none

### Garde-fous
- 90 tests passent
