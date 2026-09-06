"""Admin blueprint — routes for managing sessions, events, and settings."""

from flask import Blueprint, jsonify, render_template, request, session

from CTFd.models import db
from CTFd.utils import get_config, set_config
from CTFd.utils.decorators import admins_only

from .config import (
    DEFAULTS,
    EVENT_COOLDOWN_KEY,
    HEARTBEAT_INTERVAL_KEY,
    MODE_BLOCK,
    MODE_KEY,
    MODE_MONITORING,
)
from .event_service import EventService
from .session_tracker import SessionTracker

admin_blueprint = Blueprint(
    "ctfd-single-session",
    __name__,
    template_folder="templates",
    static_folder="assets",
    url_prefix="/plugins/ctfd-single-session",
)


# ======================================================================
# HTML pages (admin-only)
# ======================================================================


@admin_blueprint.route("/admin")
@admin_blueprint.route("/admin/sessions")
@admins_only
def admin_sessions():
    page = request.args.get("page", 1, type=int)
    pagination = SessionTracker.get_all_active_sessions(page=page, per_page=50)
    mode = get_config(MODE_KEY, MODE_MONITORING)
    unresolved = EventService.get_unresolved_count()
    return render_template(
        "ssm_sessions.html",
        sessions=pagination.items,
        pagination=pagination,
        mode=mode,
        unresolved_count=unresolved,
    )


@admin_blueprint.route("/admin/events")
@admins_only
def admin_events():
    page = request.args.get("page", 1, type=int)
    event_type = request.args.get("type", None)
    show_resolved = request.args.get("resolved", None)
    resolved_flag = None
    if show_resolved == "true":
        resolved_flag = True
    elif show_resolved == "false":
        resolved_flag = False

    pagination = EventService.get_events(
        page=page, per_page=50, event_type=event_type, resolved=resolved_flag
    )
    mode = get_config(MODE_KEY, MODE_MONITORING)
    unresolved = EventService.get_unresolved_count()
    return render_template(
        "ssm_events.html",
        events=pagination.items,
        pagination=pagination,
        mode=mode,
        unresolved_count=unresolved,
    )


@admin_blueprint.route("/admin/settings")
@admins_only
def admin_settings():
    mode = get_config(MODE_KEY, MODE_MONITORING)
    unresolved = EventService.get_unresolved_count()
    settings = {
        "mode": mode,
        "event_cooldown": get_config(EVENT_COOLDOWN_KEY, "300"),
        "heartbeat_interval": get_config(HEARTBEAT_INTERVAL_KEY, "30"),
    }
    return render_template(
        "ssm_settings.html",
        settings=settings,
        mode=mode,
        unresolved_count=unresolved,
    )


# ======================================================================
# JSON API endpoints (admin-only)
# ======================================================================


@admin_blueprint.route("/api/sessions/live", methods=["GET"])
@admins_only
def api_sessions_live():
    page = request.args.get("page", 1, type=int)
    pagination = SessionTracker.get_all_active_sessions(page=page, per_page=50)
    sessions = [s.to_dict() for s in pagination.items]
    return jsonify(success=True, sessions=sessions, pages=pagination.pages, page=pagination.page)


@admin_blueprint.route("/api/events/live", methods=["GET"])
@admins_only
def api_events_live():
    page = request.args.get("page", 1, type=int)
    event_type = request.args.get("type", None)
    show_resolved = request.args.get("resolved", None)
    resolved_flag = None
    if show_resolved == "true":
        resolved_flag = True
    elif show_resolved == "false":
        resolved_flag = False

    pagination = EventService.get_events(
        page=page, per_page=50, event_type=event_type, resolved=resolved_flag
    )
    events = [e.to_dict() for e in pagination.items]
    unresolved_count = EventService.get_unresolved_count()
    return jsonify(success=True, events=events, pages=pagination.pages, page=pagination.page, unresolved_count=unresolved_count)


@admin_blueprint.route("/api/settings", methods=["PATCH"])
@admins_only
def api_update_settings():
    data = request.get_json() if request.is_json else request.form
    allowed_keys = {
        "mode": MODE_KEY,
        "event_cooldown": EVENT_COOLDOWN_KEY,
        "heartbeat_interval": HEARTBEAT_INTERVAL_KEY,
    }
    updated = {}
    for form_key, config_key in allowed_keys.items():
        if form_key in data:
            val = data[form_key]
            # Validate mode
            if form_key == "mode" and val not in (MODE_MONITORING, MODE_BLOCK):
                return jsonify(success=False, error="Invalid mode"), 400
            set_config(config_key, str(val))
            updated[form_key] = str(val)

    return jsonify(success=True, updated=updated)


@admin_blueprint.route("/api/sessions/<int:session_id>", methods=["DELETE"])
@admins_only
def api_force_logout_session(session_id):
    success = SessionTracker.force_logout_session(session_id)
    if success:
        return jsonify(success=True)
    return jsonify(success=False, error="Session not found or already inactive"), 404


@admin_blueprint.route("/api/sessions/user/<int:user_id>", methods=["DELETE"])
@admins_only
def api_force_logout_all(user_id):
    count = SessionTracker.force_logout_all(user_id)
    return jsonify(success=True, count=count)


@admin_blueprint.route("/api/events/<int:event_id>/resolve", methods=["PATCH"])
@admins_only
def api_resolve_event(event_id):
    admin_id = session.get("id")
    success = EventService.resolve_event(event_id, admin_id)
    if success:
        return jsonify(success=True)
    return jsonify(success=False, error="Event not found"), 404
