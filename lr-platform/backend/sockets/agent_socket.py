from typing import Any, cast

from flask import request
from backend.extensions import socketio
from backend.manager.agent_manager import register_agent, set_offline, update_heartbeat
from backend.manager.logger import get_logger
from backend.manager.stream_manager import remove_sid

connected_agents = {}
logger = get_logger(__name__)


def _request_sid():
    return str(getattr(cast(Any, request), 'sid', ''))


def get_agent_sid(agent_id):
    for sid, info in connected_agents.items():
        if info.get("agent_id") == agent_id:
            return sid
    return None


def register_socket_events(socketio_instance=None):
    """Import hook used by sockets.socket_handler.

    The event handlers in this module are registered by the decorators below
    when the module is imported.
    """
    return None

@socketio.on("agent_connect", namespace='/agent')
def handle_agent_connect(data):
    data = data or {}
    agent_id = data.get("agent_id")
    if agent_id:
        register_agent(
            agent_id=agent_id,
            hostname=data.get("hostname"),
            ip_address=data.get("ip_address"),
            username=data.get("username"),
            os=data.get("os"),
            cpu=data.get("cpu"),
            ram=data.get("ram")
        )
        connected_agents[_request_sid()] = {
            "agent_id": agent_id,
            "hostname": data.get("hostname"),
            "ip_address": data.get("ip_address"),
            "username": data.get("username"),
            "os": data.get("os"),
            "cpu": data.get("cpu"),
            "ram": data.get("ram"),
            "status": "online"
        }
        logger.info("Agent connected: %s", agent_id)
        try:
            from backend.services.desktop_shortcut_service import DesktopShortcutService

            socketio.start_background_task(
                DesktopShortcutService.sync_pending_for_agent,
                _request_sid(),
            )
        except Exception as error:
            logger.warning("Pending desktop shortcut sync did not start: %s", error)
        return {"success": True, "agent_id": agent_id}
    else:
        logger.warning("Agent connected without an ID")
        return {"success": False, "message": "agent_id is required"}

@socketio.on("disconnect", namespace='/agent')
def handle_agent_disconnect():
    sid = _request_sid()
    agent_info = connected_agents.pop(sid, None)
    for agent_id in remove_sid(sid):
        logger.info("Stream closed: %s", agent_id)
    if agent_info:
        set_offline(agent_info["agent_id"])
        logger.info("Agent disconnected: %s", agent_info["agent_id"])
    else:
        logger.warning("Agent disconnected without a known ID")

@socketio.on("heartbeat", namespace='/agent')
def handle_heartbeat(data):
    data = data or {}
    agent_id = data.get("agent_id")
    if not agent_id:
        return
    update_heartbeat(agent_id)
    for sid, info in connected_agents.items():
        if info["agent_id"] == agent_id:
            connected_agents[sid]["status"] = "online"
            logger.debug("Heartbeat received from %s", agent_id)
            break
