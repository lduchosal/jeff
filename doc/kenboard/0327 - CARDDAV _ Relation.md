---
id: 327
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-10T12:04:54
updated_at: 2026-05-10T19:20:06
---

# CARDDAV / Relation

Remonter les liaisons familiales dans le CardDAV via RELATED (RFC 6350).

---

## Résolution

### Analyse
- vCard 4.0 définit la propriété `RELATED` avec types : parent, spouse, child, sibling
- Baikal 0.10.1 (sabre/dav) supporte vCard 3.0 et 4.0 avec conversion automatique
- Référence par UID (`urn:uuid:...`) pour la stabilité

### Mapping
- `pere`/`mere` → `RELATED;TYPE=parent:urn:uuid:...`
- `conjoint` → `RELATED;TYPE=spouse:urn:uuid:...`
- `enfants` → `RELATED;TYPE=child:urn:uuid:...`
- `freres_soeurs` → `RELATED;TYPE=sibling:urn:uuid:...`

### Modifications
- **src/jeff/domain/urlback.py** — `inject_related(vcard_raw, relations)` : écrit les RELATED, skip si déjà à jour
- **src/jeff/domain/transform.py** — `parse_vcard` lit les RELATED existants
- **src/jeff/services/sync.py** — `_writeback_famille()` : résout slug→UID, fetch vCard, inject_related, PUT
- **src/jeff/cli.py** — `jeff sync --writeback-famille`

### Usage
```sh
jeff famille          # éditer les liens localement
jeff famille --check  # vérifier la cohérence
jeff sync --writeback-famille  # pousser vers CardDAV
```

### Garde-fous
- 90 tests passent
- Opération lente (fetch+PUT par contact) → flag explicite
