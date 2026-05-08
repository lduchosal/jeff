---
id: 266
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-07T12:14:57
updated_at: 2026-05-08T19:16:27
---

# JEFF / CRM / Markdown CRM guidé par un agent

# SOTA — CRM Markdown filesystem + publication HTML + agent

Recherche effectuee le 2026-05-07.

---

## 1. Projets existants

### hal_md — PRM en Markdown (reference)

Le projet le plus abouti dans cette categorie.

- **Concept** : gestion du reseau social personnel via fichiers Markdown +
  YAML frontmatter, visualise dans Obsidian.
- **Structure** :
  ```
  people/
    jean-dupont/
      jean-dupont.md          # fiche contact (frontmatter + notes)
      2026-05-01.md           # interaction datee
      2026-04-15.md
  organizations/
    acme-corp.md
  attachments/
  templates/
  queries/                    # requetes par mois (anniversaires, etc.)
  ```
- **Frontmatter contact** :
  ```yaml
  ---
  name: Jean Dupont
  slug: jean-dupont
  email: jean@example.com
  phone: "+41 79 123 45 67"
  birthday: 1985-03-15
  tags: [friend, strong, a-list]
  skills: [python, devops]
  positions:
    - org: acme-corp
      title: CTO
  links:
    - person: marie-martin
      type: colleague
  ---
  ```
- **Outils CLI** (Python) : `comms.py` (recents), `most_contacted.py`
  (frequence), `last_contact.py`, `md_birthdays.py`
- **Stack** : Python, Obsidian (wikilinks + Dataview), Git
- **Licence** : MIT

