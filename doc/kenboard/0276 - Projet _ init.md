---
id: 276
status: done
who: Claude
due_date: 
position: 7
created_at: 2026-05-08T22:12:17
updated_at: 2026-05-08T23:08:36
---

# Projet / init

copy pyprojet from kenboard and publish scripts
remove dependencies
make it clean as a new projet
keep all quality gates

---

## Resolution

Adapte depuis https://github.com/lduchosal/kenboard

### Fichiers crees

- `pyproject.toml` — pdm, zero deps, quality gates identiques a kenboard
- `publish.sh` — workflow quality (15 steps) + publish PyPI (22 steps)
- `src/jeff/__init__.py` — v0.1.0
- `tests/unit/test_version.py` — test minimal
- `.gitignore` — .ken, .sync-state.json, __pycache__, dist/, etc.

### Quality gates conservees

black, isort, docformatter, mypy, flake8, interrogate, refurb, ruff, vulture, pytest+coverage (fail_under=75)

### Retire vs kenboard

- Dependencies : zero (flask, mysql, auth, etc. retires)
- Scripts JS : retires (js-install, js-lint, js-typecheck, js-test, js-build)
- Sonarcloud : retire
- E2E playwright : retire
- Screenshots : retire
