"""
CTFd Account Provisioning Plugin
Automates player account creation for offline CTF competitions.
"""

from CTFd.plugins import register_admin_plugin_menu_bar, register_plugin_assets_directory
from CTFd.utils import get_config, set_config

from .config import DEFAULTS
from .routes import blueprint


def load(app):
    """
    CTFd plugin entry point. Called by CTFd's init_plugins().

    :param app: Flask application instance
    """
    plugin_name = __name__.split(".")[-1]

    # Initialize default configuration values
    for key, value in DEFAULTS.items():
        if get_config(key) is None:
            set_config(key, value)

    # Register the admin blueprint
    app.register_blueprint(blueprint)

    # Register static assets directory
    register_plugin_assets_directory(
        app,
        base_path=f"/plugins/{plugin_name}/assets",
        endpoint=f"plugins.{plugin_name}.assets",
    )

    # Register admin menu bar entry
    register_admin_plugin_menu_bar(
        title="Account Provisioning",
        route="/plugins/ctfd-account-provisioning/admin",
    )

    print(" * CTFd Account Provisioning plugin loaded successfully")
