---
id: 345
status: review
who: Claude
due_date: 
position: 4
created_at: 2026-05-11T20:57:53
updated_at: 2026-05-11T21:21:39
---

# CI / FAIL Required test coverage of 75.0% not reached. Total coverage: 64.25%

Coverage 64% → 76% (seuil 75%).

---

## Résolution

### Tests ajoutés
- **test_birthday.py** (7 tests) — find_birthdays, record_birthday_exchange, idempotence
- **test_birthday_mail.py** (4 tests) — build_birthday_html, contacts sans phone, avec signe
- **test_export.py** (4 tests) — export squirrelmail actif, skip archivé, pipe dans notes
- **test_genealogy.py** (5 tests) — arbre simple, couple, parent-enfant, 3 générations
- **test_urlback.py** (+5 tests) — inject_related, skip si identique, remplacement, multiple
- **test_cli.py** (+6 tests) — export, check, cron offline, delete mark/skip, birthday-mail

### Résultat
- 133 tests passent
- Coverage : 76.12% (seuil 75%)
