---
id: 312
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-10T07:58:40
updated_at: 2026-05-10T08:54:35
---

# VCARD / Notes / formattage

Les notes vCard perdent leur formatage (retours à la ligne) dans le publish.

---

## Résolution

### Cause racine
`_yaml_value` collapsait tous les newlines en `, ` (fix pour les adresses #296), y compris les notes.

### Modifications
- **src/jeff/domain/transform.py** — séparé le traitement :
  - Notes multi-lignes → YAML block scalar `|` (préserve les newlines)
  - Adresses multi-lignes → collapsées à la source dans `parse_vcard` via `_collapse_newlines()`
  - `_yaml_value` ne collapse plus les newlines
- **src/jeff/templates/contact.html** — simplifié : `<div class="prose prose--pre">{{ contact.note }}</div>`
- **doc/ui/contact.css** — ajout `white-space: pre-line` sur `.prose--pre`
- **tests** — `test_multiline_note_preserved` vérifie que les newlines sont préservés dans le YAML

### Garde-fous
- 87 tests passent
- Le test adresse multi-ligne (#296) passe toujours
