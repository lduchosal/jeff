---
id: 302
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-09T22:08:26
updated_at: 2026-05-10T00:20:18
---

# UI / Dashboard contacts dans jeff publish

Améliorer jeff publish pour un dashboard de suivi des contacts actifs.

---

## Résolution

### Modifications
- **src/jeff/publish.py** — groupe les contacts par relation, calcule les stats (par relation et par priorité), passe les données groupées au template
- **src/jeff/templates/index.html** — dashboard avec badges stats, sections par relation (famille/ami/collegue/connaissance/autre), grille de cartes avec avatar, note tronquée, tags, dot de priorité
- **src/jeff/templates/contact.html** — badges triage (relation, priorité, fréquence) dans le header
- **doc/ui/contact.css** — styles dashboard : stat-badge, dashboard-grid, contact-card, priority-dot, tag--small

### Comportements obtenus
- Page index groupée par relation avec compteurs
- Cartes contacts avec note, tags (max 4 + compteur), dot de priorité coloré (rouge/jaune/vert)
- Page contact avec badges de triage
- 51 tests passent
