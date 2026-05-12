---
id: 323
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-10T09:13:40
updated_at: 2026-05-10T09:17:43
---

# CRON / Writing back gender

Le gender writeback prend trop de temps à chaque cron.

---

## Résolution

### Cause
`_writeback_gender` parcourt TOUS les .md, fetch le vCard courant et fait un PUT pour chaque contact avec un genre — très lent.

### Modification
- **src/jeff/services/sync.py** — `writeback_gender` est un paramètre `False` par défaut
- **src/jeff/cli.py** — `jeff sync --writeback-gender` pour activer explicitement
- `jeff cron` ne fait plus le gender writeback

### Usage
```sh
jeff cron                      # rapide, pas de gender writeback
jeff sync --writeback-gender   # après un jeff genre, push vers CardDAV
```

### Garde-fous
- 90 tests passent
