"""
Account provisioning service for CTFd Account Provisioning plugin.
Orchestrates the full workflow: parse → validate → preview → import → document.
"""

import logging
import secrets
from dataclasses import dataclass, field, asdict
import datetime
import io
import base64
from CTFd.plugins._lifecycle import lifecycle_lock
from CTFd.models import db
from CTFd.schemas.users import UserSchema
from . import storage
from .participant_validator import ParticipantRecord
from .ctfd_import_adapter import ImportResult, ImportSuccess, ImportFailure

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


def cleanup_preview(token):
    with lifecycle_lock("provisioning"):
        job = storage.get(token)
        if job is not None and storage.decode(job)["state"] == "preview":
            storage.delete(token)


def cleanup_document(token):
    cleanup_preview(token)


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

    if not parse_result.players and not parse_result.errors:
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

    # Check collisions against both the DB collation and this batch. Schema
    # validation uses the same admin context as the real import, without commits.
    allocated_emails = set()
    for participant in validation.participants:
        if participant.status != "valid":
            continue
        counter = 2
        while (participant.email.casefold() in allocated_emails or
               Users.query.filter_by(email=participant.email).first() is not None):
            participant.email = f"{participant.username}{counter}@{email_domain}"
            counter += 1
        allocated_emails.add(participant.email.casefold())
        response = UserSchema().load({"name": participant.username,
                                      "email": participant.email,
                                      "password": participant.password})
        if response.errors:
            participant.status = "invalid"
            participant.error = "error_account_constraints"
            participant.errors = response.errors
    validation.valid_count = sum(p.status == "valid" for p in validation.participants)
    validation.invalid_count = len(validation.participants) - validation.valid_count

    # Step 6: Generate a secure token and store preview data
    token = secrets.token_urlsafe(32)
    preview = PreviewData(
        token=token,
        participants=validation.participants,
        valid_count=validation.valid_count,
        invalid_count=validation.invalid_count,
        total_count=validation.total_count,
    )
    with lifecycle_lock("provisioning"):
        storage.save(token, {"state": "preview", "participants": [asdict(p) for p in preview.participants]})

    return preview


def _result(data):
    return ImportResult(successful=[ImportSuccess(**p) for p in data['successful']],
                        failed=[ImportFailure(**p) for p in data['failed']])


def provision_accounts(token, lang="en"):
    # One job transaction includes users AND their encrypted recovery result.
    # A killed worker rolls back both; retry never guesses ownership from names.
    with lifecycle_lock("provisioning"):
        db.session.rollback()
        storage.cleanup_expired()
        if db.engine.dialect.name == "sqlite":
            # SQLite otherwise starts its first SAVEPOINT without an outer write
            # transaction, making RELEASE commit accounts before the job result.
            db.session.execute("BEGIN IMMEDIATE")
        job = storage.get(token)
        if job is None:
            return None, None
        data = storage.decode(job)
        if data['state'] == 'preview':
            participants = [ParticipantRecord(**p) for p in data['participants']]
            try:
                result = import_users(participants, commit=False)
                data = {"state": "complete", "token": token, "successful": [asdict(p) for p in result.successful],
                        "failed": [asdict(p) for p in result.failed], "lang": lang}
                job.payload = storage.encode(data)
                job.expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=storage.ttl('document'))
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
        result = _result(data)
        # Rendering is deliberately deferred to download; a rendering failure
        # cannot hide account-creation success and retries can recover credentials.
        return result, token if result.successful else None


def get_document(doc_token):
    with lifecycle_lock("provisioning"):
        db.session.rollback()
        storage.cleanup_expired()
        job = storage.get(doc_token)
        if job is None:
            return None
        data = storage.decode(job)
        if data['state'] != 'complete' or not data['successful']:
            return None
        if 'document' not in data:
            output = generate_credential_document(_result(data).successful, lang=data.get('lang', 'en'))
            data['document'] = base64.b64encode(output.getvalue()).decode('ascii')
            job.payload = storage.encode(data)
            db.session.commit()
        # Fresh stream for every GET; retries and concurrent downloads are safe.
        return io.BytesIO(base64.b64decode(data['document']))


def cleanup_after_download(doc_token):
    """Compatibility entry point: downloads no longer consume recovery data."""
    with lifecycle_lock("provisioning"):
        storage.cleanup_expired()


def recoverable_documents():
    from flask import session
    with lifecycle_lock("provisioning"):
        storage.cleanup_expired()
        result = []
        jobs = storage.ProvisioningJob.query.filter_by(owner_id=session.get('id')).order_by(storage.ProvisioningJob.expires_at.desc()).all()
        for job in jobs:
            data = storage.decode(job)
            if data['state'] == 'complete' and data['successful']:
                result.append({'token': data['token'], 'count': len(data['successful']), 'expires_at': job.expires_at})
        return result
