---
id: 319
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-10T08:21:27
updated_at: 2026-05-10T08:54:32
---

# HTML /  WhatsApp / broken chars

Les emojis sont cassés dans le lien WhatsApp.

---

## Résolution

### Cause racine
La redirection wa.me → api.whatsapp.com corrompt les emojis percent-encodés en UTF-8 (%F0%9F → %EF%BF%BD).

### Modifications
- **src/jeff/services/publish.py** — filtre `whatsapp_encode` avec `urllib.parse.quote` (encodage UTF-8 correct)
- **src/jeff/templates/contact.html** — liens WhatsApp utilisent `api.whatsapp.com/send` directement au lieu de `wa.me` pour éviter la redirection qui corrompt

### Garde-fous
- 87 tests passent
