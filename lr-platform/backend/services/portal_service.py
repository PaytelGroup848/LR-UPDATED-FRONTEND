import os
import ntpath
import re
from datetime import datetime
from secrets import token_urlsafe

from bson.objectid import ObjectId
from flask import current_app, has_request_context, request

from backend.models.application import PublishedApp
from backend.models.assignment import ApplicationAssignment
from backend.models.rdp_session import RdpSession
from backend.models.server import Server
from backend.models.user import User
from backend.security.credential_crypto import decrypt_secret
from backend.services.access_policy_service import AccessPolicyService
from backend.services.audit_service import AuditService


def _object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def _id_variants(value) -> list[object]:
    variants: list[object] = [str(value)]
    object_id = _object_id(value)
    if object_id:
        variants.append(object_id)
    return variants


def _session_response(session):
    data = RdpSession.to_dict(session)

    if session.get("server_id"):
        server = Server.get_by_id(session.get("server_id"))
        if server:
            data["server_name"] = server.get("name")

    app_name = data.get("published_app_name")
    if app_name:
        data["app_name"] = app_name
        data["application_name"] = app_name

    return data


def _guacamole_configured():
    return all(
        current_app.config.get(key)
        for key in ("GUACAMOLE_URL", "GUACAMOLE_USER", "GUACAMOLE_PASSWORD")
    )


def _rdp_line(key, value):
    return f"{key}:s:{str(value or '').replace(chr(10), ' ').replace(chr(13), ' ')}"


def _rdp_int_line(key, value):
    return f"{key}:i:{int(value)}"


def _external_base_url():
    forwarded_host = request.headers.get("X-Forwarded-Host")
    forwarded_proto = request.headers.get("X-Forwarded-Proto") or request.scheme
    if forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}".rstrip("/")
    return request.host_url.rstrip("/")


def _display_mode(app):
    if not app:
        return "full_desktop"
    return app.get("display_mode") or (
        "full_desktop" if app.get("launch_mode") == "desktop" else "remote_app"
    )


def _launch_mode(app, display_mode):
    if not app or display_mode == "full_desktop":
        return "desktop"
    if (app.get("remote_app_program") or "").strip():
        return "remote_app"
    if (app.get("initial_program") or app.get("target") or "").strip():
        return "initial_program"
    launch_mode = app.get("launch_mode")
    if launch_mode and launch_mode != "desktop":
        return launch_mode
    return "remote_app"


def _requested_view(data):
    value = str((data or {}).get("view_mode") or (data or {}).get("display_mode") or "").strip().lower()
    if value in {"desktop", "full_desktop", "remote_desktop"}:
        return "full_desktop"
    if value in {"app", "remote_app", "remoteapp", "published_app"}:
        return "remote_app"
    if value in {"web", "web_view", "html5", "browser"}:
        return "html5"
    return None


def _force_html5_gateway(data):
    value = (data or {}).get("force_html5_gateway") or (data or {}).get("use_html5_gateway")
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _ignore_stored_display_mode(data):
    value = (data or {}).get("ignore_stored_display_mode")
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _rdp_identity_for_user(user, server):
    portal_username = (user or {}).get("username") or ""
    windows_username = (user or {}).get("windows_username") or portal_username
    windows_password = decrypt_secret((user or {}).get("windows_password"))
    windows_domain = (
        (user or {}).get("windows_domain")
        or server.get("windows_domain")
        or server.get("domain")
        or server.get("hostname")
        or ""
    )

    if windows_username:
        return {
            "username": windows_username,
            "password": windows_password or "",
            "domain": windows_domain,
            "mode": "per_user_windows_account" if windows_password else "per_user_windows_username",
            "isolated": True,
            "warning": None if windows_password else (
                "Windows password is not stored for this user. The remote desktop client may ask once."
            ),
        }

    return {
        "username": server.get("username") or "",
        "password": decrypt_secret(server.get("password")),
        "domain": server.get("windows_domain") or server.get("domain") or server.get("hostname") or "",
        "mode": "shared_server_credentials",
        "isolated": False,
        "warning": (
            "This launch is using shared server credentials. "
            "Assign a Windows account to the LR user for isolated per-user sessions."
        ),
    }


