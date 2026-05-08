---
id: 288
status: done
who: Claude
due_date: 
position: 2
created_at: 2026-05-08T23:42:53
updated_at: 2026-05-08T23:48:48
---

# CLI / Verbose

Add verbose to jeff sync and jeff publish

---

## Resolution

Flag --verbose / -v ajoute au groupe CLI principal :

```
jeff --verbose sync
jeff -v publish
```

Bascule le logger de WARNING → DEBUG. Tous les modules (carddav, transform, publish) emettent des logs DEBUG sur stderr. La sortie normale (stdout) reste inchangee.
