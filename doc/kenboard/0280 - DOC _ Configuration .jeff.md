---
id: 280
status: done
who: Claude
due_date: 
position: 5
created_at: 2026-05-08T23:08:14
updated_at: 2026-05-08T23:08:30
---

# DOC / Configuration .jeff

Documenter la configuration de l'application jeff.

Fichier .jeff a la racine du projet (key=value, # comments, chmod 600, gitignore).

Champs :
- carddav_url : URL de l'addressbook CardDAV (ex: https://host/dav.php/addressbooks/user/default/)
- carddav_username : utilisateur Baikal
- carddav_password : mot de passe Baikal
- sync_state_path : chemin du fichier d'etat de sync (defaut: .sync-state.json)
- content_dir : dossier de sortie des fichiers Markdown (defaut: content/contacts)
- photo_dir : dossier de sortie des photos (defaut: static/photos)

Override possible via env vars JEFF_CARDDAV_URL, JEFF_CARDDAV_USERNAME, JEFF_CARDDAV_PASSWORD, etc.

Priorite : env vars > .jeff > defaults.

Securite : le fichier contient des credentials, chmod 600, ne jamais commiter.
