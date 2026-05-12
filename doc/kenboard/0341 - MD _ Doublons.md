---
id: 341
status: review
who: Claude
due_date: 
position: 4
created_at: 2026-05-10T19:09:48
updated_at: 2026-05-10T19:22:25
---

# MD / Doublons

Détecter et nettoyer les doublons de fichiers .md par UID.

---

## Résolution

### Modifications
- **src/jeff/services/duplicates.py** — `find_duplicates()` cherche les fichiers .md avec le même UID, trie par date de modification, recommande le plus récent. `remove_duplicate()` supprime un fichier.
- **src/jeff/cli.py** — commande `jeff check` : affiche les doublons, propose de garder le plus récent et supprimer les autres (f=fix, s=skip, q=quit, default=fix).
- **tests/unit/test_duplicates.py** — 4 tests : pas de doublons, 2 doublons, 3 doublons, suppression.

### Usage
```sh
jeff check
```
```
1 duplicate UID(s) found

── [1/1] UID: urn:uuid:xxx ──
  Keep: Jean Dupont (jean-dupont.md)
  Delete: Jean Dupond (jean-dupond.md)

  > f
    ✗ deleted jean-dupond.md
```

### Garde-fous
- 100 tests passent
- Default = fix (garder le plus récent)
