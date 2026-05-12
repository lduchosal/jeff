---
id: 349
status: review
who: Claude
due_date: 
position: 5
created_at: 2026-05-12T18:26:40
updated_at: 2026-05-12T18:32:43
---

# CLI / help

jeff --help affiche une aide utile.

---

## Résolution
- **src/jeff/cli.py** — aide enrichie avec description, epilog, support -h. Toutes les commandes listées avec description courte. Epilog: "Run jeff COMMAND --help for details. Start with jeff init."

### Garde-fous
- 133 tests passent
