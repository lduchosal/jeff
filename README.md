<p align="center">
  <img src="logo.svg" alt="jeff" width="480">
</p>

<h1 align="center">jeff</h1>

<p align="center">Your contacts live in CardDAV. Your CRM lives in Markdown.</p>

<p align="center">

[![PyPI version](https://img.shields.io/pypi/v/jeff-contacts.svg)](https://pypi.org/project/jeff-contacts/)
[![Python versions](https://img.shields.io/pypi/pyversions/jeff-contacts.svg)](https://pypi.org/project/jeff-contacts/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build](https://github.com/lduchosal/jeff/actions/workflows/python-package.yml/badge.svg)](https://github.com/lduchosal/jeff/actions/workflows/python-package.yml)
[![Publish](https://github.com/lduchosal/jeff/actions/workflows/publish.yml/badge.svg)](https://github.com/lduchosal/jeff/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/lduchosal/jeff/branch/main/graph/badge.svg)](https://codecov.io/gh/lduchosal/jeff)
[![Docstring coverage](./interrogate_badge.svg)](./interrogate_badge.svg)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=lduchosal_jeff&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=lduchosal_jeff)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=lduchosal_jeff&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=lduchosal_jeff)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=lduchosal_jeff&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=lduchosal_jeff)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=lduchosal_jeff&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=lduchosal_jeff)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=lduchosal_jeff&metric=bugs)](https://sonarcloud.io/summary/new_code?id=lduchosal_jeff)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=lduchosal_jeff&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=lduchosal_jeff)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=lduchosal_jeff&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=lduchosal_jeff)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=lduchosal_jeff&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=lduchosal_jeff)

</p>

**jeff** syncs contacts from a Baikal CardDAV server into clean Markdown files with YAML frontmatter, then publishes a static HTML site. No database, no SaaS, no vendor lock-in — just files, Git, and a fast static site.

## Quick start

```sh
pip install jeff-contacts
jeff init                # creates .jeff config file
# Edit .jeff with your CardDAV credentials
jeff sync                # fetch contacts
jeff publish             # build HTML site
open public/index.html
```

## Workflow

Le workflow jeff se fait en 5 étapes. Les 4 premières sont à faire une fois lors de la mise en place, la dernière tourne quotidiennement.

### 1. `jeff sync` — Récupérer les contacts

```sh
jeff sync           # sync incrémental (seuls les changements)
jeff sync --full    # force un re-sync complet
```

Connecte le serveur CardDAV (Baikal), détecte les contacts modifiés via ctag/etag, télécharge les vCards et les transforme en fichiers Markdown avec frontmatter YAML. Chaque contact devient un fichier `.md` dans `content/contacts/`.

Le sync est incrémental : seuls les contacts ajoutés, modifiés ou supprimés depuis le dernier sync sont traités. Un `--full` force la régénération de tous les fichiers.

### 2. `jeff triage` — Trier les contacts

```sh
jeff triage
```

```
  [1/559] ──────────────────────────────────────────
  Jean Dupont
    tags: ami, ski, photo
    note: Photographe amateur
    addr: Avenue des Alpes 109, Geneve, Suisse
    email: jean@example.com
    phone: +41791234567

  > a a h H    # actif, ami, haute priorité, homme
  ✓ Jean Dupont → actif
```

Passe en revue chaque contact non trié et permet de décider rapidement :
- **a** = actif (garder dans le CRM) avec relation, priorité et genre
- **r** = archivé (masqué du dashboard mais conservé)
- **s** = skip (on décide plus tard)
- **q** = quitter (reprend où on s'est arrêté la prochaine fois)

Relations : `a`=ami, `c`=collègue, `f`=famille, `k`=connaissance.
Priorités : `h`=haute, `m`=moyenne, `b`=basse.
Genre : `H`=homme, `F`=femme.

### 3. `jeff genre` — Assigner le genre

```sh
jeff genre
```

```
  [1/204] Jean Dupont: h
  [2/204] Marie Martin: f
  [3/204] Acme Corp: n
```

Passe rapidement sur tous les contacts sans genre. Utile pour :
- Les liens familiaux (distinguer père/mère automatiquement)
- L'affichage dans le dashboard (♂️/♀️)
- Le writeback vers CardDAV (X-GENDER)

Codes : `H`=homme, `F`=femme, `N`=none (entreprise), Enter=skip, `q`=quit.

### 4. `jeff famille` — Liens familiaux

```sh
jeff famille              # tous les contacts famille
jeff famille dupont       # filtrer par nom
jeff famille --check      # vérifier la cohérence
```

```
── [1/54] Jacques Dupont (homme) ──
    ↳ (aucun lien)

    1. Anne Dupont (femme)
    2. Jean Dupont (homme)
    3. Luc Dupont (homme)

    f=père m=mère w=conjoint c=enfant b=frère/sœur
    ?texte=chercher  Enter=skip  q=quit

  > 1w 2c 3c
  ✓ Jacques Dupont: conjoint=anne-dupont enfants=[jean-dupont, luc-dupont]
  ↔ Anne Dupont: conjoint=jacques-dupont
  ↔ Jean Dupont: pere=jacques-dupont
  ↔ Luc Dupont: pere=jacques-dupont
```

Pour chaque contact famille, affiche les membres du même nom de famille numérotés. On tape les numéros avec le code de relation. Les liens sont écrits **réciproquement** — assigner un père ajoute automatiquement l'enfant chez le père, et le genre détermine si c'est père ou mère.

`jeff famille --check` vérifie que tous les liens sont bidirectionnels et propose de corriger les incohérences.

### 5. `jeff note` — Consigner une interaction

```sh
jeff note antoine                       # note pour aujourd'hui
jeff note antoine --date 2025-05-06     # date passée
```

```
  Antoine Martin
  type (w=whatsapp  t=tel  m=mail  v=visite  n=note): t
  note: Pris des nouvelles, on planifie une rando pour juin.
  ✓ 2025-05-06.md
```

Crée un fichier d'interaction daté dans le dossier du contact. La recherche est partielle — `jeff note ant` trouve "Antoine Martin". Chaque interaction est un `.md` avec date et type, visible dans le dossier du contact :

```
content/contacts/antoine-martin/
  antoine-martin.md     # fiche contact
  2025-05-06.md         # interaction WhatsApp
  2025-04-01.md         # interaction téléphone
```

### 6. `jeff cron` — Automatisation quotidienne

```sh
jeff cron
```

```
── Sync ──
Discovering addressbooks...
Addressbook: Contacts
Already up to date.

── Birthdays ──
  🎂 Jean Dupont (recorded)

── Publish ──
Published 204 contact(s) to public/
```

Enchaîne automatiquement : **sync** → **détection des anniversaires** → **publication du site HTML**. Conçu pour tourner dans un crontab :

```
0 7 * * * cd /path/to/project && jeff cron
```

Le site publié inclut :
- Dashboard avec contacts groupés par relation et triés par priorité
- Section anniversaires du jour avec bouton WhatsApp pré-rempli
- Arbre généalogique (Graphviz SVG)
- Fiches contact avec coordonnées, liens familiaux et signe astrologique

## Autres commandes

| Commande | Description |
|----------|-------------|
| `jeff delete` | Marquer des contacts archivés pour suppression du CardDAV |
| `jeff check` | Détecter et nettoyer les doublons (même UID) |
| `jeff export` | Exporter au format SquirrelMail (.abook) |
| `jeff birthday-mail` | Envoyer un rappel anniversaire par email |
| `jeff sync --writeback-gender` | Pousser le genre vers CardDAV (X-GENDER) |
| `jeff sync --writeback-famille` | Pousser les liens familiaux vers CardDAV (RELATED) |

## Architecture

```
src/jeff/
  cli.py                  CLI commands (click)
  domain/                 Business objects
    carddav.py            CardDAV client
    config.py             Configuration (.jeff file)
    transform.py          vCard → Markdown
    urlback.py            vCard injection (URL, gender, RELATED)
  services/               Business logic
    sync.py               Sync orchestration
    publish.py            Static site builder
    triage.py             Contact triage
    famille.py            Family link management
    genealogy.py          Family tree (Graphviz)
    birthday.py           Birthday detection
    birthday_mail.py      Email reminders
    genre.py              Gender assignment
    duplicates.py         Duplicate detection
    export.py             Address book export
```

## License

MIT
