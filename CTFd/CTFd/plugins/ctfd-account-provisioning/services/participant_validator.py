"""
Participant validator for CTFd Account Provisioning plugin.
Combines parsed player data with generated usernames, passwords, and emails
into validated participant records ready for import.
"""

from dataclasses import dataclass, field


@dataclass
class ParticipantRecord:
    """A fully prepared participant record ready for CTFd import."""
    row_number: int
    name: str           # Original Unicode display name
    username: str        # Generated ASCII username
    email: str           # Generated placeholder email
    password: str        # Generated plaintext password (kept in memory only)
    status: str = "valid"    # "valid" or "invalid"
    errors: dict = field(default_factory=dict)
    error: str = ""          # Error message key if invalid


@dataclass
class ValidationResult:
    """Result of the full validation and preparation process."""
    participants: list = field(default_factory=list)
    valid_count: int = 0
    invalid_count: int = 0
    total_count: int = 0


def validate_and_prepare(parsed_players, parse_errors, usernames, passwords,
                         email_domain="ctf.local"):
    """
    Combine parsed players with generated usernames, passwords, and emails
    into validated ParticipantRecords.

    :param parsed_players: List of ParsedPlayer objects from csv_parser
    :param parse_errors: List of error dicts from csv_parser
    :param usernames: List of generated usernames (same order as parsed_players)
    :param passwords: List of generated passwords (same order as parsed_players)
    :param email_domain: Domain for auto-generated email addresses
    :return: ValidationResult with all participant records
    """
    participants = []
    valid_count = 0
    invalid_count = 0

    # First add valid players
    for i, player in enumerate(parsed_players):
        username = usernames[i]
        password = passwords[i]
        email = f"{username}@{email_domain}"

        record = ParticipantRecord(
            row_number=player.row_number,
            name=player.name,
            username=username,
            email=email,
            password=password,
            status="valid",
        )
        participants.append(record)
        valid_count += 1

    # Then add invalid entries from parse errors
    for error in parse_errors:
        record = ParticipantRecord(
            row_number=error["row"],
            name="",
            username="",
            email="",
            password="",
            status="invalid",
            error=error["error"],
        )
        participants.append(record)
        invalid_count += 1

    # Sort by row number for consistent display
    participants.sort(key=lambda p: p.row_number)

    return ValidationResult(
        participants=participants,
        valid_count=valid_count,
        invalid_count=invalid_count,
        total_count=valid_count + invalid_count,
    )
