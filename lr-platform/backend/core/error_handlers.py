from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(Exception)
    def log_unhandled_exception(error):
        if isinstance(error, HTTPException):
            return error

        app.logger.exception("Unhandled exception")
        raise error