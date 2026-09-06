"""
Account provisioning service for CTFd Account Provisioning plugin.
Orchestrates the full workflow: parse → validate → preview → import → document.
"""

import logging
import secrets
from dataclasses import dataclass, field

from CTFd.models import Users

from .ctfd_import_adapter import import_users
from .document_generator import generate_credential_document
from .csv_parser import parse_csv
from .participant_validator import validate_and_prepare
from .password_generator import generate_passwords
from .username_generator import generate_usernames

logger = logging.getLogger("ctfd-account-provisioning")


@dataclass
class PreviewData:
    """Data for the preview display, stored temporarily server-side."""
    token: str                          # Unique token for session reference
    participants: list = field(default_factory=list)
    valid_count: int = 0
    invalid_count: int = 0
    total_count: int = 0
    error_message: str = ""


# In-memory store for preview data, keyed by token.
# This avoids storing plaintext passwords in the session cookie.
# Entries are cleaned up after provisioning or on new upload.
_preview_store = {}

# In-memory store for generated credential documents, keyed by token.
# Entries are cleaned up after download.
_document_store = {}


def cleanup_preview(token):
    """Remove preview data from the store."""
    _preview_store.pop(token, None)


def cleanup_document(token):
    """Remove document data from the store."""
    _document_store.pop(token, None)


def process_upload(file_stream, email_domain="ctf.local"):
    """
    Process an uploaded CSV file and generate preview data.

    :param file_stream: File-like object of the uploaded .csv
    :param email_domain: Domain for auto-generated emails
    :return: PreviewData object
    """
    # Step 1: Parse CSV
    parse_result = parse_csv(file_stream)

    if not parse_result.success:
        return PreviewData(
            token="",
            error_message=parse_result.error_message,
        )

    if not parse_result.players:
        return PreviewData(
            token="",
            error_message="error_no_valid_players",
        )

    # Step 2: Get existing usernames from DB to avoid collisions
    existing_users = Users.query.with_entities(Users.name).all()
    existing_usernames = {u.name for u in existing_users}

    # Also check existing emails
    existing_emails = {
        u.email for u in Users.query.with_entities(Users.email).all()
    }

    # Step 3: Generate usernames
    player_names = [p.name for p in parse_result.players]
    player_ids = [p.player_id for p in parse_result.players]
    usernames = generate_usernames(player_names, player_ids, existing_usernames)

    # Step 4: Generate passwords
    passwords = generate_passwords(len(parse_result.players))

    # Step 5: Validate and prepare participant records
    validation = validate_and_prepare(
        parsed_players=parse_result.players,
        parse_errors=parse_result.errors,
        usernames=usernames,
        passwords=passwords,
        email_domain=email_domain,
    )

    # Step 5b: Check for email collisions with existing DB emails
    for participant in validation.participants:
        if participant.status == "valid" and participant.email in existing_emails:
            # Try to find a unique email by appending number
            base_email = participant.email
            counter = 2
            while participant.email in existing_emails:
                username_part = participant.username
                participant.email = f"{username_part}{counter}@{email_domain}"
                counter += 1

    # Step 6: Generate a secure token and store preview data
    token = secrets.token_urlsafe(32)
    preview = PreviewData(
        token=token,
        participants=validation.participants,
        valid_count=validation.valid_count,
        invalid_count=validation.invalid_count,
        total_count=validation.total_count,
    )
    _preview_store[token] = preview

    return preview


def provision_accounts(token, lang="en"):
    """
    Execute account provisioning for previously previewed data.

    :param token: Preview token from process_upload
    :param lang: Language code for the credential document
    :return: Tuple of (ImportResult, document_token or None)
    """
    preview = _preview_store.get(token)
    if preview is None:
        return None, None

    # Import users into CTFd
    import_result = import_users(preview.participants)

    # Clean up preview data (contains plaintext passwords)
    cleanup_preview(token)

    # Generate credential document only for successfully created accounts
    doc_token = None
    if import_result.successful:
        doc_output = generate_credential_document(
            import_result.successful, lang=lang
        )
        doc_token = secrets.token_urlsafe(32)
        _document_store[doc_token] = doc_output

    return import_result, doc_token


def get_document(doc_token):
    """
    Retrieve a generated credential document.

    :param doc_token: Document token from provision_accounts
    :return: BytesIO object or None
    """
    return _document_store.get(doc_token)


def cleanup_after_download(doc_token):
    """Clean up document data after download."""
    cleanup_document(doc_token)
