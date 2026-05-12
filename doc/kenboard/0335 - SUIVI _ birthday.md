---
id: 335
status: review
who: Claude
due_date: 
position: 1
created_at: 2026-05-10T18:05:18
updated_at: 2026-05-10T19:29:18
---

# SUIVI / birthday

Mail de rappel anniversaire via sendmail.

---

## Résolution

### Modifications
- **src/jeff/services/birthday_mail.py** — `build_birthday_html()` génère le HTML du mail (nom, date, signe, lien WhatsApp). `send_birthday_mail()` envoie via `sendmail -t`.
- **src/jeff/domain/config.py** — champs `mail_to` et `mail_from` (config .jeff ou env vars)
- **src/jeff/cli.py** — commande `jeff birthday-mail` (`--tomorrow` pour le lendemain). `jeff cron` envoie automatiquement si `mail_to` est configuré.

### Config .jeff
```
mail_to=moi@example.com
mail_from=jeff@example.com
```

### Crontab
```
0 23 * * * cd /path && jeff birthday-mail --tomorrow
0  6 * * * cd /path && jeff birthday-mail
```

### Contenu du mail
- Liste des contacts avec anniversaire
- Signe astrologique
- Lien WhatsApp pré-rempli avec le message d'anniversaire

### Garde-fous
- 100 tests passent
