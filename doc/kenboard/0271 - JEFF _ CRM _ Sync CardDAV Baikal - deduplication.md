---
id: 271
status: doing
who: Claude
due_date: 
position: 0
created_at: 2026-05-08T19:12:36
updated_at: 2026-05-08T21:18:43
---

# JEFF / CRM / Sync CardDAV Baikal - deduplication

Les contacts existants sont stockes dans une base CardDAV Baikal : https://carddav.example.com/

Le CRM Markdown (tache 266) doit prendre en compte cette source de verite pour eviter la proliferation de doublons.

La base carddav est la source de verite. Tout est stocke dans la base carddav. Un export vers MD permet a un modele d'intervenir et d'avoir un export HTML (hugo) facilement consultable et agreable a lire.

Suite de la tache 266.

---

## Resolution

Recherche effectuee le 2026-05-08.

---

## 1. Librairies Python pour CardDAV / vCard

### vdirsyncer (pip install vdirsyncer)

Outil CLI de sync CardDAV/CalDAV vers fichiers locaux .vcf. Config INI, commandes discover + sync. Pas d'API Python publique stable (issue #770 ouverte). Internals utilisables mais non garantis entre versions. Gere sync bidirectionnelle avec conflict_resolution configurable.

### pyCardDAV — DEPRECIE

Remplace par vdirsyncer + khard. Code source utile comme reference pour les requetes HTTP CardDAV brutes (PROPFIND, PUT, DELETE, REPORT via requests).

### khard (pip install khard, v0.20.0)

Gestionnaire de contacts vCard en console. Opere sur fichiers .vcf locaux (ne fait PAS de sync reseau). S'utilise en complement de vdirsyncer. Activement maintenu.

### vobject (pip install vobject, v1.0.0+)

LA librairie Python pour parser/serialiser des vCards. Supporte vCard 3.0 nativement, 4.0 en import partiel. API claire :

```python
import vobject
vcard = vobject.readOne(vcf_string)
vcard.fn.value        # "Jean Dupont"
vcard.n.value.family  # "Dupont"
vcard.email.value     # "jean@example.com"
vcard.uid.value       # UID
vcard.serialize()     # -> string vCard
```

### Autres packages utiles

| Package | Usage |
|---------|-------|
| requests + lxml | Client HTTP CardDAV + parsing XML WebDAV |
| ruamel.yaml | YAML read/write preservant commentaires et ordre |
| python-slugify | Slugification des noms |
| thefuzz (ex-fuzzywuzzy) | Matching fuzzy pour deduplication |

### Decision : stack directe requests + lxml + vobject

Evite la dependance a l'API instable de vdirsyncer. Meme approche protocole (PROPFIND, REPORT, PUT) mais controlee.

---

## 2. Protocole CardDAV — essentiels

CardDAV = WebDAV + vCard sur HTTP (RFC 6352). Baikal expose :

| Endpoint | Role |
|----------|------|
| /.well-known/carddav | Decouverte |
| /dav.php/addressbooks/{user}/ | Home set |
| /dav.php/addressbooks/{user}/default/ | Carnet |
| /dav.php/addressbooks/{user}/default/{uid}.vcf | Contact |

Operations cles :
- PROPFIND Depth:1 → liste hrefs + etags
- addressbook-multiget REPORT → fetch batch de vCards
- GET → contact unique
- PUT + If-None-Match: * → creation
- PUT + If-Match: "etag" → mise a jour (verrouillage optimiste)
- DELETE + If-Match: "etag" → suppression

Auth : Basic Auth sur HTTPS (methode standard Baikal).

Detection de changements (par ordre de preference) :
1. sync-token (RFC 6578) — le plus efficace, retourne uniquement les deltas
2. CTag — un hash global par collection, necessite diff etags si change
3. ETags — comparaison unitaire par ressource

---

## 3. Baikal — specificites

Serveur CalDAV/CardDAV PHP leger base sur SabreDAV. Backend SQLite ou MySQL.

Particularites :
- Pas d'API REST/JSON (issue #4, jamais implementee) → tout passe par DAV/XML
- Anciennes versions utilisaient /card.php/ au lieu de /dav.php/
- macOS exige des redirects .well-known correctement configures
- Apres mise a jour, toujours tester la connectivite CardDAV
- Auth : Basic (defaut), Digest, ou delegation Apache

---

## 4. Strategie de deduplication

### UID comme cle primaire (cas nominal)

Le champ UID du vCard est l'identifiant universel. Si deux vCards partagent le meme UID = meme contact. Le UID est la cle de jointure entre CardDAV et Markdown.

Probleme : certains exports omettent le UID → generer un UUID v4 a l'import.

### Matching fuzzy (cas sans UID)

```python
from thefuzz import fuzz

def contacts_match(a, b, threshold=85):
    name_score = fuzz.token_sort_ratio(a.fn, b.fn)
    email_match = a.email and b.email and a.email.lower() == b.email.lower()
    return name_score >= threshold or email_match
```

Normalisation prealable :
- Noms : strip, lowercase, gerer "Nom, Prenom" vs "Prenom Nom"
- Telephones : supprimer espaces, tirets, parentheses, prefixes pays
- Emails : lowercase

### Merge

Un contact primaire, enrichi des champs uniques du doublon. Toujours conserver le UID du primaire. Logger les decisions de merge.

---

## 5. Sens de la sync — CardDAV → Markdown (unidirectionnel)

### Decision : CardDAV est la source de verite, export one-way vers Markdown

