---
id: 329
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-10T12:34:21
updated_at: 2026-05-10T13:05:30
---

# BUG / jeff sync crash sans connexion internet

jeff sync crashe avec un traceback sans connexion internet.

---

## Résolution

### Modifications
- **src/jeff/services/sync.py** — catch `requests.ConnectionError` lors du discover, retourne un `SyncResult` avec `error='no connection'` et message propre
- **src/jeff/cli.py** — `jeff sync` exit code 1 sur erreur réseau. `jeff cron` continue avec birthdays + publish (données locales toujours valides)

### Comportement
```
jeff sync
Discovering addressbooks...
Error: no internet connection. Sync skipped.
```

`jeff cron` sans connexion :
```
── Sync ──
Discovering addressbooks...
Error: no internet connection. Sync skipped.

── Birthdays ──
  No birthdays today.

── Publish ──
Published 204 contact(s)
```
