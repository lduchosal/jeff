---
id: 311
status: done
who: Claude
due_date: 
position: 2
created_at: 2026-05-10T00:15:44
updated_at: 2026-05-10T00:20:22
---

# CI / coverage

Codecov nécessite un token pour uploader les rapports de coverage.

---

## Résolution

### Modifications
- Secret `CODECOV_TOKEN` ajouté manuellement dans GitHub Settings → Secrets
- Le workflow `python-package.yml` utilise déjà `codecov/codecov-action@v5` avec le token
- `test-ci` génère déjà `coverage.xml` via `--cov-report=xml`

### Aucune modification de code nécessaire
La configuration était correcte, il manquait juste le secret GitHub.
