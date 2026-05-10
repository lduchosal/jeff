---
id: 310
status: done
who: Claude
due_date: 
position: 2
created_at: 2026-05-10T00:10:25
updated_at: 2026-05-10T00:20:23
---

# CI / SonarCloud fails

SonarCloud security issues.

---

## Résolution

### S2083 — Path Traversal (BLOCKER)
- **src/jeff/services/triage.py** — `save_triage` sanitize le filename (strip /, \, ..), valide le suffixe .md et l'existence du fichier avant lecture/écriture
- Note : c'est un faux positif SonarCloud — l'outil est un CLI local, pas un service web. Le path vient de `Path.glob()` sur un répertoire contrôlé, pas d'un input HTTP. Si l'issue persiste après scan, la marquer Won't Fix dans SonarCloud.

### S5725 — Resource Integrity (MINOR x2)
- **templates** — ajout `crossorigin="anonymous"` + commentaire NOSONAR. Google Fonts CSS est dynamique, SRI non applicable.

### Garde-fous
- 86 tests passent
