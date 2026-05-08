---
id: 277
status: done
who: Claude
due_date: 
position: 6
created_at: 2026-05-08T22:45:47
updated_at: 2026-05-08T23:08:34
---

# SYNC / Fetch contacts from CardDAV Baikal

Connecter au serveur CardDAV Baikal via requests + lxml. Implementer la decouverte des addressbooks (PROPFIND), le fetch des contacts (addressbook-multiget REPORT), et la detection des changements (sync-token / ctag / etags). Auth Basic sur HTTPS. Stocker l'etat de sync dans .sync-state.json.

---

## Resolution

### Fichier : src/jeff/carddav.py

Module minimal, 3 classes :

- **CardDAVConfig** — url, username, password
- **CardDAVClient** — client HTTP avec 6 methodes :
  - discover_addressbooks() → PROPFIND Depth:1, filtre resourcetype addressbook
  - get_ctag() → PROPFIND Depth:0, parse cs:getctag
  - list_contacts() → PROPFIND Depth:1, retourne dict href→etag, skip collection
  - fetch_contacts() → addressbook-multiget REPORT, batch fetch vCard raw
  - fetch_all_contacts() → combine list + fetch
  - sync() → incremental : ctag check, etag diff, fetch only changed, detect deleted
- **SyncState** — dataclass avec save/load JSON (.sync-state.json)

### Detection de changements

1. get_ctag() — si identique au state, return vide (zero requete)
2. list_contacts() — diff etags vs state
3. fetch_contacts() — multiget uniquement les hrefs changes
4. retourne (new_or_updated, deleted_hrefs, new_state)

### Tests : tests/unit/test_carddav.py — 12 tests

HTTP mocke au niveau requests.Session.request (meme pattern que kenboard/test_ken.py). Couvre :
- SyncState round-trip JSON
- SyncState load fichier manquant
- Decouverte addressbooks
- Parse ctag
- Liste contacts (skip collection)
- Multiget parse vCards
- Empty hrefs → pas de requete
- Sync ctag unchanged → vide
- Sync detect new contacts
- Sync detect deleted contacts
- Sync detect updated contacts (etag change)

### Stack

requests + lxml (XML parsing) — pas de dependance vdirsyncer
