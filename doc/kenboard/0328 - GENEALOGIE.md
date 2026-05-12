---
id: 328
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-10T12:14:18
updated_at: 2026-05-10T19:10:48
---

# GENEALOGIE

Page généalogie avec arbre familial en CSS pur.

---

## Résolution

### Architecture
- **src/jeff/services/genealogy.py** — `build_family_trees()` construit l'arbre depuis les liens famille. Trouve les racines (ancêtres sans parents), descend récursivement. Déduplique les couples. `tree_to_html()` génère du HTML imbriqué `<ul>/<li>`.
- **src/jeff/templates/genealogie.html** — page avec les arbres rendus
- **doc/ui/contact.css** — arbre CSS pur : flexbox, lignes de connexion via `::before/::after`, cartes colorées (bleu/rose)

### Fonctionnalités
- Couples affichés côte à côte avec `+`
- Lignes verticales/horizontales entre générations
- Cartes cliquables vers la fiche contact
- ♂️/♀️ emojis
- Lien depuis le dashboard

### Exemple de rendu
```
        Jacques ♂️ + Anne ♀️
              │
        Jean ♂️ + Marie ♀️
          ┌───┴───┐
       Luc ♂️  Léa ♀️
```

### Garde-fous
- 90 tests passent
- Pas de JS, pas de CDN
