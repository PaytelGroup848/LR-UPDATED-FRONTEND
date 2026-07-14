from flask import Blueprint, jsonify, request
from flask_login import login_required

from backend.services.agent_service import AgentService


agent_bp = Blueprint("agent", __name__)


@agent_bp.route(
    "/agents",
    methods=["GET"]
)
@login_required
def get_agents():

    return jsonify(
        AgentService.get_agents(username=request.args.get("username"))
    )


@agent_bp.route(
    "/agents/<agent_id>",
    methods=["GET"]
)
@login_required
def get_agent(agent_id):

    result = AgentService.get_agent(
        agent_id
    )

    if not result["success"]:
        return jsonify(result), 404

    return jsonify(result)
