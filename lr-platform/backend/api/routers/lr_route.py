from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required

from backend.services.lr_resources_service import LrResourcesService
from backend.services.user_license_service import UserLicenseService


lr_bp = Blueprint("lr", __name__, url_prefix="/api/lr")


def _license_gate(context):
    blocked = UserLicenseService.block_response(current_user, context=context)
    if blocked:
        result, status_code = blocked
        return jsonify(result), status_code
    return None


@lr_bp.route("/my-resources", methods=["GET"])
@login_required
def my_resources():
    result, status_code = LrResourcesService.my_resources(current_user.id)
    return jsonify(result), status_code


@lr_bp.route("/launch", methods=["POST"])
@login_required
def launch_resource():
    data = request.get_json(silent=True) or {}
    if session.get("connection_type") != "remoteapp":
        return jsonify({
            "success": False,
            "error": "RemoteApp launch requires a remoteapp login session",
        }), 409
    blocked = _license_gate({
        "action": "launch_resource",
        "resource_id": str(data.get("resource_id") or ""),
        "type": str(data.get("type") or ""),
    })
    if blocked:
        return blocked

    result, status_code = LrResourcesService.launch_resource(
        data=data,
        user_id=current_user.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
    )
    return jsonify(result), status_code
