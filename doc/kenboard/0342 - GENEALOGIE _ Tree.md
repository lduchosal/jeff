---
id: 342
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-10T19:10:38
updated_at: 2026-05-10T19:20:03
---

# GENEALOGIE / Tree

Améliorer l'affichage de l'arbre généalogique Graphviz.

---

## Résolution

### Améliorations
- **splines=polyline** au lieu d'ortho — routing plus propre, moins de chevauchements
- **Couples** connectés via un point invisible avec edges épais (#64748b)
- **Same rank** forcé pour les conjoints
- **Couleurs** : bleu (#dbeafe) homme, rose (#fce7f3) femme, gris neutre
- **Rounded boxes** avec bordure colorée
- **Liens cliquables** (href vers les fiches contacts)

### Garde-fous
- 96 tests passent
