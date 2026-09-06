"""Plugin configuration constants and defaults."""

PLUGIN_NAME = "ctfd-single-session"
CONFIG_PREFIX = "ssm"

# Config keys
MODE_KEY = f"{CONFIG_PREFIX}:mode"
EVENT_COOLDOWN_KEY = f"{CONFIG_PREFIX}:event_cooldown"
HEARTBEAT_INTERVAL_KEY = f"{CONFIG_PREFIX}:heartbeat_interval"


# Mode values
MODE_MONITORING = "monitoring"
MODE_BLOCK = "block"

# Event types
EVENT_MULTIPLE_SESSIONS = "multiple_sessions"
EVENT_LOGIN_BLOCKED = "login_blocked"

# Defaults applied on first load
DEFAULTS = {
    MODE_KEY: MODE_MONITORING,
    EVENT_COOLDOWN_KEY: "300",
    HEARTBEAT_INTERVAL_KEY: "30",
}
