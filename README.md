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

## How it works

```
Baikal (CardDAV)  ──sync──>  Markdown + YAML  ──publish──>  Static HTML
```

1. **Sync** contacts from your CardDAV server (incremental, ctag/etag-based)
2. **Transform** vCards into Markdown files with structured YAML frontmatter
3. **Triage** contacts interactively (actif/archivé, relation, priority, gender)
4. **Publish** a dashboard with contact cards, family tree, and birthday reminders

## Quick start

```sh
pip install jeff-contacts
jeff init
```

This creates a `.jeff` config file. Edit it with your CardDAV credentials:

```
carddav_url=https://your-baikal.example.com/dav.php/addressbooks/user/default/
carddav_username=user
carddav_password=secret
```

Then sync and publish:

```sh
jeff sync
jeff publish
open public/index.html
```

## Commands

```
jeff --help

Workflow quotidien:
  jeff cron              Sync + anniversaires + publish (pour crontab)

Sync & publication:
  jeff sync              Sync contacts depuis CardDAV
  jeff sync --full       Force un re-sync complet
  jeff publish           Génère le site HTML statique

Gestion des contacts:
  jeff triage            Trier les contacts (actif/archivé/relation/priorité)
  jeff genre             Assigner le genre (H=homme, F=femme, N=none)
  jeff delete            Marquer des contacts pour suppression
  jeff check             Détecter et nettoyer les doublons (même UID)

Famille:
  jeff famille           Éditer les liens familiaux (père, mère, conjoint, enfants)
  jeff famille dupont    Éditer un contact spécifique
  jeff famille --check   Vérifier la cohérence bidirectionnelle des liens

Export & notifications:
  jeff export            Exporter au format SquirrelMail (.abook)
  jeff birthday-mail     Envoyer un rappel anniversaire par email

Configuration:
  jeff init              Créer le fichier .jeff
```

## Triage

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

Format: `a <relation> <priority> <genre>` — `r` pour archiver, `s` pour skip, `q` pour quitter.

## Family links

```sh
jeff famille
```

```
── [1/54] Jacques Dupont (homme) ──
    ↳ (aucun lien)

    1. Anne Dupont (femme)
    2. Jean Dupont (homme)
    3. Luc Dupont (homme)

    f=père m=mère w=conjoint c=enfant b=frère/sœur

  > 1w 2c 3c
  ✓ Jacques Dupont: conjoint=anne-dupont enfants=[jean-dupont, luc-dupont]
  ↔ Anne Dupont: conjoint=jacques-dupont
  ↔ Jean Dupont: pere=jacques-dupont
  ↔ Luc Dupont: pere=jacques-dupont
```

Links are written **reciprocally** — setting a parent also sets the child, and vice versa.

## Dashboard

`jeff publish` generates a static HTML dashboard with:

- Contacts grouped by relation (famille, ami, collegue, connaissance)
- Priority badges and gender indicators
- Birthday section with WhatsApp message button
- Genealogy tree (Graphviz SVG)
- Contact detail pages with all info, family links, and zodiac sign

## Daily cron

```sh
jeff cron
```

Runs sync + birthday detection + publish in one command. Add to crontab:

```
0 7 * * * cd /path/to/project && jeff cron
```

Optional birthday email reminders:

```
0 23 * * * cd /path && jeff birthday-mail --tomorrow
0  6 * * * cd /path && jeff birthday-mail
```

Requires `mail_to=you@example.com` in `.jeff` and `sendmail`/`msmtp` configured.

## Writeback to CardDAV

jeff can write data back to your CardDAV server:

```sh
jeff sync --writeback-gender    # Push gender (X-GENDER) to CardDAV
jeff sync --writeback-famille   # Push family links (RELATED) to CardDAV
```

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
