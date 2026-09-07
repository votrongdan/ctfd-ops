"""
Admin routes for CTFd Account Provisioning plugin.
Provides upload, preview, provision, and download endpoints.
"""

import logging

from flask import Blueprint, jsonify, render_template, request, send_file, session

from CTFd.utils import get_config, set_config
from CTFd.utils.decorators import admins_only

from .i18n import get_supported_languages, get_text
from .services.provisioning_service import (
    cleanup_preview,
    get_document,
    process_upload,
    provision_accounts,
    recoverable_documents,
)

logger = logging.getLogger("ctfd-account-provisioning")

blueprint = Blueprint(
    "ctfd-account-provisioning",
    __name__,
    template_folder="templates",
    static_folder="assets",
    url_prefix="/plugins/ctfd-account-provisioning",
)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _get_lang():
    """Get the current language setting."""
    lang = request.args.get(
        "lang",
        get_config("account_provisioning:language", default="en"),
    )
    if lang not in get_supported_languages():
        lang = "en"
    return lang


@blueprint.route("/admin")
@admins_only
def admin_page():
    """Render the main Account Provisioning admin page."""
    lang = _get_lang()
    email_domain = get_config("account_provisioning:email_domain", default="ctf.local")
    nonce = session.get("nonce", "")

    # Build translations dict for the template
    translation_keys = [
        "page_title", "page_subtitle", "upload_title", "upload_description",
        "upload_button", "upload_select_file", "settings_title",
        "email_domain_label", "email_domain_help", "language_label",
        "preview_title", "preview_summary", "total_players", "valid_players",
        "invalid_players", "col_number", "col_name", "col_username",
        "col_email", "col_password", "col_status", "status_valid",
        "status_invalid", "confirm_button", "confirm_message", "cancel_button",
        "results_title", "results_success", "results_partial",
        "results_failure", "download_button", "col_result", "result_created",
        "result_failed",
    ]
    t = {key: get_text(key, lang) for key in translation_keys}

    return render_template(
        "account_provisioning.html",
        t=t,
        lang=lang,
        email_domain=email_domain,
        nonce=nonce,
        supported_languages=get_supported_languages(),
        recovery_jobs=recoverable_documents(),
    )


@blueprint.route("/admin/upload", methods=["POST"])
@admins_only
def upload():
    """Handle CSV file upload and return preview data as JSON."""
    lang = _get_lang()

    # Check for file
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "error": get_text("error_no_file", lang),
        }), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({
            "success": False,
            "error": get_text("error_no_file", lang),
        }), 400

    # Validate file extension
    if not file.filename.lower().endswith(".csv"):
        return jsonify({
            "success": False,
            "error": get_text("error_invalid_file", lang),
        }), 400

    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        return jsonify({
            "success": False,
            "error": get_text("error_file_too_large", lang),
        }), 400

    # Get email domain from form or config
    email_domain = request.form.get(
        "email_domain",
        get_config("account_provisioning:email_domain", default="ctf.local"),
    )

    # Save email domain setting
    set_config("account_provisioning:email_domain", email_domain)

    # Save language setting
    req_lang = request.form.get("lang", lang)
    if req_lang in get_supported_languages():
        set_config("account_provisioning:language", req_lang)

    # Process the upload
    preview = process_upload(file, email_domain=email_domain)

    if preview.error_message:
        return jsonify({
            "success": False,
            "error": get_text(preview.error_message, lang),
        }), 400

    # Serialize preview data for JSON response
    participants_data = []
    for p in preview.participants:
        participants_data.append({
            "row_number": p.row_number,
            "name": p.name,
            "username": p.username,
            "email": p.email,
            "password": p.password,
            "status": p.status,
            "error": get_text(p.error, lang) if p.error else "",
            "errors": p.errors,
        })

    return jsonify({
        "success": True,
        "token": preview.token,
        "valid_count": preview.valid_count,
        "invalid_count": preview.invalid_count,
        "total_count": preview.total_count,
        "participants": participants_data,
    })


@blueprint.route("/admin/provision", methods=["POST"])
@admins_only
def provision():
    """Execute account provisioning for previewed data."""
    lang = _get_lang()

    data = request.get_json()
    if not data or "token" not in data:
        return jsonify({
            "success": False,
            "error": get_text("error_no_preview_data", lang),
        }), 400

    token = data["token"]
    req_lang = data.get("lang", lang)

    import_result, doc_token = provision_accounts(token, lang=req_lang)

    if import_result is None:
        return jsonify({
            "success": False,
            "error": get_text("error_no_preview_data", lang),
        }), 400

    # Serialize results
    successful_data = []
    for s in import_result.successful:
        successful_data.append({
            "name": s.name,
            "username": s.username,
            "email": s.email,
            "user_id": s.user_id,
        })

    failed_data = []
    for f in import_result.failed:
        failed_data.append({
            "name": f.name,
            "username": f.username,
            "email": f.email,
            "errors": f.errors,
        })

    # Build result message
    if import_result.all_succeeded:
        message = get_text("results_success", lang).format(
            count=import_result.total_success
        )
    elif import_result.total_success > 0:
        message = get_text("results_partial", lang).format(
            success=import_result.total_success,
            total=import_result.total,
            failed=import_result.total_failed,
        )
    else:
        message = get_text("results_failure", lang)

    return jsonify({
        "success": True,
        "message": message,
        "doc_token": doc_token,
        "total_success": import_result.total_success,
        "total_failed": import_result.total_failed,
        "successful": successful_data,
        "failed": failed_data,
    })


@blueprint.route("/admin/download/<doc_token>")
@admins_only
def download(doc_token):
    """Download the generated credential document."""
    doc_output = get_document(doc_token)

    if doc_output is None:
        return jsonify({"success": False, "error": "Document not found."}), 404

    response = send_file(
        doc_output,
        as_attachment=True,
        download_name="player_credentials.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@blueprint.route("/admin/preview/<token>", methods=["DELETE"])
@admins_only
def cancel_preview(token):
    cleanup_preview(token)
    return jsonify(success=True)