Source : [github.com/thephm/hal_md](https://github.com/thephm/hal_md)

---

### axis-crm — CRM Git pour freelances

- **Concept** : CRM complet (clients, projets, reunions, tarifs) en
  Markdown dans un repo Git. Zero database, zero SaaS.
- **Init** : `npx axis-crm init`
- **Stack** : Node.js CLI + Obsidian (dashboards Dataview) + n8n
  (automatisations)
- **Automatisation** : webhooks de reunions → IA identifie le client,
  extrait resume + actions, commit les notes dans le bon dossier
- **Licence** : npm public

Source : [libraries.io/npm/axis-crm](https://libraries.io/npm/axis-crm)

---

### markdown-crm — template minimaliste

- **Structure** :
  ```
  contacts/
  companies/
  interactions/
  tasks/
  templates/
  archive/
  ```
- **Champs** : nom, entreprise, email, tel, statut (Lead/Client/...),
  tags, date dernier contact, date prochain follow-up, notes, logs
- **Philosophie** : documentation coherente plutot qu'automatisation
  complexe

Source : [github.com/CLSherrod/markdown-crm](https://github.com/CLSherrod/markdown-crm)

---

## 2. Patterns Obsidian

La communaute Obsidian a developpe des patterns CRM matures :

| Pattern                      | Detail                                                        |
|------------------------------|---------------------------------------------------------------|
| Nommage                      | `@Prenom Nom - Entreprise`                                    |
| Aliases frontmatter          | Prenom, Nom, email — pour lien rapide                         |
| Interactions dans le journal | `appele [[jean-dupont]] de [[acme-corp]]` dans la note du jour |
| Dataview queries             | Contacts pas contactes depuis X jours, taches ouvertes par personne |
| Tags relationnels            | `#ami`, `#prospect`, `#a-list`, `#froid`                      |

**Insight cle** (forum Obsidian) : l'information subjective (comment
on s'est connecte, contexte relationnel) a plus de valeur que les
coordonnees objectives deja stockees ailleurs.

Source : [forum.obsidian.md/t/crm-system-in-markdown](https://forum.obsidian.md/t/crm-system-in-markdown-in-obsidian/15691)

---

## 3. Discussion HN : CRM Markdown optimise pour agents LLM

Un thread recent pose la question : un CRM purement Markdown, concu
pour les agents LLM plutot que pour une UI humaine, est-ce viable ?

### Arguments pour

- **Markdown = format le plus digestible pour les LLM** — pas besoin
  de generer du SQL pour comprendre l'historique d'un client
- **Simplicite operationnelle** : backup/replication via rsync ou Git
- **Agent autonome en arriere-plan** : un LLM peut lire les fichiers,
  mettre a jour les resumes, categoriser les clients, maintenir la
  memoire systeme

### Arguments contre

- **Verrouillage fichiers** : conflits de concurrence si plusieurs
  agents ecrivent simultanement
- **Limites inode** : a grande echelle, trop de petits fichiers
- **Pas de garanties ACID** : risque de corruption sans transaction
- **Tokens** : un commentateur argue que les LLM ecrivent des requetes
  SQL plus efficacement que traiter de gros documents markdown

### Architecture proposee

```
Filesystem Markdown (source de verite)
  + Redis (index / recherche)
  + Agent LLM (cerveau du systeme)
  + YAML frontmatter (metadonnees structurees)
```

Source : [news.ycombinator.com/item?id=47721153](https://news.ycombinator.com/item?id=47721153)

---

## 4. Publication HTML via Hugo

Hugo est le candidat naturel pour publier un CRM markdown en site statique.

### Mecanismes utiles

| Fonctionnalite Hugo       | Usage CRM                                                  |
|---------------------------|-------------------------------------------------------------|
| **Content types**         | Un type par entite : `contacts/`, `companies/`, `interactions/` |
| **Taxonomies custom**     | `tags`, `secteur`, `statut`, `ville` — pages auto-generees |
| **Archetypes**            | Templates frontmatter par type (nouveau contact, nouvelle interaction) |
| **Frontmatter**           | YAML structure → accessible dans les templates Go           |
| **Data files** (`data/`)  | Listes de reference (pays, secteurs) en YAML/JSON           |
| **Shortcodes**            | Widgets inline (timeline interactions, carte contact)       |
| **Related content**       | Liens automatiques entre contacts et entreprises            |
| **Output formats**        | HTML, JSON API, RSS — multi-format depuis les memes sources |
| **Taxonomies imbriquees** | `secteur/tech/saas` — hierarchie de classification          |

### Structure Hugo CRM

```
content/
  contacts/
    jean-dupont.md       # frontmatter + bio + notes
    marie-martin.md
  companies/
    acme-corp.md         # frontmatter + description
  interactions/
    2026-05-07-appel-jean.md
layouts/
  contacts/
    single.html          # fiche contact
    list.html            # repertoire
  companies/
    single.html
  interactions/
    single.html
data/
  sectors.yaml           # referentiel secteurs
  statuses.yaml          # referentiel statuts
archetypes/
  contacts.md            # template nouveau contact
  interactions.md        # template nouvelle interaction
```

### Avantages

- **Build ultra-rapide** : Hugo genere des milliers de pages en < 1s
- **Recherche** : via Fuse.js ou Pagefind (index JSON genere au build)
- **Deploiement** : `hugo && rsync` ou CI/CD vers n'importe quel hebergeur
- **Versioning** : tout le CRM dans Git, historique complet
- **Acces prive** : serveur avec auth basique ou SSO, ou publication interne

Sources : [gohugo.io/content-management/taxonomies](https://gohugo.io/content-management/taxonomies/),
[gohugo.io/content-management/organization](https://gohugo.io/content-management/organization/)

---

## 5. Role de l'agent LLM

En combinant les patterns Karpathy (tache 264) et CRM markdown :

### Operations agent

| Operation       | Declencheur              | Action                                                |
|-----------------|--------------------------|-------------------------------------------------------|
| **Ingest**      | Nouveau contact / source | Cree la fiche, enrichit le frontmatter, lie aux entites existantes |
| **Log**         | Apres un appel / email   | Cree un fichier interaction, met a jour `last_contact` dans la fiche |
| **Enrich**      | Periodique ou a la demande | Recherche web, complete les champs manquants (titre, entreprise, LinkedIn) |
| **Query**       | Question utilisateur     | Lit l'index, synthetise une reponse avec citations     |
| **Lint**        | Periodique               | Detecte doublons, contacts sans interaction recente, champs vides |
| **Summarize**   | Fin de journee / semaine | Genere un resume des interactions recentes, prochains follow-ups |
| **Publish**     | Commit / CI              | Declenche `hugo build`, deploie le site statique       |

### Schema agent (type CLAUDE.md)

Le schema definirait :
- Les types d'entites et leurs champs obligatoires/optionnels
- Les conventions de nommage des fichiers
- Les regles de cross-reference (wikilinks)
- Les workflows d'ingest et de lint
- Le format des interactions
- Les taxonomies Hugo a maintenir

---

## 6. Flat-file CMS alternatifs (si Hugo ne suffit pas)

| Outil       | Stack          | Point fort                              |
|-------------|----------------|-----------------------------------------|
| **Grav**    | PHP, Markdown  | Admin UI integree, systeme de pages modulaires |
| **Statamic**| PHP/Laravel    | YAML + Markdown, live preview, API REST, multi-user |
| **Pico**    | PHP, Markdown  | Ultra-simple, zero admin                |
| **Kirby**   | PHP            | Chaque page = un dossier, tres flexible |

Pour un CRM gere par agent, **Hugo reste le meilleur choix** car :
- Pas de runtime serveur (pur statique)
- Build scriptable depuis un agent
- Taxonomies et content types natifs
- Ecosysteme de recherche client-side (Pagefind, Fuse.js)

---

## 7. Synthese

### Architecture recommandee

```
crm/
  content/              ← fichiers Markdown (source de verite)
    contacts/
    companies/
    interactions/
  data/                 ← referentiels YAML
  archetypes/           ← templates frontmatter
  layouts/              ← templates Hugo
  SCHEMA.md             ← regles pour l'agent
  index.md              ← catalogue (style Karpathy)

Git                     ← versioning + historique + collaboration
Agent LLM              ← ingest, enrich, lint, query, summarize
Hugo                    ← publication HTML statique
```

### Stack minimal pour demarrer

1. **Fichiers Markdown + YAML frontmatter** dans un repo Git
2. **SCHEMA.md** definissant les conventions pour l'agent
3. **Hugo** avec content types + taxonomies pour la publication
4. **Agent Claude** pour la gestion courante (via CLAUDE.md)
5. **Pagefind** ou **Fuse.js** pour la recherche cote client

### Complexite a eviter

- Pas de base de donnees — le filesystem EST la base
- Pas de Redis sauf si > 1000 contacts
- Pas de multi-agent concurrent — un seul agent ecrit a la fois
- Pas de frontmatter surcharge — commencer avec 5-8 champs, etendre au besoin