def _local_windows_domain(username, domain):
    if domain or not username:
        return domain or ""
    if "\\" in username or "@" in username:
        return ""
    return "."


def _rdp_login_name(username, domain):
    if not username:
        return ""
    if "\\" in username or "@" in username:
        return username
    if domain:
        return f"{domain}\\{username}"
    return f".\\{username}"


def _working_directory(program, configured_directory=None):
    value = str(configured_directory or "").strip()
    if value and not value.lower().endswith((".exe", ".bat", ".cmd", ".msi")):
        return value

    program = str(program or "").strip()
    if "\\" in program:
        return ntpath.dirname(program)
    return ""


def _username_leaf(username):
    value = str(username or "").strip()
    if "\\" in value:
        value = value.rsplit("\\", 1)[-1]
    if "@" in value:
        value = value.split("@", 1)[0]
    return value


def _safe_app_name(value):
    name = re.sub(r'[\\/:*?"<>|]+', " ", str(value or "").strip()).strip()
    return re.sub(r"\s+", " ", name) or "Application"


def _published_program_path(app, program, username):
    program = str(program or "").strip()
    if not program:
        return program

    normalized = program.replace("/", "\\")
    match = re.match(r"^C:\\Users\\([^\\]+)\\", normalized, flags=re.IGNORECASE)
    if not match:
        return program

    source_user = match.group(1).lower()
    target_user = _username_leaf(username).lower()
    if source_user == target_user:
        return program

    app_name = _safe_app_name((app or {}).get("name"))
    return ntpath.join(
        r"C:\ProgramData\LRPlatform\PublishedApps",
        app_name,
        ntpath.basename(normalized),
    )


def _folder_program(app, program):
    folder_path = str((app or {}).get("folder_path") or "").strip()
    if not folder_path:
        return program
    return f'explorer.exe "{folder_path}"'


def _session_query(user_id, server, app):
    query = {
        "user_id": {"$in": _id_variants(user_id)},
        "server_id": server.get("_id"),
        "status": {"$in": ["active", "pending"]},
    }
    if app:
        query["published_app_id"] = app.get("_id")
        query["display_mode"] = app.get("display_mode")
    else:
        query["published_app_id"] = None
    return query


