---
id: 313
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-10T08:02:25
updated_at: 2026-05-10T08:54:44
---

# HTML / Assets

Télécharger les fonts Google et les servir localement.

---

## Résolution

### Modifications
- **src/jeff/static/fonts.css** — @font-face pour Inter (400/500/600) et JetBrains Mono (400/500)
- **src/jeff/static/fonts/** — 4 fichiers woff2 (inter-latin, inter-latin-ext, jetbrains-mono-latin, jetbrains-mono-latin-ext)
- **src/jeff/templates/** — liens Google Fonts supprimés, remplacés par fonts.css local
- **src/jeff/services/publish.py** — copie fonts.css et fonts/ dans le output
- **.gitignore** — exception pour src/jeff/static/

### Comportements obtenus
- Aucune requête externe (Google Fonts) dans le CRM publié
- Pas de leak d'adresse IP vers Google
- Fonts servies localement en woff2
