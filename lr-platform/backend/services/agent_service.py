from datetime import datetime, timedelta

from backend.models.agent import Agent


def _serialize(agent):
    if not agent:
        return None

    last_seen = agent.get("last_seen")
    status = agent.get("status") or "offline"
    if last_seen and datetime.utcnow() - last_seen > timedelta(seconds=45):
        status = "offline"

    return {
        "id": str(agent.get("_id")) if agent.get("_id") else None,
        "agent_id": agent.get("agent_id"),
        "hostname": agent.get("hostname"),
        "ip_address": agent.get("ip_address"),
        "username": agent.get("username"),
        "os": agent.get("os"),
        "cpu": agent.get("cpu"),
        "ram": agent.get("ram"),
        "status": status,
        "last_seen": last_seen.isoformat() if last_seen else None,
        "recording": bool(agent.get("recording")),
    }


class AgentService:

    @staticmethod
    def get_agents(username=None):
        query = {}
        if username:
            query["username"] = str(username)
        return {
            "success": True,
            "agents": [_serialize(agent) for agent in Agent.collection.find(query).sort("last_seen", -1).limit(500)],
        }

    @staticmethod
    def get_agent(agent_id):
        agent = Agent.get_by_agent_id(agent_id)
        if not agent:
            return {
                "success": False,
                "error": "Agent not found"
            }
        return {
            "success": True,
            "agent": _serialize(agent),
        }