class PortalService:

    @staticmethod
    def get_current_user(user):
        data = User.to_dict(user)
        data["is_admin"] = User.is_admin(user)
        return data

    @staticmethod
    def get_home_servers():
        return [Server.to_dict(server) for server in Server.find_active()]

    @staticmethod
    def get_dashboard_data():
        return {
            "stats": PortalService.get_session_stats(None)[0],
            "servers": PortalService.get_home_servers()
        }

    @staticmethod
    def get_portal_servers():
        return {
            "success": True,
            "servers": [Server.to_dict(server) for server in Server.find_active()]
        }, 200

    @staticmethod
    def get_portal_apps(user_id):
        apps = PublishedApp.assigned_to_user(user_id)
        return {
            "success": True,
            "apps": [PublishedApp.to_dict(app) for app in apps]
        }, 200

    @staticmethod
    def launch_app(app_id, user_id, ip_address, user_agent, data=None):
        requested_view = _requested_view(data)
        force_html5_gateway = _force_html5_gateway(data)
        ignore_stored_display_mode = _ignore_stored_display_mode(data)
        allowed, reason, app = AccessPolicyService.can_launch_app(user_id, app_id)
        if not allowed:
            AuditService.log(
                "session.launch_app.denied",
                user_id=user_id,
                category="session",
                ip_address=ip_address,
                success=False,
                reason=reason,
                metadata={"app_id": str(app_id)},
            )
            return {"success": False, "error": reason}, 403 if app else 404

        if app is None:
            return {"success": False, "error": "Application not found"}, 404

        server = Server.get_by_id(app.get("server_id"))
        if server is None:
            return {"success": False, "error": "Assigned server is not available"}, 404

        launch_data = PortalService._create_launch_session(
            user_id=user_id,
            server=server,
            app=app,
            ip_address=ip_address,
            user_agent=user_agent,
            requested_view=requested_view,
            force_html5_gateway=force_html5_gateway,
            ignore_stored_display_mode=ignore_stored_display_mode,
        )
        return launch_data

    @staticmethod
    def launch_remote_app(app_id, user_id, ip_address, user_agent):
        """Launch an assigned published RemoteApp without any desktop fallback."""
        allowed, reason, app = AccessPolicyService.can_launch_app(user_id, app_id)
        if not allowed:
            return {"success": False, "error": reason}, 403 if app else 404

        item_type = str(app.get("item_type") or "").strip().lower()
        remote_app_program = str(app.get("remote_app_program") or "").strip()
        if item_type in {"desktop", "folder"}:
            return {"success": False, "error": "Selected resource is not a published RemoteApp"}, 400
        if not remote_app_program:
            return {
                "success": False,
                "error": "Published application is missing its RemoteApp program",
            }, 400

        server = Server.get_by_id(app.get("server_id"))
        if server is None or server.get("is_active") is False:
            return {"success": False, "error": "Assigned server is not available"}, 404

        return PortalService._create_launch_session(
            user_id=user_id,
            server=server,
            app=app,
            ip_address=ip_address,
            user_agent=user_agent,
            requested_view="remote_app",
            force_html5_gateway=True,
            ignore_stored_display_mode=True,
            require_remote_app=True,
        )

    @staticmethod
    def launch_server(data, user_id, ip_address, user_agent):
        server_id = data.get("server_id")
        requested_view = _requested_view(data)
        user = User.get_by_id(user_id)
        allowed, reason, server = AccessPolicyService.can_launch_server(user, server_id)
        if not allowed:
            AuditService.log(
                "session.launch_server.denied",
                user=user,
                user_id=user_id,
                category="session",
                server_id=server_id,
                ip_address=ip_address,
                success=False,
                reason=reason,
            )
            return {"success": False, "error": reason}, 403 if server else 404

        if server is None:
            return {"success": False, "error": "Server not found"}, 404

        return PortalService._create_launch_session(
            user_id=user_id,
            server=server,
            app=None,
            ip_address=ip_address,
            user_agent=user_agent,
            requested_view=requested_view,
        )

    @staticmethod
    def _create_launch_session(
        user_id,
        server,
        app,
        ip_address,
        user_agent,
        requested_view=None,
        force_html5_gateway=False,
        ignore_stored_display_mode=False,
        require_remote_app=False,
    ):
        user = User.get_by_id(user_id)
        display_mode = requested_view or (None if ignore_stored_display_mode else _display_mode(app))
        display_mode = (display_mode or "remote_app") if app else (display_mode or "full_desktop")
        launch_mode = _launch_mode(app, display_mode)
        launch_app = dict(app, display_mode=display_mode, launch_mode=launch_mode) if app else None
        use_html5_gateway = force_html5_gateway or display_mode == "html5"

        rdp_identity = _rdp_identity_for_user(user, server)
        connection_id = None
        launch_url = None
        guac_token = None
        warning = rdp_identity.get("warning")

        if use_html5_gateway and _guacamole_configured():
            try:
                from backend.manager.guacamole_manager import get_guac_client

                client = get_guac_client()
                connection_name = str(
                    (launch_app.get("name") if launch_app else server.get("name"))
                    or "LR Remote Session"
                )
                connection_host = str(server.get("host") or server.get("ip_address") or "")
                result = client.create_rdp_connection(
                    name=connection_name,
                    host=connection_host,
                    port=int(server.get("port") or 3389),
                    rdp_username=rdp_identity.get("username") or "",
                    rdp_password=rdp_identity.get("password") or "",
                    domain=_local_windows_domain(
                        rdp_identity.get("username"),
                        rdp_identity.get("domain"),
                    ),
                    app=launch_app,
                    require_remote_app=require_remote_app,
                )
                if result.get("success"):
                    connection_id = result.get("connection_id")
                    launch_url = result.get("client_url")
                    guac_token = result.get("token")
                else:
                    warning = result.get("error") or "Remote desktop gateway did not create a connection"
            except Exception as error:
                warning = str(error)
        elif use_html5_gateway:
            warning = "Remote desktop gateway is not configured"

        if require_remote_app and not launch_url:
            return {
                "success": False,
                "error": warning or "RemoteApp connection could not be created",
            }, 502

        session = RdpSession.create({
            "user_id": _object_id(user_id) or user_id,
            "server_id": server.get("_id"),
            "published_app_id": launch_app.get("_id") if launch_app else None,
            "guac_token": guac_token,
            "guac_connection_id": connection_id,
            "launch_url": launch_url,
            "reconnect_token": token_urlsafe(24),
            "connection_type": display_mode,
            "display_mode": display_mode,
            "launch_mode": launch_mode,
            "windows_username": rdp_identity.get("username"),
            "windows_domain": rdp_identity.get("domain"),
            "session_isolation": rdp_identity.get("mode"),
            "is_isolated_session": rdp_identity.get("isolated"),
            "status": "active" if connection_id else "pending",
            "ip_address": ip_address,
            "user_agent": user_agent,
            "client_fingerprint": (
                request.headers.get("X-Client-Fingerprint")
                if has_request_context()
                else None
            ),
        })
        session_id = str(session.get("_id"))

        response = {
            "success": True,
            "message": (
                "Launch request created"
                if connection_id
                else "Downloading remote desktop file"
                if not use_html5_gateway
                else warning
            ),
            "session": _session_response(session),
            "connection_id": connection_id,
            "launch_url": launch_url,
            "session_id": session_id,
            "display_mode": display_mode,
            "launch_mode": launch_mode,
            "launch_transport": "html5" if launch_url else "rdp_file" if not use_html5_gateway else None,
            "session_isolation": rdp_identity.get("mode"),
            "is_isolated_session": rdp_identity.get("isolated"),
        }
        if not use_html5_gateway:
            response["rdp_file_url"] = (
                f"{_external_base_url()}/portal/api/sessions/{session.get('_id')}/rdp-file"
            )
        if warning:
            response["warning"] = warning
            response["setup_required"] = not _guacamole_configured()

        AuditService.log(
            "session.launch.created",
            user_id=user_id,
            category="session",
            server_id=server.get("_id"),
            session_id=session_id,
            ip_address=ip_address,
            success=True,
            metadata={
                "app_id": str(launch_app.get("_id")) if launch_app else None,
                "display_mode": display_mode,
                "session_isolation": rdp_identity.get("mode"),
                "transport": response.get("launch_transport"),
                "warning": warning,
            },
        )
        return response, 200

    @staticmethod
    def reconnect_session(session_id, user, ip_address, user_agent):
        allowed, reason, session = AccessPolicyService.can_reconnect_session(user, session_id)
        if not allowed:
            AuditService.log(
                "session.reconnect.denied",
                user=user,
                category="session",
                session_id=session_id,
                ip_address=ip_address,
                success=False,
                reason=reason,
            )
            return {"success": False, "error": reason}, 403 if session else 404

        if session is None:
            return {"success": False, "error": "Session not found"}, 404

        RdpSession.collection.update_one(
            {"_id": session["_id"]},
            {
                "$set": {
                    "last_seen_at": datetime.utcnow(),
                    "reconnected_at": datetime.utcnow(),
                    "reconnect_user_agent": user_agent,
                    "reconnect_ip_address": ip_address,
                }
            }
        )
        launch_url = session.get("launch_url")
        if session.get("guac_connection_id"):
            from backend.manager.guacamole_manager import get_guac_client

            client = get_guac_client()
            guac_token = client.get_admin_token()
            if guac_token:
                RdpSession.collection.update_one(
                    {"_id": session["_id"]},
                    {"$set": {"guac_token": guac_token}},
                )
                launch_url = client.build_client_url(
                    str(session.get("guac_connection_id")),
                    guac_token,
                )
        response = {
            "success": True,
            "message": "Session recovered",
            "session": _session_response(session),
            "session_id": str(session.get("_id")),
            "launch_url": launch_url,
            "launch_transport": "html5" if launch_url else "rdp_file",
            "session_isolation": session.get("session_isolation"),
            "is_isolated_session": bool(session.get("is_isolated_session")),
        }
        if not launch_url:
            response["rdp_file_url"] = (
                f"{_external_base_url()}/portal/api/sessions/{session.get('_id')}/rdp-file"
            )

        AuditService.log(
            "session.reconnect.success",
            user=user,
            category="session",
            server_id=session.get("server_id"),
            session_id=str(session.get("_id")),
            ip_address=ip_address,
            success=True,
        )
        return response, 200

    @staticmethod
    def get_rdp_file(session_id, user_id):
        session_object_id = _object_id(session_id)
        if not session_object_id:
            return None, "Session not found", 404

        session = RdpSession.collection.find_one({
            "_id": session_object_id,
            "user_id": {"$in": _id_variants(user_id)},
        })
        if not session:
            return None, "Session not found", 404

        server = Server.get_by_id(session.get("server_id"))
        if not server:
            return None, "Server not found", 404

        app = None
        if session.get("published_app_id"):
            app = PublishedApp.get_by_id(session.get("published_app_id"))

        host = server.get("host") or server.get("ip_address")
        port = int(server.get("port") or 3389)
        address = f"{host}:{port}" if port != 3389 else host
        username = session.get("windows_username") or server.get("username")
        domain = (
            session.get("windows_domain")
            or server.get("windows_domain")
            or server.get("domain")
            or server.get("hostname")
        )
        rdp_username = _rdp_login_name(username, domain)
        lines = [
            "screen mode id:i:2",
            "use multimon:i:0",
            "desktopwidth:i:1280",
            "desktopheight:i:800",
            "session bpp:i:32",
            "compression:i:1",
            "keyboardhook:i:2",
            "audiomode:i:0",
            "redirectclipboard:i:1",
            "redirectprinters:i:0",
            "administrative session:i:0",
            "disableconnectionsharing:i:1",
            "prompt for credentials:i:1",
            "promptcredentialonce:i:0",
            "enablecredsspsupport:i:1",
            "authentication level:i:2",
            _rdp_line("full address", address),
            _rdp_line("username", rdp_username),
        ]

        if app:
            display_mode = session.get("display_mode") or _display_mode(app)
            launch_mode = _launch_mode(app, display_mode)
            if display_mode != "full_desktop":
                remote_app_program = (app.get("remote_app_program") or "").strip()
                initial_program = (app.get("initial_program") or remote_app_program or app.get("target") or "").strip()

                if launch_mode == "remote_app" and remote_app_program.startswith("||"):
                    lines.extend([
                        _rdp_int_line("remoteapplicationmode", 1),
                        _rdp_line("remoteapplicationprogram", remote_app_program),
                        _rdp_line("remoteapplicationname", app.get("name")),
                        _rdp_line("remoteapplicationcmdline", app.get("arguments")),
                    ])
                elif initial_program:
                    initial_program = _published_program_path(app, initial_program, username)
                    initial_program = _folder_program(app, initial_program)
                    lines.extend([
                        _rdp_line("alternate shell", initial_program),
                        _rdp_line("shell working directory", _working_directory(
                            initial_program,
                            app.get("working_directory"),
                        )),
                    ])

        filename = f"{(app or server).get('name', 'lr-remote')}.rdp"
        safe_filename = "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)
        content = "\r\n".join(lines) + "\r\n"
        return {
            "content": content,
            "filename": safe_filename,
        }, None, 200

    @staticmethod
    def get_my_sessions(user_id):
        sessions = list(
            RdpSession.collection.find({"user_id": {"$in": _id_variants(user_id)}})
            .sort("started_at", -1)
        )
        return {
            "success": True,
            "sessions": [_session_response(session) for session in sessions]
        }, 200

    @staticmethod
    def get_session_stats(user_id):
        filter_query = {}
        if user_id:
            filter_query["user_id"] = {"$in": _id_variants(user_id)}

        active_query = dict(filter_query)
        active_query["status"] = "active"

        return {
            "success": True,
            "active": RdpSession.collection.count_documents(active_query),
            "total": RdpSession.collection.count_documents(filter_query)
        }, 200

    @staticmethod
    def get_client_exe_path():
        return os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "static",
                "client",
                "lr_remote_access_client.exe",
            )
        )

    @staticmethod
    def get_admin_panel_exe_path():
        return os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "static",
                "admin",
                "Admin Panel.exe",
            )
        )
