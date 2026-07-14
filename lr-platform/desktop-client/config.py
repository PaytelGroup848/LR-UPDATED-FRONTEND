import os

try:
    from build_version import APP_VERSION
except ImportError:
    APP_VERSION = "0.0.0-dev"

APP_ID = "desktop-client"
APP_NAME = "Desktop Client"
DEFAULT_SERVER_URL = os.getenv('LR_SERVER_URL', 'http://191.44.87.38:8004')
