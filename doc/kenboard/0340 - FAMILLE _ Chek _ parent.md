---
id: 340
status: done
who: Claude
due_date: 
position: 6
created_at: 2026-05-10T19:04:35
updated_at: 2026-05-10T19:20:04
---

# FAMILLE / Chek / parent

Vérifier que parent ↔ enfants est bidirectionnel dans jeff famille --check.

---

## Résolution

La fonctionnalité était déjà implémentée (#325). Ajout de 6 tests unitaires avec des vrais fichiers .md pour couvrir tous les cas :

### Tests ajoutés
1. **test_no_issues_when_consistent** — pere=jacques ↔ enfants=[jean] → 0 issue
2. **test_parent_missing_child** — jean a pere=jacques mais jacques n'a pas jean dans enfants → détecté
3. **test_child_missing_parent** — jacques a enfants=[jean] mais jean n'a pas pere=jacques → détecté
4. **test_conjoint_not_reciprocal** — jean a conjoint=marie mais marie n'a pas conjoint=jean → détecté
5. **test_sibling_not_reciprocal** — jean a freres_soeurs=[paul] mais paul n'a pas jean → détecté
6. **test_mere_missing_child** — jean a mere=anne mais anne n'a pas jean dans enfants → détecté

### Garde-fous
- 96 tests passent
