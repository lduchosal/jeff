---
id: 292
status: done
who: Claude
due_date: 
position: 0
created_at: 2026-05-09T08:09:11
updated_at: 2026-05-09T20:25:48
---

# UI / LOGO

Le script publish.sh affiche un joli logo JEFF
Reprendre l'ascii art du publish.sh pour en faire un pixel art en svg et mettre à jour le logo.svg

---

## Résolution

### Logo
![logo](https://raw.githubusercontent.com/lduchosal/jeff/main/logo.svg)

### Modifications
- **logo.svg** — remplacé par un pixel art 32x32 reproduisant les lettres JEFF de l'ASCII art du publish.sh. Fond dark teal (#0A3C3C), lettres bright teal (#4DD9C9) avec highlight sur la première ligne (#7AEADD).

### Comportements obtenus
- Logo SVG carré 32x32, utilisable comme favicon
- Les 4 lettres J-E-F-F sont lisibles en pixel art
- Style cohérent avec la palette teal du projet

### Garde-fous
- SVG valide, viewBox 32x32, shape-rendering crispEdges pour un rendu net en pixel art
