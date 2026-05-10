---
id: 304
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-09T22:19:31
updated_at: 2026-05-10T00:20:18
---

# AGENT / Liens familiaux dans les contacts

Liens familiaux dans les contacts avec CLI batch interactive.

---

## Résolution

### Champs ajoutés au frontmatter
- **genre** : homme / femme — utilisé pour les réciproques (enfant → pere ou mere)
- **pere, mere, conjoint** : slug du contact lié
- **freres_soeurs, enfants** : liste de slugs

### CLI
- `jeff triage` : 4ème param pour le genre : `a f h H` (actif, famille, haute, homme)
- `jeff famille` :
  - Affiche genre à côté des noms
  - Affiche les liens existants
  - Aide à chaque contact
  - `?texte` pour chercher
  - **Réciproques automatiques** avec genre : `1c` sur un homme → `pere=slug` sur l'enfant, sur une femme → `mere=slug`

### Préservation
Tous les champs (genre, famille) dans `_triage_keys` → jamais écrasés par `jeff sync`. Testé.

### Garde-fous
- 52 tests passent
