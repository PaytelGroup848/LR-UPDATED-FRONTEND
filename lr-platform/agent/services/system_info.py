import platform
import psutil
import uuid
import getpass
import socket

def get_system_info():
    return {
        "agent_id": str(uuid.getnode()),
        "hostname": platform.node(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "username": getpass.getuser(),
        "os": platform.system() + " " + platform.release(),
        "cpu": platform.processor(),
        "ram": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB"
    }
