---
id: 332
status: done
who: Claude
due_date: 
position: 6
created_at: 2026-05-10T13:41:50
updated_at: 2026-05-10T19:04:53
---

# FAMILLE / argument

Ajouter un argument à jeff famille pour filtrer par nom.

---

## Résolution

- **src/jeff/cli.py** — argument optionnel `[QUERY]` : filtre les contacts famille par nom ou slug (case-insensitive). Fonctionne aussi avec `--check`.

### Usage
```sh
jeff famille edmond        # éditer les liens d'edmond
jeff famille dupont         # tous les Dupont
jeff famille --check dupont # vérifier la cohérence des Dupont
jeff famille               # tous les contacts famille
```

### Garde-fous
- 90 tests passent
