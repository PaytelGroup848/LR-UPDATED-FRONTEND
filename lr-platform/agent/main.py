import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, cast

import socketio

AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_project_env():
    for env_path in (PROJECT_ROOT / ".env", AGENT_DIR / ".env"):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_project_env()

try:
    from agent.services.keyboard_control import KeyboardControl
    from agent.services.mouse_control import MouseControl
    from agent.services.screen_agent import ScreenAgent
    from agent.services.system_info import get_system_info
    from agent.services.desktop_shortcut import create_desktop_shortcut, delete_desktop_shortcut
    from agent.services.windows_account import create_windows_user
    from agent.services.policy_enforcer import apply_policy
except ImportError:
    from services.keyboard_control import KeyboardControl
    from services.mouse_control import MouseControl
    from services.screen_agent import ScreenAgent
    from services.system_info import get_system_info
    from services.desktop_shortcut import create_desktop_shortcut, delete_desktop_shortcut
    from services.windows_account import create_windows_user
    from services.policy_enforcer import apply_policy


SERVER_URL = (
    os.getenv('LIVEPANEL_SERVER_URL')
    or os.getenv('LR_SERVER_URL')
    or 'http://localhost:8004'
)
NAMESPACE = '/agent'

sio = cast(Any, socketio.Client())
system_info = get_system_info()
agent_id = system_info['agent_id']
screen_stream = ScreenAgent(sio, agent_id)
mouse_control = MouseControl()
keyboard_control = KeyboardControl()


@sio.event(namespace=NAMESPACE)
def connect():
    print('[+] Connected to LivePanel Server')
    response = sio.call('agent_connect', system_info, namespace=NAMESPACE, timeout=10)
    print('[+] Agent registered:', response)
    threading.Thread(target=heartbeat, daemon=True).start()


@sio.event(namespace=NAMESPACE)
def disconnect():
    print('[-] Disconnected from Server')
    screen_stream.stop()


@sio.event(namespace=NAMESPACE)
def connect_error(data):
    print('[ERROR] Agent namespace connect failed:', data)


@sio.on('start_stream', namespace=NAMESPACE)
def start_stream(data):
    data = data or {}
    if data.get('agent_id') in (None, agent_id):
        settings = data.get('settings') or {}
        if data.get('session_id'):
            settings['session_id'] = data.get('session_id')
        screen_stream.start(settings)


@sio.on('stop_stream', namespace=NAMESPACE)
def stop_stream(data):
    data = data or {}
    if data.get('agent_id') in (None, agent_id):
        screen_stream.stop()


@sio.on('mouse_event', namespace=NAMESPACE)
def mouse_event(data):
    result = mouse_control.handle_event(data)
    sio.emit('mouse_event_result', {'agent_id': agent_id, 'session_id': (data or {}).get('session_id'), **result}, namespace=NAMESPACE)


@sio.on('keyboard_event', namespace=NAMESPACE)
def keyboard_event(data):
    result = keyboard_control.handle_event(data)
    sio.emit('keyboard_event_result', {'agent_id': agent_id, 'session_id': (data or {}).get('session_id'), **result}, namespace=NAMESPACE)


@sio.on('create_windows_user', namespace=NAMESPACE)
def handle_create_windows_user(data):
    data = data or {}
    if data.get('agent_id') not in (None, agent_id):
        return {'success': False, 'message': 'Agent mismatch'}

    return create_windows_user(
        username=data.get('username'),
        password=data.get('password'),
        full_name=data.get('full_name'),
        description=data.get('description'),
    )


@sio.on('create_desktop_shortcut', namespace=NAMESPACE)
def handle_create_desktop_shortcut(data):
    data = data or {}
    if data.get('agent_id') not in (None, agent_id):
        return {'success': False, 'message': 'Agent mismatch'}

    return create_desktop_shortcut(
        username=data.get('username'),
        shortcut_name=data.get('shortcut_name'),
        target_path=data.get('target_path'),
        arguments=data.get('arguments'),
        working_directory=data.get('working_directory'),
        icon_path=data.get('icon_path'),
        folder_permission=data.get('folder_permission'),
    )


@sio.on('delete_desktop_shortcut', namespace=NAMESPACE)
def handle_delete_desktop_shortcut(data):
    data = data or {}
    if data.get('agent_id') not in (None, agent_id):
        return {'success': False, 'message': 'Agent mismatch'}

    return delete_desktop_shortcut(
        username=data.get('username'),
        shortcut_name=data.get('shortcut_name'),
    )


@sio.on('apply_policy', namespace=NAMESPACE)
def handle_apply_policy(data):
    data = data or {}
    if data.get('agent_id') not in (None, agent_id):
        return {'success': False, 'message': 'Agent mismatch'}

    return apply_policy(
        policy=data.get('policy') or {},
        target_username=data.get('target_username'),
    )


def heartbeat():
    while sio.connected:
        sio.emit('heartbeat', {'agent_id': agent_id}, namespace=NAMESPACE)
        time.sleep(5)


def start_agent():
    print(f"[+] LR Agent starting. Server: {SERVER_URL} Namespace: {NAMESPACE} Agent: {agent_id}")
    while True:
        try:
            sio.connect(SERVER_URL, namespaces=[NAMESPACE])
            sio.wait()
        except Exception as error:
            if sio.connected:
                print('[WARN]', error)
                sio.wait()
                continue
            print('[ERROR]', error)
            print('Reconnecting in 5 seconds...')
            time.sleep(5)


if __name__ == '__main__':
    start_agent()
