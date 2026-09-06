"""
Login / logout hooks and before-request processors.

This module monkey-patches CTFd's ``login_user`` and ``logout_user`` so the
plugin can track sessions without modifying CTFd core.  It also registers
``@app.before_request`` handlers for:

* **Block Mode gate** — rejects logins when an active session already exists.
* **Session heartbeat** — throttled ``last_seen`` updates.
"""

import logging

from flask import render_template, request, session

from CTFd.models import Users, db
from CTFd.utils import get_config
from CTFd.utils.crypto import verify_password
from CTFd.utils.user import authed, get_ip
from CTFd.utils.validators import validate_email

from .config import MODE_BLOCK, MODE_KEY
from .event_service import EventService
from .session_tracker import SessionTracker

logger = logging.getLogger("ssm")


# ======================================================================
# Monkey-patching login_user / logout_user
# ======================================================================

def install_hooks(app):
    """
    Replace ``login_user`` and ``logout_user`` across all modules that import
    them, then register request-level hooks on *app*.
    """
    import CTFd.auth as auth_module
    import CTFd.utils.initialization as init_module
    import CTFd.utils.security.auth as auth_utils

    _original_login_user = auth_utils.login_user
    _original_logout_user = auth_utils.logout_user

    # ---- wrapped login_user -------------------------------------------

    def wrapped_login_user(user):
        """Call the real login_user, then record the session."""
        _original_login_user(user)

        # Skip API-token auth — it calls login_user on every request.
        if request and request.headers.get("Authorization"):
            return

        try:
            if getattr(session, 'sid', None) is None:
                from flask import current_app
                session.sid = current_app.session_interface._generate_sid()
            
            sid = session.sid
            if not sid:
                return

            mode = get_config(MODE_KEY, "monitoring")

            if mode == MODE_BLOCK:
                record, blocked = SessionTracker.register_session_atomic(
                    user_id=user.id,
                    session_id=sid,
                )
                if blocked:
                    # Race condition: another request created a session between
                    # our before_request check and now.  Undo the login so the
                    # user sees a clean login page on next request.
                    session.clear()
                    logger.warning(
                        "[SSM] Race-condition block for user %s (id=%d)",
                        user.name,
                        user.id,
                    )
                    return
            else:
                # Monitoring mode — always allow, always record.
                SessionTracker.register_session(
                    user_id=user.id,
                    session_id=sid,
                )
                active = SessionTracker.get_active_sessions(user.id)
                if len(active) > 1:
                    EventService.create_multi_session_event(user.id, active)
        except Exception:
            logger.exception("[SSM] Error in wrapped_login_user")

    # ---- wrapped logout_user ------------------------------------------

    def wrapped_logout_user():
        """Clean up session record, then call the real logout_user."""
        try:
            if authed() and hasattr(session, "sid") and session.sid:
                SessionTracker.remove_session_by_sid(session.sid)
        except Exception:
            logger.exception("[SSM] Error in wrapped_logout_user")
        finally:
            _original_logout_user()

    # ---- apply patches ------------------------------------------------

    auth_utils.login_user = wrapped_login_user
    auth_utils.logout_user = wrapped_logout_user

    # auth.py imports login_user/logout_user at module level, so the names
    # in its namespace still point to the originals.  Patch them too.
    auth_module.login_user = wrapped_login_user
    auth_module.logout_user = wrapped_logout_user

    # initialization/__init__.py also imports both.
    init_module.login_user = wrapped_login_user
    init_module.logout_user = wrapped_logout_user

    # ------------------------------------------------------------------
    # before_request: Block-Mode gate
    # ------------------------------------------------------------------

    @app.before_request
    def ssm_block_mode_gate():
        """
        In Block Mode, reject POST /login when the user already has an
        active session.

        We validate credentials here first so that a wrong-password attempt
        does not leak whether an active session exists.
        """
        if get_config(MODE_KEY, "monitoring") != MODE_BLOCK:
            return None
        if request.endpoint != "auth.login" or request.method != "POST":
            return None

        name = request.form.get("name", "")
        password = request.form.get("password", "")

        # Look up user (same logic as CTFd's auth.login)
        if validate_email(name):
            user = Users.query.filter_by(email=name).first()
        else:
            user = Users.query.filter_by(name=name).first()

        if not user or user.password is None:
            return None  # let CTFd handle "invalid credentials"

        if not verify_password(password, user.password):
            return None  # let CTFd handle "wrong password"

        # Credentials are valid — check for existing active session
        if SessionTracker.has_active_session(user.id):
            EventService.create_login_blocked_event(user.id)
            errors = [
                "This account is already logged in on another device. "
                "Please log out from the other device first."
            ]
            return render_template("login.html", errors=errors)

        return None  # proceed to normal login flow

    # ------------------------------------------------------------------
    # before_request: session heartbeat
    # ------------------------------------------------------------------

    @app.before_request
    def ssm_session_heartbeat():
        """Update last_seen_at (throttled) for the current session."""
        if not authed():
            return None
        # Skip API token requests
        if request.headers.get("Authorization"):
            return None
        if not hasattr(session, "sid") or not session.sid:
            return None
        try:
            SessionTracker.update_last_seen(session.sid)
        except Exception:
            logger.exception("[SSM] Error in session heartbeat")
        return None
