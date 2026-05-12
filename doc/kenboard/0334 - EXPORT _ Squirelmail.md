---
id: 334
status: review
who: Claude
due_date: 
position: 0
created_at: 2026-05-10T18:02:47
updated_at: 2026-05-10T19:38:12
---

# EXPORT / Squirelmail

Exporter les contacts actifs au format SquirrelMail.

---

## Résolution

### Format
SquirrelMail .abook : `nickname|firstname|lastname|email|info` (pipe-delimited, un contact par ligne).

### Modifications
- **src/jeff/services/export.py** — `export_squirrelmail(content_dir, output_path)` : exporte les contacts `status=actif` avec email
- **src/jeff/cli.py** — commande `jeff export` avec `--format squirrelmail` (défaut) et `-o contacts.abook`

### Usage
```sh
jeff export
jeff export -o /path/to/squirrelmail.abook
```

### Garde-fous
- 100 tests passent
- Seuls les contacts actifs avec email sont exportés
- Les pipes dans les notes sont remplacés par /
