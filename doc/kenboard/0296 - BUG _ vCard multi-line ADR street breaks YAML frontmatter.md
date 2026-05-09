---
id: 296
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-09T14:40:53
updated_at: 2026-05-09T20:25:51
---

# BUG / vCard multi-line ADR street breaks YAML frontmatter

## Erreur

`jeff publish` crashe avec `yaml.scanner.ScannerError` sur un contact dont la rue vCard ADR contient un saut de ligne.

---

## Résolution

### Modifications
- **src/jeff/transform.py** — `_yaml_value` collapse les newlines en `, ` avant d'émettre la valeur YAML (ex: `Centre Malley Lumières\nChemin du Viaduc 1` → `Centre Malley Lumières, Chemin du Viaduc 1`)
- **tests/unit/test_transform.py** — ajout fixture `VCARD_MULTILINE_ADR` et test `test_multiline_address` qui vérifie que le frontmatter généré est du YAML valide

### Comportements obtenus
- Les adresses multi-lignes vCard sont correctement jointes et produisent du YAML valide
- `jeff publish` ne crashe plus sur ces contacts

### Garde-fous
- 50 tests passent
