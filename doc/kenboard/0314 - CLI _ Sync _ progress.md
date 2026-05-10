---
id: 314
status: review
who: Claude
due_date: 
position: 1
created_at: 2026-05-10T08:04:36
updated_at: 2026-05-10T08:09:06
---

# CLI / Sync / progress

Ajouter des infos de progress pendant le jeff sync.

---

## Résolution

### Modifications
- **src/jeff/services/sync.py** — callback ProgressFn passé à run_sync, _writeback_urls, _writeback_gender. Messages de progress : discovering, fetching, transform [i/n], URL [i/n], gender [i/n]
- **src/jeff/cli.py** — passe click.echo comme callback progress

### Comportements obtenus
- Le sync affiche chaque étape en temps réel
- Compteurs [i/n] sur les opérations longues (transform, URL writeback, gender writeback)
- Le service reste découplé de click (callback générique)
