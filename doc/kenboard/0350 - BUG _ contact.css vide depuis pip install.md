---
id: 350
status: review
who: Claude
due_date: 
position: 0
created_at: 2026-05-12T21:29:27
updated_at: 2026-05-12T21:30:49
---

# BUG / contact.css vide depuis pip install

contact.css vide quand installé depuis pip.

---

## Cause racine
`publish.py` cherchait `doc/ui/contact.css` qui n'existe que dans le repo git. En pip install, ce chemin n'existe pas → fallback écrit `/* no css found */`.

## Résolution
- **src/jeff/static/contact.css** — CSS bundlé dans le package
- **src/jeff/services/publish.py** — fallback : user CSS (doc/ui/) > bundled (static/) > empty

## Priorité de chargement
1. `doc/ui/contact.css` (mode dev, passé par cli.py)
2. `src/jeff/static/contact.css` (bundlé dans le pip package)
3. Placeholder vide (ne devrait plus arriver)

## Garde-fous
- 133 tests passent
