---
id: 333
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-10T13:45:32
updated_at: 2026-05-10T19:10:02
---

# CLI / Delete / séparer du status

Séparer delete du status dans le frontmatter.

---

## Résolution

### Nouveau champ `delete`
- **vide** : pas encore décidé → `jeff delete` le propose
- **false** : garder (actif, ou skippé dans jeff delete)
- **true** : à supprimer → `jeff sync` le supprime du CardDAV

### Modifications
- **transform.py** — `delete` dans les scalars et `_triage_keys`
- **cli.py** :
  - `jeff triage` actif → `delete: false` auto
  - `jeff delete` → ne propose que `delete:` vide, skip = `delete: false`
  - `jeff famille <query>` → cherche dans TOUS les contacts (pas juste famille)
- **sync.py** — supprime `delete: true` au lieu de `status: supprimé`

### Garde-fous
- 90 tests passent
