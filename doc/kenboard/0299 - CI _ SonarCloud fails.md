---
id: 299
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-09T20:34:34
updated_at: 2026-05-09T22:09:47
---

# CI / SonarCloud fails

https://github.com/lduchosal/jeff/actions/runs/25608666782/job/75174954536

SonarCloud Automatic Analysis était activée en même temps que le scan CI.

---

## Résolution

### Modifications
- Désactivation de l'Automatic Analysis dans SonarCloud (Administration → Analysis Method) — action manuelle faite par l'utilisateur.
- Aucune modification de code nécessaire.

### Comportements obtenus
- Le scan CI SonarCloud ne conflit plus avec l'Automatic Analysis

### Garde-fous
- Re-run du workflow CI pour confirmer
