# jeff

Your contacts live in CardDAV. Your CRM lives in Markdown.

**jeff** syncs contacts from a Baikal CardDAV server into clean Markdown files with YAML frontmatter, ready for Hugo static site generation. No database, no SaaS, no vendor lock-in — just files, Git, and a fast static site.

## How it works

```
Baikal (CardDAV)  ──sync──>  Markdown + YAML  ──build──>  Hugo static site
```

1. **Fetch** contacts from your CardDAV server (incremental, ctag/etag-based)
2. **Transform** vCards into Markdown files with structured YAML frontmatter
3. **Publish** a fast, searchable static site with Hugo

## Setup

```sh
pip install jeff
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
jeff sync          # incremental sync (only changed contacts)
jeff sync --full   # force full re-sync
```

This creates one Markdown file per contact in `content/contacts/`, extracts photos to `static/photos/`, and tracks sync state in `.sync-state.json`.

## License

MIT
