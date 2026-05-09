---
id: 295
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-09T14:19:49
updated_at: 2026-05-09T20:25:50
---

# BUG / jeff publish crashes on YAML frontmatter parse

## Error

`jeff publish` crashes with `yaml.scanner.ScannerError` when a YAML value contains `---`.

## Action

Add a unit test then fix `_parse_frontmatter`.

---

## Résolution

### Modifications
- **src/jeff/publish.py** — remplacé `text.split("---", 2)` par une recherche ligne par ligne du délimiteur `---` de fermeture
- **tests/unit/test_publish.py** — ajout du test `test_body_with_dashes` avec un frontmatter contenant `---` dans une valeur YAML et un `---` horizontal rule dans le body

### Comportements obtenus
- `_parse_frontmatter` ne crashe plus quand une valeur YAML contient `---`
- Le body après le frontmatter (y compris les horizontal rules) est ignoré

### Garde-fous
- 49 tests passent
- Le test de régression reproduit exactement le ScannerError décrit
