---
id: 301
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-09T21:18:15
updated_at: 2026-05-09T22:09:48
---

# QUALITY / SonarCloud issues

fix issues
https://sonarcloud.io/project/overview?id=lduchosal_jeff

---

## Résolution

### Issues corrigées (8/23)
- **S6397** transform.py — regex `[ñ]` simplifié en `ñ`
- **S1192** carddav.py — constantes `_D_RESPONSE` et `_D_HREF` extraites (3 duplications chacune)
- **S1481** test_carddav.py — `new_state` inutilisé remplacé par `_`
- **S7682** publish.sh — `return 0` ajouté aux 4 fonctions
- **S7679** publish.sh — params positionnels assignés à des variables locales

### Issues ignorées (volontairement)
- **S2068** (5x) — hard-coded credentials dans les tests : normal pour des tests unitaires
- **S8565** — lock file manquant : faux positif, pdm.lock existe
- **S5725** (3x) — resource integrity sur les templates HTML : pas pertinent pour des templates internes
- **S1481** publish.py — `bundled` déjà supprimé dans un commit précédent
- **S3776** (2x) — complexité cognitive de `sync` (45) et `parse_vcard` (82) : fonctions linéaires, refactor lourd sans valeur ajoutée

### Garde-fous
- 51 tests passent
- flake8/mypy/refurb clean
