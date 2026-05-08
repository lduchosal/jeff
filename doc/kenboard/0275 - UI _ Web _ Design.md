---
id: 275
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-08T21:26:05
updated_at: 2026-05-08T21:36:37
---

# UI / Web / Design

Proposer un joli design clair et net pour l'affichage d'un detail de contact avec le suivi CRM

Recherche ce qui existe, ne pas reinventer, pure css

---

## Resolution

### Inspirations

- **Twenty CRM** : palette neutre 12 gris, Inter, composants data-forward, whitespace genereux
- **Linear** : monochrome + 1 accent, uppercase micro-labels pour les sections, bordures 1px subtiles
- **Apple HIG** : backgrounds stratifies (#FFF / #F2F2F7 / #E5E5EA), separateurs fins

### Design

Style Apple/Linear : fond blanc, palette neutre warm-gray, un seul bleu accent (#3B82F6). Sections avec titres uppercase discrets. Key-value pairs en CSS Grid 2 colonnes. Timeline verticale pour les interactions. Tags en pills colores. Score avec dot semantique (vert/orange/rouge). Sidebar pour positions et contacts lies.

### Fichiers crees

- `static/css/contact.css` — design system complet (variables, layout, composants)
- `layouts/contacts/single.html` — template Hugo avec header, details, CRM data, timeline, notes, sidebar

### Specs

- Pure CSS (variables, Grid, Flexbox, zero JS)
- Responsive : mobile-first, sidebar collapse < 768px, field stack < 480px
- Font : Inter, 0.9375rem base
- Palette : 4 backgrounds, 3 textes, 1 accent, 3 semantiques
- Compatible Hugo : frontmatter YAML standard

### Garde-fous

- Zero dependance externe (pas de Tailwind, pas de framework)
- Accessible : labels semantiques, alt text, focus styles via browser defaults
- Pas de shadow sur le contenu principal (clean, pas "card soup")
