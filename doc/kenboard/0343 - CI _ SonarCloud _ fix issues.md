---
id: 343
status: review
who: Claude
due_date: 
position: 4
created_at: 2026-05-10T21:01:52
updated_at: 2026-05-10T21:06:38
---

# CI / SonarCloud / fix issues

Corriger les issues SonarCloud.

---

## Résolution

### Issues corrigées (5/17)
- **S5361** transform.py — `re.sub("ñ")` → `str.replace("ñ")`
- **S1481** transform.py — `sign_emoji` inutilisé → `_`
- **S1481** publish.py — `emoji` inutilisé → `_`
- **S1172** sync.py — paramètre `content_dir` inutilisé supprimé de `_writeback_urls`
- **S1192** cli.py — constante `_NO_CONTACTS` extraite (5 duplications)

### Issues restantes (12/17)
Toutes S3776 (complexité cognitive) — fonctions longues mais linéaires. Refactoring possible mais cosmétique.

### Garde-fous
- 100 tests passent
