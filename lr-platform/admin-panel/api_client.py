import requests
from urllib.parse import urljoin


def _dict_or_empty(value):
    return value if isinstance(value, dict) else {}


class AdminApiClient:
    # Talks to the FastAPI backend on behalf of the LR Admin Panel.

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def _headers(self):
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def login(self, username: str, password: str) -> None:
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if response.status_code >= 400:
            raise ValueError("Invalid username or password")

        self.token = response.json()["access_token"]

    # ---------------- Users / Roles ----------------

    def get_users(self):
        response = requests.get(
            f"{self.base_url}/users/",
            headers=self._headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_roles(self):
        response = requests.get(
            f"{self.base_url}/roles/",
            headers=self._headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    # ---------------- License / Product keys ----------------

    def list_product_keys(self):
        response = requests.get(
            f"{self.base_url}/license/admin/keys",
            headers=self._headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def create_product_keys(
        self,
        plan_name: str,
        max_activations: int,
        valid_days: int,
        issued_to: str | None,
        quantity: int
    ):
        response = requests.post(
            f"{self.base_url}/license/admin/keys",
            headers=self._headers(),
            json={
                "plan_name": plan_name,
                "max_activations": max_activations,
                "valid_days": valid_days,
                "issued_to": issued_to,
                "quantity": quantity
            },
            timeout=10
        )
        if response.status_code >= 400:
            raise ValueError(response.json().get("detail", "Failed"))
        return response.json()

    def revoke_product_key(self, key_code: str):
        response = requests.post(
            f"{self.base_url}/license/admin/keys/{key_code}/revoke",
            headers=self._headers(),
            timeout=10
        )
        if response.status_code >= 400:
            raise ValueError(response.json().get("detail", "Failed"))
        return response.json()


class LicenseApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.user: dict | None = None

    def login(self, username, password):
        response = self.session.post(
            f"{self.base_url}/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code >= 400:
            raise ValueError("Invalid username or password")

        data = response.json()
        self.user = _dict_or_empty(data.get("user"))
        role = str(self.user.get("role") or "").upper().replace(" ", "_")
        if role not in {"ADMIN", "SUPER_ADMIN"}:
            self.user = None
            raise ValueError(ADMIN_REQUIRED_MESSAGE)

    def logout(self):
        try:
            self.session.post(f"{self.base_url}/logout", json={}, timeout=10)
        finally:
            self.user = None

    def list_product_keys(self):
        return self._request("GET", "/license/admin/keys")

    def create_product_keys(self, plan_name, max_activations, valid_days, issued_to, quantity):
        return self._request("POST", "/license/admin/keys", json={
            "plan_name": plan_name,
            "max_activations": max_activations,
            "valid_days": valid_days,
            "issued_to": issued_to,
            "quantity": quantity,
        })

    def revoke_product_key(self, key_code):
        return self._request("POST", f"/license/admin/keys/{key_code}/revoke")

    def _request(self, method, path, **kwargs):
        url = urljoin(self.base_url + '/', path.lstrip('/'))
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
        except requests.RequestException as error:
            raise ApiError(f'Connection failed: {error}') from error

        content_type = response.headers.get('content-type', '')
        data = response.json() if 'application/json' in content_type else {'message': response.text.strip()}
        if response.status_code >= 400:
            raise ApiError(data.get('error') or data.get('message') or f'HTTP {response.status_code}')
        return data



class ApiError(Exception):
    pass


MICROSERVICE_GATEWAY_MESSAGE = (
    "Backend URL is pointing to the old microservice API gateway without "
    "the web backend proxy. Start the current gateway/web-backend stack, or "
    "set Backend URL to the Flask backend port."
)
ADMIN_REQUIRED_MESSAGE = (
    "Login successful, but this account is not an admin. "
    "Use an ADMIN/SUPER_ADMIN account for the admin panel."
)


class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.user: dict | None = None

    def set_base_url(self, base_url):
        self.base_url = base_url.rstrip('/')

    def login(self, username, password, token=None):
        self._ensure_compatible_backend()
        payload = {'username': username, 'password': password}
        if token:
            payload['token'] = token
        data = self.post('/login', payload)
        self.user = _dict_or_empty(data.get('user') if isinstance(data, dict) else None)
        role = str(self.user.get('role') or '').upper().replace(' ', '_')
        if role not in {'ADMIN', 'SUPER_ADMIN'}:
            self.user = None
            raise ApiError(ADMIN_REQUIRED_MESSAGE)
        return data

    def logout(self):
        try:
            return self.post('/logout', {})
        finally:
            self.user = None

    def health(self):
        self._ensure_compatible_backend()
        return self.get('/api/health')

    def monitoring(self):
        return self.get('/api/monitoring')

    def users(self, limit=500, offset=0, search=None):
        query = f'?limit={int(limit)}&offset={int(offset)}'
        if search:
            query += f'&q={search}'
        return self.get(f'/users{query}').get('users', [])

    def create_user(self, payload):
        return self.post('/users', payload)

    def update_user(self, user_id, payload):
        return self.patch(f'/users/{user_id}', payload)

    def delete_user(self, user_id):
        return self.delete(f'/users/{user_id}')

    def servers(self):
        data = self.get('/servers')
        return data if isinstance(data, list) else data.get('servers', [])

    def apps(self):
        return self.get('/api/apps').get('apps', [])

    def create_app(self, payload):
        return self.post('/api/apps', payload)

    def update_app(self, app_id, payload):
        return self.patch(f'/api/apps/{app_id}', payload)

    def delete_app(self, app_id):
        return self.delete(f'/api/apps/{app_id}')

    def assignments_for_user(self, user_id):
        return self.get(f'/api/apps/assignments/user/{user_id}')

    def user_policy(self, user_id):
        return self.get(f'/api/user-policies/{user_id}')

    def save_user_policy(self, user_id, policy):
        return self.post(f'/api/user-policies/{user_id}', {'policy': policy})

    def login_links(self, user_id=None, limit=100):
        query = f'?limit={int(limit)}'
        if user_id:
            query += f'&user_id={user_id}'
        data = self.get(f'/api/login-links{query}')
        return data.get('links', []) if isinstance(data, dict) else []

    def assign_app(self, app_id, user_id, enabled=True):
        return self.post(f'/api/apps/{app_id}/assign', {'user_id': user_id, 'is_enabled': enabled})

    def unassign_app(self, app_id, user_id):
        return self.delete(f'/api/apps/{app_id}/assign/{user_id}')

    def generate_url(self, user_id=None, expires_minutes=60, one_time=True):
        return self.post('/api/generate-url', {
            'user_id': user_id,
            'expires_minutes': expires_minutes,
            'one_time': one_time,
        })

    def sessions(self, user_id=None, status=None, limit=None):
        params = []
        if user_id:
            params.append(f'user_id={user_id}')
        if status:
            params.append(f'status={status}')
        if limit:
            params.append(f'limit={int(limit)}')
        query = '?' + '&'.join(params) if params else ''
        return self.get(f'/api/sessions/{query}').get('sessions', [])

    def session_stats(self):
        return self.get('/api/sessions/stats')

    def agents(self, username=None):
        query = f'?username={username}' if username else ''
        data = self.get(f'/agents{query}')
        return data if isinstance(data, list) else data.get('agents', [])

    def streams(self):
        data = self.get('/api/streams')
        streams = data.get('streams', []) if isinstance(data, dict) else data
        if isinstance(streams, dict):
            streams = streams.get('items', [])
        return streams if isinstance(streams, list) else []

    def error_logs(self, limit=100):
        data = self.get(f'/api/error-logs?limit={int(limit)}')
        errors = data.get('errors', []) if isinstance(data, dict) else data
        return errors if isinstance(errors, list) else []

    def logs(self, limit=100, user_id=None):
        query = f'?limit={int(limit)}'
        if user_id:
            query += f'&user_id={user_id}'
        data = self.get(f'/logs{query}')
        logs = data.get('logs', []) if isinstance(data, dict) else data
        return logs if isinstance(logs, list) else []

    def get(self, path):
        return self._request('GET', path)

    def post(self, path, payload=None):
        return self._request('POST', path, json=payload or {})

    def patch(self, path, payload=None):
        return self._request('PATCH', path, json=payload or {})

    def delete(self, path):
        return self._request('DELETE', path)

    def _request(self, method, path, **kwargs):
        url = urljoin(self.base_url + '/', path.lstrip('/'))
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
        except requests.RequestException as error:
            message = str(error)
            if 'user-service' in message or 'auth-service' in message or 'license-service' in message:
                raise ApiError(MICROSERVICE_GATEWAY_MESSAGE) from error
            raise ApiError(f'Connection failed: {error}') from error

        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            data = response.json()
        else:
            data = {'message': response.text.strip()}

        if response.status_code >= 400:
            message = data.get('error') or data.get('message') or f'HTTP {response.status_code}'
            if message == 'Service route not found':
                raise ApiError(MICROSERVICE_GATEWAY_MESSAGE)
            raise ApiError(message)
        return data

    def _ensure_compatible_backend(self):
        health_url = urljoin(self.base_url + '/', 'health')
        try:
            response = self.session.get(health_url, timeout=5)
        except requests.RequestException:
            return

        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            return

        try:
            data = response.json()
        except ValueError:
            return

        services = data.get('services')
        if (
            isinstance(services, dict)
            and {'auth', 'user', 'license'}.issubset(services)
            and 'web_backend' not in services
        ):
            raise ApiError(MICROSERVICE_GATEWAY_MESSAGE)
