---
id: 316
status: done
who: Claude
due_date: 
position: 6
created_at: 2026-05-10T08:13:14
updated_at: 2026-05-10T08:54:31
---

# HTML / Anniversaires

Annoncer les anniversaires dans le publish.

---

## Résolution

### Modifications
- **src/jeff/services/publish.py** — détecte les anniversaires du jour (match MM-DD du champ birthday). Passe birthdays + message au template. Chaque contact page sait s'il est birthday.
- **src/jeff/templates/index.html** — section anniversaires en haut du dashboard avec emoji 🎂, date du jour, cartes contact
- **src/jeff/templates/contact.html** — section anniversaire avec le message et bouton "Envoyer par WhatsApp" (lien wa.me pré-rempli avec le message)
- **doc/ui/contact.css** — styles birthday (fond jaune), bouton WhatsApp (vert)

### Message
> Je vois que c'est une journée spéciale pour toi, je te souhaite un joyeux anniversaire et une journée remplie de joies et de belles attentions. 😘🎉🎊🎁🎂🌈

### Comportements obtenus
- La home page affiche les anniversaires du jour en section prioritaire
- La page contact affiche le message + bouton WhatsApp pré-rempli
- Si pas d'anniversaire, rien n'est affiché
- 87 tests passent
