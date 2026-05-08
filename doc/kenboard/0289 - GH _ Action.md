---
id: 289
status: review
who: Claude
due_date: 
position: 0
created_at: 2026-05-08T23:50:23
updated_at: 2026-05-09T00:03:43
---

# GH / Action

Copie les gh action de kenboard et fait de meme pour jeff

---

## Resolution

### .github/workflows/python-package.yml

CI sur push/PR main :
- Matrix Python 3.11, 3.12, 3.13 (ubuntu-latest)
- pdm install + pdm install -G dev
- pdm build
- pdm run test-ci (pytest + coverage)
- Upload coverage Codecov
- Upload coverage.xml artifact pour SonarCloud
- Job SonarCloud dependant du build

Retire vs kenboard : pas de MySQL, pas de JS, pas de Windows, pas de e2e.

### .github/workflows/publish.yml

Publication PyPI :
- Schedule hebdo (lundi 9h UTC) ou workflow_dispatch manuel
- pdm + pdm-bump
- publish.sh --ci --patch/minor/major
- Secret PYPI_TOKEN
