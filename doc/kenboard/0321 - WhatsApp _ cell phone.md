---
id: 321
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-10T08:33:59
updated_at: 2026-05-10T09:10:38
---

# WhatsApp / cell phone

WhatsApp doit utiliser le cell en priorité, tous les téléphones doivent apparaître.

---

## Résolution

### Bug
`phone_cell` était calculé dans `parse_vcard` mais pas écrit dans le frontmatter YAML (manquait dans la liste `scalars`). Le template tombait sur `contact.phone` (home).

### Modifications
- **src/jeff/domain/transform.py** — ajout `phone_cell` dans les scalars du frontmatter
- **src/jeff/templates/contact.html** — itère sur `contact.phones` pour afficher tous les numéros avec leur type
- **tests** — 3 tests : priorité cell, présence dans frontmatter, fallback pref

### Garde-fous
- 90 tests passent
