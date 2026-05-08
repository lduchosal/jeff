---
id: 278
status: todo
who: Claude
due_date: 
position: 1
created_at: 2026-05-08T22:45:48
updated_at: 2026-05-08T22:45:48
---

# SYNC / Transform vCard to Markdown

Parser les vCards avec vobject, extraire les champs vers YAML frontmatter (schema complet : uid, name, emails, phones, addresses, positions, tags, photo, etc.). Generer un fichier .md par contact dans content/contacts/. Gerer les photos base64 (extraction en fichier). Deduplication par UID vCard. Ecrire le lien CRM en retour dans Baikal (URL + X-ABLabel:Profil CRM).
