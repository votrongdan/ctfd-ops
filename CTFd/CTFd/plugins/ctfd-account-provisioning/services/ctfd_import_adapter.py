"""
CTFd import adapter for CTFd Account Provisioning plugin.

This adapter reuses CTFd's own user import logic (UserSchema validation + db commit)
as found in CTFd/utils/csv/__init__.py load_users_csv(). Rather than calling the
HTTP route or creating a separate user creation mechanism, this adapter uses the
same UserSchema and database operations that CTFd's CSV import uses.

Rationale for replicating load_users_csv logic inline:
- load_users_csv() does not provide per-user success/failure tracking with user IDs
- We need to know exactly which users were created and their DB IDs
- We use the exact same code path: UserSchema().load(dict) → db.session.add() → commit()
"""

import logging
from dataclasses import dataclass, field

from CTFd.models import Users, db
from CTFd.schemas.users import UserSchema

logger = logging.getLogger("ctfd-account-provisioning")


@dataclass
class ImportSuccess:
    """A successfully imported user."""
    index: int
    name: str
    username: str
    email: str
    password: str  # Plaintext, kept only for credential document generation
    user_id: int = 0


@dataclass
class ImportFailure:
    """A failed user import."""
    index: int
    name: str
    username: str
    email: str
    errors: dict = field(default_factory=dict)


@dataclass
class ImportResult:
    """Result of the import operation."""
    successful: list = field(default_factory=list)
    failed: list = field(default_factory=list)

    @property
    def total_success(self):
        return len(self.successful)

    @property
    def total_failed(self):
        return len(self.failed)

    @property
    def total(self):
        return self.total_success + self.total_failed

    @property
    def all_succeeded(self):
        return self.total_failed == 0


def import_users(participants):
    """
    Import a list of validated participants into CTFd using the same
    logic as CTFd's load_users_csv() function.

    This function uses UserSchema to validate and create User objects,
    then commits each to the database individually — matching CTFd's
    own import behavior.

    :param participants: List of ParticipantRecord objects with status="valid"
    :return: ImportResult with successful and failed imports
    """
    result = ImportResult()
    valid_participants = [p for p in participants if p.status == "valid"]

    for i, participant in enumerate(valid_participants):
        # Prepare user data in the same format CTFd's CSV import expects
        user_data = {
            "name": participant.username,
            "email": participant.email,
            "password": participant.password,
        }

        # Use UserSchema — the same schema CTFd's load_users_csv uses
        schema = UserSchema()
        try:
            response = schema.load(user_data)
        except Exception as e:
            logger.error(
                "Schema load exception for user '%s': %s",
                participant.username,
                str(e),
            )
            result.failed.append(ImportFailure(
                index=i,
                name=participant.name,
                username=participant.username,
                email=participant.email,
                errors={"schema": [str(e)]},
            ))
            continue

        if response.errors:
            logger.info(
                "Validation errors for user '%s': %s",
                participant.username,
                str(response.errors),
            )
            result.failed.append(ImportFailure(
                index=i,
                name=participant.name,
                username=participant.username,
                email=participant.email,
                errors=response.errors,
            ))
            continue

        # Add to database and commit — same as load_users_csv
        user = response.data
        
        # Explicitly verify the user so they can log in without email verification
        user.verified = True
        user.hidden = False

        db.session.add(user)
        try:
            db.session.commit()
            result.successful.append(ImportSuccess(
                index=i,
                name=participant.name,
                username=participant.username,
                email=participant.email,
                password=participant.password,
                user_id=user.id,
            ))
            logger.info(
                "Successfully created user '%s' (id=%d)",
                participant.username,
                user.id,
            )
        except Exception as e:
            db.session.rollback()
            logger.error(
                "Database error creating user '%s': %s",
                participant.username,
                str(e),
            )
            result.failed.append(ImportFailure(
                index=i,
                name=participant.name,
                username=participant.username,
                email=participant.email,
                errors={"database": [str(e)]},
            ))

    return result
