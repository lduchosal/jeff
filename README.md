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
Baikal (CardDAV)  ──sync──>  Markdown + YAML  ──build──>  Hugo static site
```

1. **Fetch** contacts from your CardDAV server (incremental, ctag/etag-based)
2. **Transform** vCards into Markdown files with structured YAML frontmatter
3. **Publish** a fast, searchable static site with Hugo

## Setup

```sh
pip install jeff-contacts
```

Create a `.jeff` file at the root of your project:

```
carddav_url=https://your-baikal.example.com/dav.php/addressbooks/user/default/
carddav_username=user
carddav_password=secret
```

```sh
chmod 600 .jeff
```

## Usage

```sh
jeff sync           # incremental sync (only changed contacts)
jeff sync --full    # force full re-sync
jeff publish        # build static HTML site
jeff --verbose sync # debug logging
```

`jeff sync` creates one Markdown file per contact in `content/contacts/`, extracts photos to `static/photos/`, and tracks sync state in `.sync-state.json`.

`jeff publish` generates a static HTML site in `public/` with a contact index and individual profile pages.

## License

MIT
