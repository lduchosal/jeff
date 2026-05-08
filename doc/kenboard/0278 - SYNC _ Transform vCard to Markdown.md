---
id: 278
status: done
who: Claude
due_date: 
position: 2
created_at: 2026-05-08T22:45:48
updated_at: 2026-05-08T23:48:49
---

# SYNC / Transform vCard to Markdown

Parser les vCards avec vobject, extraire les champs vers YAML frontmatter. Generer un fichier .md par contact dans content/contacts/. Gerer les photos base64 (extraction en fichier). Deduplication par UID vCard.

---

## Resolution

### Fichier : src/jeff/transform.py

4 fonctions principales :

- **parse_vcard(raw)** → dict avec tous les champs : uid, name, slug, name_family/given, emails (list), phones (list), addresses (list), positions (list), tags, urls, birthday, note, rev, photo
- **render_frontmatter(data)** → string YAML frontmatter
- **extract_photo(data, slug, photo_dir)** → extrait base64 en fichier .jpg/.png
- **contact_to_markdown(contact, content_dir, photo_dir)** → pipeline complet, ecrit le .md

Helper : **slugify(text)** — gere accents francais, caracteres speciaux

### Mapping vCard → YAML

- EMAIL (repete) → emails[] + email (scalar, pref ou premier)
- TEL (repete) → phones[] + phone (scalar)
- ADR (repete) → addresses[] avec street/city/region/postal_code/country
- ORG + TITLE → positions[]
- CATEGORIES → tags[]
- URL → urls[]
- PHOTO base64 → fichier extrait dans photo_dir
- Champs absents = omis (pas de null)

### Tests : tests/unit/test_transform.py — 12 tests

- slugify : basic, accents, special chars, empty
- parse_vcard : full, minimal, multi-org
- render_frontmatter : scalars, lists, quoted phones
- contact_to_markdown : full pipeline, minimal

### Teste sur Baikal reel

3 contacts (Jeff, Claude, Luc) transformes avec succes.
