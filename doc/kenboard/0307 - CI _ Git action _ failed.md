---
id: 307
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-09T23:49:06
updated_at: 2026-05-10T00:20:20
---

# CI / Git action / failed

CI échoue : coverage 62%, seuil 75%.

---

## Résolution

### Modifications
- **tests/unit/test_cli.py** — ajout de 14 tests CliRunner pour triage, genre, famille, publish (skip, actif, archivé, quit, search, liens réciproques)
- **tests/unit/test_famille.py** — 14 tests pour le service famille (reciprocal_updates, merge_list_field, format_existing_links)
- **pyproject.toml** — suppression config coverage dupliquée

### Coverage
- Avant : 62% (cli.py 18%, services/famille 0%)
- Après : 86% (cli.py 90%, services/famille 96%)
- Seuil 75% atteint

### Garde-fous
- 86 tests passent
- Coverage CI : 86.02%
