---
id: 330
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-10T12:50:23
updated_at: 2026-05-10T13:05:26
---

# SYNC / delete carddav contact

Les contacts marqués supprimé sont supprimés du CardDAV au sync.

---

## Résolution

### Modifications
- **src/jeff/domain/carddav.py** — nouvelle méthode `delete_contact(href, etag)` : DELETE avec If-Match
- **src/jeff/services/sync.py** — après le sync, parcourt les .md avec `status: supprimé`, supprime du CardDAV via DELETE, supprime le .md local, met à jour le state
- **src/jeff/cli.py** — affiche les contacts supprimés du CardDAV

### Flow complet
```sh
jeff delete        # marque les archivés comme supprimé (interactif + confirmation)
jeff sync          # supprime du CardDAV + supprime le .md local
```

### Garde-fous
- 90 tests passent
- DELETE avec If-Match (optimistic locking)
- .md supprimé seulement si le DELETE réussit
