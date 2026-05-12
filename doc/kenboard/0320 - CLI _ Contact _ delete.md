---
id: 320
status: done
who: Claude
due_date: 
position: 3
created_at: 2026-05-10T08:28:52
updated_at: 2026-05-10T13:05:29
---

# CLI / Contact / delete

jeff delete propose de supprimer les contacts archivés.

---

## Résolution

### Logique
Seuls les contacts `status: archivé` sont proposés — les contacts actifs ont déjà été triés et sont d'actualité.

### Usage
```sh
jeff delete
```
```
355 archived contacts
d=delete  Enter=skip  q=quit

  [1/355] Jean Dupont (ski) — ancien collègue
  > d
    ✗ marked for deletion
  [2/355] Marie Martin (cafe)
  >
...
1 contacts marked for deletion:
  ✗ Jean Dupont

Confirm? (y/n): y
1 contact(s) marked as 'supprimé'.
```
