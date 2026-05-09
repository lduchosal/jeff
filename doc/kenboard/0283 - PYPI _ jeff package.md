---
id: 283
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-08T23:24:36
updated_at: 2026-05-09T20:25:52
---

# PYPI / jeff package

Create a PyPI package jeff-contacts

---

## Resolution

### pyproject.toml

Nom du package change de "jeff" a "jeff-contacts" pour eviter les conflits sur PyPI. Le CLI reste `jeff` (entry point inchange).

### README.md

Install mis a jour : `pip install jeff-contacts`

### Publication

Le workflow publish.sh existant gere deja : pdm build → pdm publish → tag git. Le nom du package est lu depuis pyproject.toml.
