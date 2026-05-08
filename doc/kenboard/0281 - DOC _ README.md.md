---
id: 281
status: done
who: Claude
due_date: 
position: 4
created_at: 2026-05-08T23:20:20
updated_at: 2026-05-08T23:48:46
---

# DOC / README.md

Minimal, petit texte marketing explicatif.

---

## Resolution

### Fichier : README.md

Pitch en une ligne : "Your contacts live in CardDAV. Your CRM lives in Markdown."

Contenu :
- Description courte du projet (sync CardDAV → Markdown → Hugo)
- Schema du flux en ASCII : Baikal → Markdown + YAML → Hugo static site
- Les 3 etapes : Fetch, Transform, Publish
- Setup en 3 commandes (pip install, .jeff, chmod)
- Licence MIT

### Pourquoi ce choix

Pas de doc technique dans le README — juste le pitch et le quickstart. La doc detaillee (config, architecture, vCard mapping) ira dans doc/ quand le projet sera plus mature. Un README court et clair convertit mieux qu'un mur de texte.
