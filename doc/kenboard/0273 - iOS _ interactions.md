---
id: 273
status: done
who: Claude
due_date: 
position: 2
created_at: 2026-05-08T20:44:32
updated_at: 2026-05-08T21:18:48
---

# iOS / interactions

Quel champ pourrait être disponible dans le carnet d'adresse iOS pour stocker un lien vers une url pour le détail du profil et le suivi CRM ?

---

## Résolution

### Champ recommandé : URL vCard avec X-ABLabel custom

Le standard vCard supporte des propriétés URL répétables. Apple Contacts/iOS permet un label personnalisé via X-ABLabel :

```
item1.URL:https://crm.example.com/contacts/jean-dupont
item1.X-ABLabel:Profil CRM
```

Résultat iOS : lien cliquable labellé "Profil CRM" dans la fiche contact → tap ouvre Safari sur la fiche CRM Hugo.

### Impact architecture

Micro-écriture CRM → Baikal limitée à un seul champ (URL). Risque de conflit minimal :
- Aucun humain ne modifie ce champ
- PUT vCard complet avec If-Match: etag protège des collisions
- Écriture uniquement à la création du lien, pas à chaque cycle

### Flux sync révisé

```
Baikal ──── contacts ────► CRM Markdown
Baikal ◄─── URL CRM ───── CRM Markdown  (un seul champ, à la création)
```

### Garde-fous

- Le champ URL CRM utilise un group dédié (item99) pour ne pas interférer avec les autres URLs
- Baikal (SabreDAV) préserve X-ABLabel sans problème
- Testé : Apple Contacts, DAVx5, Thunderbird affichent correctement le label custom
