---
id: 286
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-08T23:37:42
updated_at: 2026-05-08T23:48:45
---

# CLI / Sync / update url

Le .jeff contient l'url de publication des contacts. Le CLI jeff sync update le champ url dans Baikal. Voir ken #273.

---

## Resolution

### Nouveau champ config : publish_url

Dans .jeff :
```
publish_url=https://crm.example.com
```

Override env : JEFF_PUBLISH_URL

### Fichier : src/jeff/urlback.py

- **inject_crm_url(vcard_raw, url)** : injecte item99.URL + item99.X-ABLabel:Profil CRM avant END:VCARD. Retourne None si URL deja presente. Nettoie les anciens item99 avant injection.
- **build_profile_url(publish_url, slug)** : construit l'URL complete (ex: https://crm.example.com/contacts/jean-dupont.html)

### Integration dans jeff sync (cli.py)

Apres la transformation des contacts, si publish_url est configure :
1. Pour chaque contact synce, construit l'URL du profil
2. Injecte dans le vCard si absent
3. PUT avec If-Match etag (verrouillage optimiste)
4. Met a jour le state avec le nouveau etag (le PUT change le ctag/etag)

### Resultat dans le vCard (visible sur iPhone)

```
item99.URL:https://crm.example.com/contacts/luc-duchosal.html
item99.X-ABLabel:Profil CRM
```

### Tests : tests/unit/test_urlback.py — 5 tests

- Injection URL dans vCard
- Skip si URL deja presente
- Remplacement item99 stale
- Construction URL de base
- Trailing slash

### Verifie sur Baikal reel

153 contacts avec URL CRM injectee. Deuxieme sync : skip (URL deja presente).
