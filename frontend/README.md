# LR Remote Access Frontend

This folder is the split Next.js frontend version of the pasted admin HTML.

## Run

```bash
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` if your backend is on a different host:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000 npm run dev
```

If the backend serves the frontend on the same domain, no env value is needed.

## Structure

- `app/` contains the pages requested: login/register, user portal, dashboard, users, applications, assignments, sessions, monitoring, logs, licensing, settings.
- `components/` contains layout, UI, table, form, chart, modal, and license pieces.
- `services/` contains API calls split by domain.
- `types/`, `utils/`, `hooks/`, `store/`, and `lib/` hold shared frontend code.

## Main Routes

- `/login` - combined login/register screen
- `/portal` - user portal with assigned app launcher, server launcher, sessions, and download client link
- `/dashboard` - admin dashboard
