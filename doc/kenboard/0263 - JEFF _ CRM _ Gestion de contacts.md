---
id: 263
status: done
who: Claude
due_date: 
position: 2
created_at: 2026-05-07T11:28:03
updated_at: 2026-05-08T19:16:40
---

# JEFF / CRM / Gestion de contacts

# SOTA — Gestion de contacts (CRM)

Recherche effectuee le 2026-05-07.

---

## 1. Benchmark open source (marmelab, janvier 2026)

| # | CRM        | Score | Stack                                        | Licence   |
|---|------------|-------|----------------------------------------------|-----------|
| 1 | Twenty     | 9/10  | TypeScript, React, NestJS, PostgreSQL, Redis | AGPL-3.0  |
| 2 | Atomic CRM | 8/10  | React, shadcn/ui, Supabase, PostgreSQL       | MIT       |
| 3 | Krayin     | 7/10  | PHP 8, Laravel, Vue.js, MySQL                | MIT       |
| 4 | EspoCRM    | 7/10  | PHP 8, Handlebar, Bootstrap, MySQL/PG        | AGPL-3.0  |
| 5 | SuiteCRM   | 5/10  | PHP 8, Smarty, jQuery, MySQL/MariaDB         | AGPL-3.0  |

Criteres : developer-friendliness, vrai open source, adapte PME, setup
rapide, self-hosting simple, UI en anglais, contacts/companies/deals/notes.

Source : [marmelab.com/blog/2026/01/09/open-source-crm-benchmark-2026](https://marmelab.com/blog/2026/01/09/open-source-crm-benchmark-2026.html)

---

## 2. Solutions notables

### Twenty — le leader open source

- **GitHub** : #1 CRM open source (stars)
- **Archi** : React + NestJS + TypeORM + PostgreSQL + Redis, API GraphQL
- **Modele de donnees** : tout est un "objet" (People, Companies, Opportunities,
  Tasks, Notes, Messages). Objets custom avec champs et relations many-to-many
  en first-class.
- **API** : 4 surfaces — Core API (donnees CRM), Metadata API (schema),
  plus REST et webhooks.
- **IA** : serveur MCP natif (Claude, ChatGPT, Cursor) via OAuth.
  Extensions via `npx create-twenty-app` (TypeScript).
- **Limites** : licence AGPL-3.0 (contaminante), pas d'UI mobile native.
- Site : [twenty.com](https://twenty.com/)

### Atomic CRM — le minimaliste

- 15 000 lignes de code. React + shadcn/ui + Supabase (PostgreSQL).
- Licence MIT, tres developer-friendly.
- Limite : peu de fonctionnalites internes, communaute petite.

### EspoCRM — le generaliste

- UX intuitive, riche en fonctionnalites CRM (email, calendrier, rapports).
- PHP 8, facile a heberger sur un petit serveur.
- Limite : complexite du code source pour contribuer.
- Site : [espocrm.com](https://www.espocrm.com/)

### Frappe CRM — l'ecosysteme ERPNext

- Python + Frappe Framework, integration WhatsApp/Twilio/Exotel.
- Modeles de donnees extensibles en Python/JS.
- Heberge a partir de 5 $/mois (utilisateurs illimites).
- Limite : moins de fonctionnalites out-of-the-box que HubSpot.
- Site : [frappe.io/crm](https://frappe.io/crm)

### Monica — CRM personnel (PRM)

- Gestion de relations personnelles (famille, amis, contacts pro).
- Journaux, rappels, photos, timeline relationnelle.
- PHP/Laravel, self-hosted gratuit.
- Philosophie : vie privee, zero tracking, zero pub.
- Site : [monicahq.com](https://www.monicahq.com/)

---

## 3. Solutions SaaS legeres (comparaison)

| Outil       | Positionnement                        | Prix (entree)     |
|-------------|---------------------------------------|--------------------|
| HubSpot CRM | Gratuit forever, montee en gamme      | 0 (freemium)       |
| Bigin (Zoho)| CRM minimaliste pour TPE              | 7 $/user/mois      |
| Capsule CRM | Contacts + pipeline, rapide           | 18 $/user/mois     |
| Copper      | Natif Google Workspace                | 9 $/user/mois      |
| Folk        | AI-native, enrichissement auto        | 20 $/user/mois     |
| noCRM       | Zero bureaucratie, focus leads        | 22 $/user/mois     |

---

## 4. Tendances 2026

### IA et enrichissement

- **Enrichissement statique** : ajout automatique de donnees firmographiques
  (titre, taille entreprise, secteur) depuis des bases externes.
- **Enrichissement dynamique** : mise a jour contextuelle depuis les
  interactions en cours (emails, appels, messages).
- **Agents IA** : remplacent les outils ponctuels — workflows multi-etapes
  autonomes (enrichissement + scoring + relance).
- **Privacy-first AI** : exigence de conception, pas simple checkbox compliance.

### Fonctionnalites IA standard en 2026

1. Lead scoring predictif
2. Generation d'emails
3. Intelligence conversationnelle
4. Previsions de ventes (forecasting)
5. Enrichissement de donnees
6. Chatbots / assistants

### Architecture moderne

- Stack dominant : **TypeScript/React** + **Node.js** backend + **PostgreSQL**
- API-first : GraphQL ou REST
- Custom objects / schema dynamique
- Integration MCP pour assistants IA
- Self-hosting via Docker / Kubernetes

---

## 5. Synthese et recommandation

| Besoin                           | Choix recommande         |
|----------------------------------|--------------------------|
| CRM complet, self-hosted, moderne | **Twenty**              |
| CRM leger, code minimal, MIT     | **Atomic CRM**          |
| CRM personnel / relationnel      | **Monica**              |
| Ecosysteme ERP existant          | **Frappe CRM**          |
| Setup rapide, PHP classique      | **EspoCRM**             |
| Zero maintenance, SaaS gratuit   | **HubSpot CRM** (free)  |

Pour un projet **custom** de gestion de contacts :
- S'inspirer de l'architecture **Twenty** (objets dynamiques, API GraphQL,
  React + NestJS + PostgreSQL) ou de la simplicite d'**Atomic CRM**
  (React + Supabase, 15k LOC).
- Integrer de l'enrichissement de contacts (statique + dynamique) des le
  depart — c'est le differentiel majeur en 2026.
- Prevoir un serveur MCP pour l'integration avec les assistants IA.
