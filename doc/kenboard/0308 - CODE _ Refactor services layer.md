---
id: 308
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-09T23:58:30
updated_at: 2026-05-10T00:20:20
---

# CODE / Refactor services layer

Refactoring complet cli / service / domaine.

---

## Résolution

### Architecture
```
src/jeff/
  cli.py (398)           ← CLI thin layer (click commands)
  log.py (36)            ← infrastructure
  domain/                ← objets métier, logique pure
    carddav.py (294)     ← client CardDAV + dataclasses
    config.py (133)      ← configuration
    transform.py (395)   ← vCard → frontmatter
    urlback.py (79)      ← injection vCard (URL, gender)
  services/              ← orchestration métier
    sync.py (169)        ← sync CardDAV + writeback
    publish.py (175)     ← build site statique
    triage.py (96)       ← triage contacts
    famille.py (75)      ← liens familiaux
```

### Principe
- **domain/** : logique pure, pas de dépendance click, pas d'orchestration
- **services/** : orchestration métier, combine les objets domaine
- **cli.py** : thin layer, appelle les services, affiche les résultats

### Garde-fous
- 86 tests passent
- flake8/mypy/refurb clean
- Coverage 86%
