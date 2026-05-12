---
id: 325
status: done
who: Claude
due_date: 
position: 4
created_at: 2026-05-10T09:26:03
updated_at: 2026-05-10T13:05:28
---

# FAMILLE / synchro

Vérification et correction des incohérences dans les liens familiaux.

---

## Résolution

### Modifications
- **src/jeff/services/famille.py** — `check_family_consistency()` vérifie la bidirectionnalité de tous les liens : pere↔enfants, mere↔enfants, conjoint↔conjoint, freres_soeurs↔freres_soeurs. `apply_fix()` corrige une incohérence.
- **src/jeff/cli.py** — `jeff famille --check` : affiche les incohérences et propose de corriger (f=fix, s=skip, q=quit)

### Usage
```sh
jeff famille --check
```
```
3 inconsistencies found

  [1/3] Jean a conjoint=marie mais Marie a conjoint=
    fix: marie → conjoint=jean
    > f
    ✓ Marie: conjoint=jean
```

### Garde-fous
- 90 tests passent
