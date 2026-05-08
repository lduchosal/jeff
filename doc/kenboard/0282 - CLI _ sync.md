---
id: 282
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-08T23:22:01
updated_at: 2026-05-08T23:48:45
---

# CLI / sync

jeff sync synchronise carddav server with local sync dir

---

## Resolution

### Fichier : src/jeff/cli.py

Commande CLI Click avec entry point `jeff sync` :

1. Charge la config depuis .jeff (ou env vars, ou --config flag)
2. Valide les champs requis (carddav_url, username, password) — exit 1 si manquant
3. Decouvre l'addressbook automatiquement (premier resultat de PROPFIND)
4. Sync incrementale via ctag/etag (ou --full pour forcer)
5. Transforme les vCards modifiees en fichiers .md + photos
6. Detecte les contacts supprimes cote serveur (supprime le .md local)
7. Enrichit le SyncState avec les slugs pour la detection future des suppressions
8. Sauvegarde l'etat dans .sync-state.json

### Entry point pyproject.toml

```
[project.scripts]
jeff = "jeff.cli:cli"
```

Apres `pip install -e .` : commande `jeff sync` disponible directement.

### Tests : tests/unit/test_cli.py — 4 tests

- sync up to date (ctag unchanged → "Already up to date")
- sync writes contacts (nouveau contact → .md cree)
- sync sans config → exit 1 avec message clair
- --version affiche la version

### Teste end-to-end sur Baikal reel

- Premier run : 3 contacts ecrits (jeff-harris, claude-monet, luc-duchosal)
- Deuxieme run : "Already up to date" (zero requete supplementaire, ctag cache)
- Fichiers generes : content/contacts/*.md + static/photos/*.png + .sync-state.json
