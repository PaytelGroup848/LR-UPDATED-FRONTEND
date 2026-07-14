from flask import Blueprint, request
from flask_login import login_required

from backend.services.windows_services_service import (
    WindowsServiceManagerService
)

services = Blueprint(
    "services_manager",
    __name__
)


@services.route("/services", methods=["GET"])
@login_required
def all_services():

    response, status_code = (
        WindowsServiceManagerService.list_services()
    )

    return response, status_code


@services.route("/start-service", methods=["POST"])
@login_required
def start():

    response, status_code = (
        WindowsServiceManagerService.start_windows_service(
            request.form.get("service_name")
        )
    )

    return response, status_code


@services.route("/stop-service", methods=["POST"])
@login_required
def stop():

    response, status_code = (
        WindowsServiceManagerService.stop_windows_service(
            request.form.get("service_name")
        )
    )

    return response, status_code
