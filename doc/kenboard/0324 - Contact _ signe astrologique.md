---
id: 324
status: done
who: Claude
due_date: 
position: 1
created_at: 2026-05-10T09:15:36
updated_at: 2026-05-10T13:05:31
---

# Contact / signe astrologique

Ajouter le signe astrologique depuis la date d'anniversaire.

---

## Résolution

### Modifications
- **src/jeff/domain/transform.py** — fonction `zodiac_sign(month, day)` → (nom, emoji). Appelée dans `parse_vcard` quand birthday est présent. Champ `signe` dans les scalars du frontmatter.
- **src/jeff/services/publish.py** — calcul du signe au publish pour les .md existants sans le champ
- **src/jeff/templates/contact.html** — affichage `♓ Poissons` à côté de la date d'anniversaire

### Exemple
```yaml
birthday: 1985-03-15
signe: "♓ Poissons"
```

### Garde-fous
- 90 tests passent
- Tous les 12 signes vérifiés
