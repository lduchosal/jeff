---
id: 331
status: done
who: Claude
due_date: 
position: 6
created_at: 2026-05-10T13:05:13
updated_at: 2026-05-10T19:20:04
---

# CLI / Delete / Carte complète

Afficher toutes les infos du contact dans jeff delete.

---

## Résolution

- **src/jeff/cli.py** — réutilise `format_summary` (nom, tags, note, adresse, email, téléphone, org) au lieu d'un résumé tronqué. Chaque contact s'affiche comme une fiche complète avant la question d/skip/q.

### Garde-fous
- 90 tests passent