Justification :
- L'enonce est clair : "La base carddav est la source de verite"
- Le Markdown sert a la consultation (Hugo HTML) et a l'intervention agent (enrichissement, lint)
- La sync bidirectionnelle ajoute une complexite majeure (conflits, verrouillage) sans valeur ajoutee dans ce contexte

### Flux de sync

```
1. PROPFIND addressbook → ctag/sync-token
2. Si change detecte :
   a. PROPFIND Depth:1 → hrefs + etags actuels
   b. Diff avec .sync-state.json local
   c. addressbook-multiget REPORT → fetch vCards modifiees
   d. vobject.readOne() → extraction champs
   e. Ecriture fichier .md (frontmatter YAML + body)
   f. Mise a jour .sync-state.json
3. Contacts supprimes cote serveur → archivage (mv vers archive/)
```

### Etat de sync (.sync-state.json)

```json
{
  "sync_token": "http://sabre.io/ns/sync/1234",
  "contacts": {
    "urn:uuid:f47ac...": {
      "etag": "\"abc123\"",
      "href": "/dav.php/addressbooks/user/default/f47ac.vcf",
      "slug": "jean-dupont",
      "last_sync": "2026-05-08T14:30:00Z"
    }
  }
}
```

---

## 6. Mapping vCard ↔ YAML frontmatter

### Schema complet

```yaml
uid: "urn:uuid:f47ac10b-..."        # ← UID
name: "Jean Dupont"                   # ← FN
name_family: "Dupont"                 # ← N.family
name_given: "Jean"                    # ← N.given
slug: "jean-dupont"                   # ← derive (pas dans vCard)

emails:                               # ← EMAIL (repete)
  - address: "jean@example.com"
    type: work
    pref: true

phones:                               # ← TEL (repete)
  - number: "+41 79 123 45 67"
    type: cell
    pref: true

email: "jean@example.com"            # ← alias commodite (PREF)
phone: "+41 79 123 45 67"            # ← alias commodite (PREF)

addresses:                            # ← ADR (repete)
  - type: work
    street: "Rue du Marche 12"
    city: "Geneve"
    region: "GE"
    postal_code: "1204"
    country: "Switzerland"

positions:                            # ← ORG + TITLE (groupes)
  - org: "acme-corp"
    title: "CTO"

birthday: 1985-03-15                  # ← BDAY
tags: [friend, a-list]                # ← CATEGORIES
urls:                                 # ← URL (repete)
  - url: "https://jeandupont.ch"
    type: home

social:                               # ← X-SOCIALPROFILE / IMPP
  - platform: linkedin
    url: "https://linkedin.com/in/jeandupont"

photo: "photos/jean-dupont.jpg"       # ← PHOTO (fichier local)
note: "Met at FOSDEM 2024."           # ← NOTE
rev: 2026-05-08T14:30:00Z            # ← REV
```

### Schema simplifie (compatible tache 266)

```yaml
name: Jean Dupont
slug: jean-dupont
email: jean@example.com
phone: "+41 79 123 45 67"
birthday: 1985-03-15
tags: [friend, a-list]
positions:
  - org: acme-corp
    title: CTO
links:
  - person: marie-martin
    type: colleague
```

### Pertes a l'import

| Champ vCard | Disposition |
|-------------|-------------|
| PRODID, SOURCE | Drop |
| SOUND, KEY, LOGO | Drop (sauf LOGO → fichier) |
| LABEL (v3) | Drop (reconstruit depuis ADR) |
| GEO | Optionnel geo: {lat, lon} |
| CLASS | → draft: true si CONFIDENTIAL |

### Champs CRM sans equivalent vCard natif

| Champ YAML | Encodage vCard retour |
|------------|----------------------|
| slug | Derive, pas stocke |
| tags | CATEGORIES (round-trip OK) |
| skills | X-CRM-SKILLS |
| links | RELATED (v4) ou X-CRM-LINK (v3) |

### Points critiques

- Telephones avec + doivent etre quotes en YAML
- Photos base64 du vCard → extraites en fichier local
- ORG/TITLE correles via property groups (item1.ORG + item1.TITLE)
- CATEGORIES ↔ tags : round-trip propre
- REV non fiable sur tous les serveurs → hash de fichier comme detection reelle

---

## 7. Integration workflow agent

### Operations agent sur le CRM synce

| Operation | Declencheur | Action |
|-----------|-------------|--------|
| Sync | Periodique / manuel | CardDAV → Markdown (ce SOTA) |
| Lint | Post-sync | Detecte champs vides, doublons fuzzy, contacts orphelins |
| Enrich | A la demande | Complete champs manquants (titre, entreprise, LinkedIn) |
| Query | Question user | Lit les .md, synthetise reponse |
| Publish | Commit / CI | hugo build → site statique |

### Architecture cible

```
carddav.example.com (Baikal)
    │
    ▼  sync (requests + vobject)
crm/
  content/contacts/          ← fichiers .md (frontmatter YAML)
  data/uid-to-slug.json      ← index UID → slug
  .sync-state.json            ← etat de sync (tokens, etags)
  layouts/                    ← templates Hugo
  SCHEMA.md                   ← regles agent
```

### Garde-fous

- Ne jamais ecrire dans CardDAV depuis l'agent (source de verite = Baikal)
- Archiver les contacts supprimes plutot que les supprimer
- Logger toutes les decisions de merge/dedup
- .sync-state.json gitignore (contient des etags volatils)
