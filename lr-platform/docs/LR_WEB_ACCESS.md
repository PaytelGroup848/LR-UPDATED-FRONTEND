# LR Web Access Launcher

LR Web Access is the branded remote-app view layered over Apache Guacamole. Guacamole remains the RDP/HTML5 engine; users see the LR floating launcher at `/web-access`.

## APIs

- `GET /api/lr/my-resources`
  - Returns only resources assigned to the logged-in user.
  - Splits records into `applications` and `folders`.
  - Does not return executable paths or Windows folder paths.

- `POST /api/lr/launch`
  - Body: `{ "resource_id": "...", "type": "application" | "folder" }`
  - Validates the current user and assignment through the existing portal launch policy.
  - Forces `view_mode=html5` so the Guacamole session can be embedded behind the LR launcher.

## Frontend

- `/web-access` loads the floating launcher and Guacamole iframe.
- `/web-access?resource_id=<id>&type=application` auto-launches one assigned app.
- `/web-access?resource_id=<id>&type=folder` auto-launches one assigned folder.
- Existing portal Remote App mode opens this branded web-access view. Desktop/Web modes keep their previous behavior.

## Configure Apps And Folders

Use the existing admin software and assign-folder screens. Each published item must have:

- `server_id`
- `name`
- For applications: `initial_program` or `remote_app_program`
- For folders: `item_type=folder`, `folder_path`, `initial_program=explorer.exe`

The browser receives only `id`, `name`, `icon`, and `type`. The backend maps `id` to the approved path.

## Example Seed

Set these variables, then run the seed module inside the backend environment:

```powershell
$env:LR_SEED_USER_ID = "<existing-user-object-id>"
$env:LR_SEED_SERVER_ID = "<existing-server-object-id>"
$env:LR_SEED_BUSY_PATH = "C:\BusyWin\Busy21.exe"
$env:LR_SEED_FOLDER_PATH = "C:\Users\Public\Desktop"
python -m backend.database.seeders.seed_lr_resources
```

This creates and assigns:

- Busy 21
- Desktop Folder
