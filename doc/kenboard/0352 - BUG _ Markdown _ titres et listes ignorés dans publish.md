---
id: 352
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-20T11:54:00
updated_at: 2026-05-20T11:54:00
---

# BUG / Markdown / titres et listes ignorés dans publish

`jeff publish` convertit les notes MD en HTML, mais plusieurs cas ne fonctionnaient pas : `- **tiret et gras**`, `## Titre 2`, gras dans les listes.

---

## Cause racine
Python-Markdown exige une **ligne vide** avant un titre et avant le premier item d'une liste. Les notes saisies à la main ne respectent pas cette contrainte, donc les `##` et les `-` étaient rendus en texte brut dans un `<p>`.

## Résolution
- **src/jeff/services/publish.py** — `_normalize_markdown()` insère une ligne vide avant les `#..######` et avant la première puce d'une liste (sans casser les listes serrées).
- Filtre `markdown` enrichi avec les extensions `extra` et `sane_lists`.
- **tests/unit/test_publish.py** — 4 tests ajoutés : titre sans ligne vide, liste avec gras, gras inline, liste serrée sans `<p>` parasite.

## Garde-fous
- 170 tests passent
