---
id: 318
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-10T08:19:02
updated_at: 2026-05-10T08:54:31
---

# CLI / jeff cron

Commande jeff cron pour le crontab quotidien.

---

## Résolution

### Modifications
- **src/jeff/services/birthday.py** — `find_birthdays(content_dir)` détecte les anniversaires du jour, `record_birthday_exchange(contact)` écrit l'échange dans le frontmatter (idempotent)
- **src/jeff/cli.py** — commande `jeff cron` qui enchaîne sync → birthdays → publish

### Usage
```sh
jeff cron          # sync + anniversaires + publish
jeff cron --full   # force full sync
```

Crontab :
```
0 7 * * * cd /path/to/project && jeff cron
```

### Output
```
── Sync ──
Discovering addressbooks...
Addressbook: Contacts
Already up to date.

── Birthdays ──
  🎂 Jean Dupont (recorded)

── Publish ──
Published 204 contact(s) to public/
```

### Garde-fous
- 87 tests passent
- Birthday exchange idempotent (pas de doublon si exécuté 2x le même jour)
