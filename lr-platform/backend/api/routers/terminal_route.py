from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from backend.services.terminal_service import (
    TerminalManagerService
)


terminal = Blueprint(
    "terminal",
    __name__
)


@terminal.route("/terminal", methods=["POST"])
@login_required
def execute():

    result, status_code = (
        TerminalManagerService.execute_command(
            current_user.id,
            request.form.get("command")
        )
    )

    if isinstance(result, dict):
        return jsonify(result), status_code

    return result, status_code
