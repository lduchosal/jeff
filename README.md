<p align="center">
  <img src="logo.svg" alt="jeff" width="128" height="128">
</p>

<h1 align="center">jeff</h1>

<p align="center">Your contacts live in CardDAV. Your CRM lives in Markdown.</p>

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
