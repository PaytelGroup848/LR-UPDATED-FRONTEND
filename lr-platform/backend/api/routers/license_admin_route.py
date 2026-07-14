from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from backend.api.routers.auth_route import admin_required
from backend.extensions import db
from backend.repositories.license_repository import LicenseActivationRepository
from backend.repositories.license_repository import ProductKeyRepository
from backend.repositories.license_repository import TrialSessionRepository
from backend.services.license_service import LicenseService
from backend.services.user_license_service import UserLicenseService


license_admin = Blueprint("license_admin", __name__, url_prefix="/license")


def _service():
    return LicenseService(
        key_repository=ProductKeyRepository(db),
        activation_repository=LicenseActivationRepository(db),
        trial_repository=TrialSessionRepository(db),
    )


def _product_key_response(product_key):
    created_at = getattr(product_key, "created_at", None)
    return {
        "id": str(getattr(product_key, "id", "")),
        "key_code": getattr(product_key, "key_code", ""),
        "plan_name": getattr(product_key, "plan_name", "STANDARD"),
        "max_activations": getattr(product_key, "max_activations", 1),
        "valid_days": getattr(product_key, "valid_days", 365),
        "is_revoked": bool(getattr(product_key, "is_revoked", False)),
        "issued_to": getattr(product_key, "issued_to", None),
        "created_at": created_at.isoformat() if created_at else None,
    }


@license_admin.route("/admin/keys", methods=["GET"])
@admin_required
def list_product_keys():
    return jsonify([
        _product_key_response(product_key)
        for product_key in _service().list_keys()
    ]), 200


@license_admin.route("/admin/keys", methods=["POST"])
@admin_required
def create_product_keys():
    data = request.get_json(silent=True) or {}
    try:
        keys = _service().create_keys(
            plan_name=data.get("plan_name") or "STANDARD",
            max_activations=1,
            valid_days=int(data.get("valid_days") or 365),
            issued_to=data.get("issued_to") or None,
            quantity=int(data.get("quantity") or 1),
            created_by_id=getattr(current_user, "id", None),
        )
    except Exception as error:
        return jsonify({"message": str(error)}), 400

    return jsonify([_product_key_response(product_key) for product_key in keys]), 201


@license_admin.route("/admin/keys/<key_code>/revoke", methods=["POST"])
@admin_required
def revoke_product_key(key_code):
    try:
        product_key = _service().revoke_key(key_code)
    except ValueError as error:
        return jsonify({"message": str(error)}), 404

    return jsonify(_product_key_response(product_key)), 200


@license_admin.route("/me", methods=["GET"])
@login_required
def my_license_status():
    return jsonify(UserLicenseService.get_status(current_user)), 200


@license_admin.route("/me/activate", methods=["POST"])
@login_required
def activate_my_license():
    data = request.get_json(silent=True) or {}
    key_code = data.get("key_code") or data.get("key") or data.get("license_key")
    try:
        activation = UserLicenseService.activate(current_user, str(key_code or "").strip())
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify({
        "success": True,
        "message": "License activated",
        "activation": activation,
        "license": UserLicenseService.get_status(current_user),
    }), 200


@license_admin.route("/me/hold", methods=["POST"])
@login_required
def hold_my_license():
    data = request.get_json(silent=True) or {}
    UserLicenseService.hold(current_user, context=data.get("context"))
    return jsonify({
        "success": True,
        "license": UserLicenseService.get_status(current_user),
    }), 200
