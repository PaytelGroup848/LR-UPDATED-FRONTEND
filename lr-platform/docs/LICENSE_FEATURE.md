# LR Admin Panel + Product Key Licensing - kya add hua

## 1. Backend (FastAPI) - naya "License" module
- `backend/models/license.py` -> `ProductKey`, `LicenseActivation`, `TrialSession`
- `backend/schemas/license.py`, `backend/repositories/license_repository.py`,
  `backend/services/license_service.py`, `backend/api/routers/license_router.py`
- `backend/migrations/versions/..._license_tables.py` -> naye 3 tables ki migration
- Naye endpoints:
  - Admin (login required, ADMIN/SUPER_ADMIN role): 
    `POST /license/admin/keys`, `GET /license/admin/keys`,
    `POST /license/admin/keys/{key_code}/revoke`
  - Device-facing (no login, device_id se identify):
    `POST /license/trial/start`, `GET /license/status/{device_id}`,
    `POST /license/activate`, `POST /license/hold`

Run after pulling: `alembic upgrade head` (backend folder me, `.env` me
`DATABASE_URL` set hone ke baad).

## 2. Business logic (jo aapne bataya)
- Naya device pehli baar connect kare to 7 din ka free trial auto-start.
- Trial chalu rehte app/website pura kaam karta hai.
- Trial khatam hote hi, jo bhi kaam chal raha tha uska "context" backend
  me save ho jata hai (`hold` call) - phir floating panel key maangta hai.
- Sahi product key dalne par activation ho jata hai aur wahi context
  wapas milta hai, taaki kaam wahi se resume ho jahan rुka tha.

## 3. Desktop client / Agent - floating panel
- `agent/license/key_window.py` -> `ProductKeyPanel` (PyQt5), always-on-top
  chhota floating window.
- `agent/license/license_client.py`, `agent/license/device_id.py`
- `agent/main.py` me wire kar diya hai - isko run karne se panel dikhega.
- Real session resume ke liye `get_current_work_context()` aur
  `resume_work()` (in `agent/main.py`) ko `agent/sessions/` ke actual
  session-tracking se jodna hoga jab woh module banoge.

## 4. Web (URL se access)
- `frontend/services/license.service.ts`, `frontend/hooks/useLicense.ts`
- `frontend/components/license/ProductKeyFloatingPanel.tsx`
- Use karne ke liye kisi bhi page/layout me:
  ```tsx
  import ProductKeyFloatingPanel from "@/components/license/ProductKeyFloatingPanel";
  // ...
  <ProductKeyFloatingPanel />
  ```
- `.env.local` me `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` set karein.

## 5. LR Admin Panel (naya desktop app) - "Folder.exe"
- Naya folder: `admin-panel/` (PyQt5 app) - Login -> Dashboard (Users tab +
  Product Keys tab: generate/list/revoke keys).
- Run karne ke liye: `pip install -r admin-panel/requirements.txt` phir
  `python admin-panel/main.py`
- **Exe banane ke liye**:
  ```bash
  python installer/build/build_admin_panel.py
  ```
  Output: `backend/static/admin/Admin Panel.exe`
  Yehi file web admin panel ke **Download Admin Panel** button se download hoti hai.
- Agent ko bhi waise hi exe folder me build karne ke liye:
  `python installer/build/build_agent.py` -> `installer/build/output/LR_Agent/`

## 6. Aage kya karna baaki hai
- `installer/resources/lr_admin_panel.ico` aur `lr_agent.ico` daal dena
  apna logo/icon (abhi optional rakha hai, agar file nahi mili to bina
  icon ke build ho jayega).
- Backend `.env` me `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`,
  `ACCESS_TOKEN_EXPIRE_MINUTES` set karna (existing config ke hisab se).
- Admin Panel aur Agent ke `BACKEND_BASE_URL` ko production URL se replace
  karna jab deploy karein (abhi `http://localhost:8000` hardcoded hai
  testing ke liye).
