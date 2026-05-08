---
id: 287
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-08T23:42:34
updated_at: 2026-05-08T23:48:49
---

# LOG / Add logging

---

## Resolution

### Fichier : src/jeff/log.py

Module minimal : setup(verbose) configure le logger racine jeff, get_logger(name) retourne un sous-logger.
- Default : WARNING (silencieux)
- Verbose : DEBUG (tout sur stderr)
- Format : LEVEL jeff.module: message

### Logs ajoutes

- carddav : PROPFIND, multiget (N contacts), ctag changed/unchanged, PUT
- transform : per-contact (nom → slug.md)
- publish : load (N contacts), render (slug.html)
