import os
import time
from datetime import datetime

import psutil
from flask import current_app

from backend.extensions import db
from backend.manager.stream_manager import stream_manager
from backend.models.agent import Agent
from backend.models.rdp_session import RdpSession


_MONITORING_CACHE = {"expires_at": 0, "data": None}


def _iso(value):
    return value.isoformat() if value else None


class MonitoringService:
    @staticmethod
    def get_health():
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(os.getcwd())
        network = psutil.net_io_counters()
        active_sessions = RdpSession.collection.count_documents({"status": "active"})
        total_agents = Agent.collection.count_documents({})
        online_agents = Agent.collection.count_documents({"status": "online"})
        return {
            "status": "healthy",
            "checked_at": datetime.utcnow().isoformat(),
            "process": {
                "pid": os.getpid(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "network_sent_mb": round(network.bytes_sent / 1024 / 1024, 1),
                "network_recv_mb": round(network.bytes_recv / 1024 / 1024, 1),
            },
            "sessions": {
                "active": active_sessions,
                "total": RdpSession.collection.count_documents({}),
            },
            "agents": {
                "online": online_agents,
                "total": total_agents,
            },
        }

    @staticmethod
    def get_service_status():
        services = {
            "backend": {"status": "ok", "message": "API responding"},
            "database": {"status": "unknown", "message": "Not checked"},
            "guacamole": {"status": "unknown", "message": "Not checked"},
            "api": {"status": "ok", "message": "Routes loaded"},
            "license": {"status": "unknown", "message": "Not checked"},
        }

        try:
            db.command("ping")
            services["database"] = {"status": "ok", "message": "MongoDB ping OK"}
        except Exception as error:
            services["database"] = {"status": "error", "message": str(error)}

        try:
            required = ("GUACAMOLE_URL", "GUACAMOLE_USER", "GUACAMOLE_PASSWORD")
            missing = [key for key in required if not current_app.config.get(key)]
            if missing:
                services["guacamole"] = {
                    "status": "warning",
                    "message": f"Missing config: {', '.join(missing)}",
                }
            else:
                services["guacamole"] = {"status": "ok", "message": "Configured"}
        except RuntimeError:
            services["guacamole"] = {"status": "warning", "message": "No app context"}

        try:
            db["product_keys"].estimated_document_count()
            services["license"] = {"status": "ok", "message": "License storage OK"}
        except Exception as error:
            services["license"] = {"status": "error", "message": str(error)}

        return services

    @staticmethod
    def get_agents_summary():
        agents = []
        for agent in Agent.collection.find().sort("last_seen", -1):
            agents.append({
                "agent_id": agent.get("agent_id"),
                "hostname": agent.get("hostname"),
                "status": agent.get("status"),
                "last_seen": _iso(agent.get("last_seen")),
            })
        return {
            "items": agents,
            "total": len(agents),
            "online": sum(1 for agent in agents if agent.get("status") == "online"),
        }

    @staticmethod
    def get_streams(agent_id=None):
        streams = stream_manager.status()
        if agent_id:
            streams = [item for item in streams if item.get("agent_id") == agent_id]
        return {
            "items": streams,
            "total": len(streams),
        }

    @staticmethod
    def get_monitoring():
        now = time.monotonic()
        if _MONITORING_CACHE["data"] is not None and _MONITORING_CACHE["expires_at"] > now:
            return _MONITORING_CACHE["data"]

        data = {
            "success": True,
            "health": MonitoringService.get_health(),
            "agents": MonitoringService.get_agents_summary(),
            "streams": MonitoringService.get_streams(),
            "services": MonitoringService.get_service_status(),
        }
        _MONITORING_CACHE.update({"expires_at": now + 3, "data": data})
        return data

    @staticmethod
    def get_monitoring_uncached():
        return {
            "success": True,
            "health": MonitoringService.get_health(),
            "agents": MonitoringService.get_agents_summary(),
            "streams": MonitoringService.get_streams(),
            "services": MonitoringService.get_service_status(),
        }
