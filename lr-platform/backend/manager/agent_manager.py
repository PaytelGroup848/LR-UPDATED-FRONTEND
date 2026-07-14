from backend.models.agent import Agent
from backend.models.server import Server
from backend.extensions import db
from datetime import datetime


def register_agent(agent_id, hostname, ip_address, username, os, cpu, ram):
    agent = Agent.collection.find_one({"agent_id": agent_id})
    if agent:
        Agent.collection.update_one(
            {"agent_id": agent_id},
            {
                "$set": {
                    "hostname": hostname,
                    "ip_address": ip_address,
                    "username": username,
                    "os": os,
                    "cpu": cpu,
                    "ram": ram,
                    "status": "online",
                    "last_seen": datetime.utcnow()
                }
            }
        )
    else:
        Agent.create(
        agent_id=agent_id,
        hostname=hostname,
        ip_address=ip_address,
        username=username,
        os=os,
        cpu=cpu,
        ram=ram,
        status="online"
    )
        

def update_heartbeat(agent_id):
    agent = Agent.collection.find_one({"agent_id": agent_id})
    if agent:
        Agent.collection.update_one(
            {"agent_id": agent_id},
            {
                "$set": {
                    "status": "online",
                    "last_seen": datetime.utcnow()
                }
            }
        )

def set_offline(agent_id):
    agent = Agent.collection.find_one({"agent_id": agent_id})
    if agent:
        Agent.collection.update_one(
            {"agent_id": agent_id},
            {
                "$set": {
                    "status": "offline",
                    "last_seen": datetime.utcnow()
                }
            }
        )