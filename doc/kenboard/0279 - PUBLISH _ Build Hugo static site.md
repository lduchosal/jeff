---
id: 279
status: done
who: Claude
due_date: 
position: 3
created_at: 2026-05-08T22:45:48
updated_at: 2026-05-08T23:48:47
---

# PUBLISH / Build Hugo static site

Publier un site statique HTML a partir des fichiers Markdown.

Decision : Jinja2 (pas Hugo). Raisons :
- Zero dependance externe (pas de Go a installer)
- Integre dans le CLI jeff (jeff publish)
- Le template HTML et le CSS existent deja (doc/ui/)
- Pour quelques centaines de contacts, Hugo est overkill

---

## Resolution

### Fichier : src/jeff/publish.py

- **_parse_frontmatter()** : parse YAML entre les --- d'un fichier .md
- **_load_contacts()** : charge tous les .md d'un dossier, trie par nom
- **build_site()** : pipeline complet — charge contacts, rend HTML via Jinja2, copie CSS + photos
- **_DotDict** : wrapper dict pour l'acces par attribut dans les templates Jinja2

### Templates : src/jeff/templates/

- **contact.html** : fiche contact complete (header avec avatar, tags, notes, sidebar avec coordonnees/WhatsApp/positions/liens)
- **index.html** : liste de tous les contacts avec avatar, nom, tags

### Commande CLI : jeff publish

```
jeff publish           # genere dans public/
jeff publish -o dist   # genere dans dist/
```

Structure generee :
```
public/
  index.html           # liste des contacts
  contacts/
    jean-dupont.html   # fiche par contact
  css/
    contact.css        # copie du CSS
  photos/
    jean-dupont.png    # copie des photos
```

### Tests : tests/unit/test_publish.py — 6 tests

- Parse frontmatter YAML
- Handle no frontmatter
- Build contact + index HTML
- Copy CSS
- Copy photos
- Empty content dir → site vide valide

### Teste end-to-end

3 contacts publies depuis les donnees syncees de Baikal. Site complet avec index, fiches, photos, CSS.
