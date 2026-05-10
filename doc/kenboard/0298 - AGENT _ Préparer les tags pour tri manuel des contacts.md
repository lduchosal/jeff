---
id: 298
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-09T20:25:51
updated_at: 2026-05-09T22:09:46
---

# AGENT / Préparer les tags pour tri manuel des contacts

## Contexte

Ajouter des champs de tri dans le frontmatter YAML pour trier les contacts manuellement.

---

## Résolution

### Modifications
- **src/jeff/transform.py** — `render_frontmatter` émet 4 champs de triage (status, relation, frequence, priorite). `contact_to_markdown` préserve les valeurs éditées à la main lors d'un re-sync.
- **src/jeff/publish.py** — `_load_contacts` filtre les contacts `status: archivé` et trie par priorité (haute > moyenne > basse) puis par nom.
- **153 fichiers .md** — mis à jour avec les 4 champs vides prêts à remplir.

### Champs ajoutés
- **status** : actif / archivé (vide = à trier)
- **relation** : ami / collegue / famille / connaissance
- **frequence** : hebdo / mensuel / trimestriel / annuel
- **priorite** : haute / moyenne / basse

### Comportements obtenus
- `jeff sync` préserve les valeurs de triage éditées à la main
- `jeff publish` exclut les contacts archivés et trie par priorité
- 50 tests passent

### Garde-fous
- pytest: 50 passed
- jeff publish: 153 contacts publiés
