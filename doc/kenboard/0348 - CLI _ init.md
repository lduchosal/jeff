---
id: 348
status: review
who: Claude
due_date: 
position: 4
created_at: 2026-05-12T18:25:59
updated_at: 2026-05-12T18:32:42
---

# CLI / init

jeff init crée le fichier .jeff pré-rempli.

---

## Résolution
- **src/jeff/cli.py** — commande `jeff init` : crée `.jeff` avec template pré-rempli (CardDAV URL/user/pass, publish_url, mail_to), mode 600, affiche les next steps.
- L'init skip la validation config pour tourner sans .jeff existant.

### Garde-fous
- 133 tests passent
