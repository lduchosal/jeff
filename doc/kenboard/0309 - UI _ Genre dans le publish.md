---
id: 309
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-10T00:08:34
updated_at: 2026-05-10T00:20:21
---

# UI / Genre dans le publish

Afficher le genre dans le publish + rappel des fonctionnalités genre déjà implémentées.

---

## Résolution

### Modifications
- **src/jeff/templates/contact.html** — badge genre (Homme bleu / Femme rose) dans les badges triage du header
- **src/jeff/templates/index.html** — dot coloré (bleu/rose) à côté du nom dans les cartes du dashboard
- **doc/ui/contact.css** — styles stat-badge--homme/femme + genre-icon

### Fonctionnalités genre (déjà implémentées)
- `jeff genre` — commande CLI batch pour assigner H/F rapidement
- `jeff triage` — 4ème param pour le genre : `a f h H`
- `jeff sync` — lit X-GENDER du vCard et écrit X-GENDER:M/F vers CardDAV
- services/genre.py — service dédié
- Préservé au re-sync via _triage_keys

### Garde-fous
- 86 tests passent
- jeff publish : 153 contacts
