---
id: 306
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-09T23:10:33
updated_at: 2026-05-10T00:20:19
---

# SYNC / Remonter le genre dans CardDAV

Remonter le genre (homme/femme) dans le CardDAV via X-GENDER.

---

## Résolution

### Modifications
- **src/jeff/urlback.py** — `inject_gender(vcard_raw, genre)` : écrit `X-GENDER:M` ou `X-GENDER:F` dans le vCard. Skip si déjà présent, remplace si différent.
- **src/jeff/transform.py** — `parse_vcard` lit `X-GENDER` du vCard et le mappe vers `genre: homme/femme`
- **src/jeff/cli.py** — `jeff sync` écrit le genre dans CardDAV pour les contacts mis à jour qui ont un genre défini localement
- **tests/unit/test_urlback.py** — 4 tests : injection M/F, skip si identique, remplacement

### Flow bidirectionnel
- CardDAV → jeff : `X-GENDER:M` → `genre: homme` dans le frontmatter
- jeff → CardDAV : `genre: homme` → `X-GENDER:M` via PUT

### Garde-fous
- 56 tests passent
