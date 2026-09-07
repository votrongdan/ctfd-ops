"""
CTFd Single Session Monitor
============================
Monitors and controls concurrent login sessions for CTFd accounts.

Two modes:
* **Monitoring** — multiple sessions allowed; admins alerted.
* **Block** — only one active session per account; new logins rejected.
"""

from CTFd.plugins import (
    register_admin_plugin_menu_bar,
    register_plugin_assets_directory,
)
from CTFd.utils import get_config, set_config

import importlib
from CTFd.plugins._lifecycle import additive_upgrade
from .config import DEFAULTS, PLUGIN_NAME
from .hooks import install_hooks
from .routes import admin_blueprint


def load(app):
    """CTFd plugin entry point — called by ``init_plugins()``."""

    # Create plugin tables (SSMSession, SSMEvent)
    # The import triggers SQLAlchemy model registration.
    from . import models  # noqa: F401

    migration = importlib.import_module(__name__ + ".migrations.0001_session_lifecycle")
    additive_upgrade(PLUGIN_NAME, migration.revision, migration.upgrade)

    # Seed default configuration values on first install
    for key, value in DEFAULTS.items():
        if get_config(key) is None:
            set_config(key, value)

    # Register admin blueprint (HTML pages + API)
    app.register_blueprint(admin_blueprint)

    # Register static assets directory
    register_plugin_assets_directory(
        app,
        base_path=f"/plugins/{PLUGIN_NAME}/assets",
        endpoint=f"plugins.{PLUGIN_NAME}.assets",
    )

    # Register admin menu bar entry
    register_admin_plugin_menu_bar(
        title="Single Session",
        route=f"/plugins/{PLUGIN_NAME}/admin/sessions",
    )

    # Install login/logout hooks and before_request processors
    install_hooks(app)

    print(" * CTFd Single Session Monitor plugin loaded successfully")
