"""
Password generator for CTFd Account Provisioning plugin.
Generates cryptographically secure, human-typeable passwords.
"""

import secrets
import string


# Characters that are easy to confuse when reading printed text
_AMBIGUOUS_CHARS = set("0O1lI")

# Character sets for password generation (excluding ambiguous characters)
_UPPERCASE = "".join(c for c in string.ascii_uppercase if c not in _AMBIGUOUS_CHARS)
_LOWERCASE = "".join(c for c in string.ascii_lowercase if c not in _AMBIGUOUS_CHARS)
_DIGITS = "".join(c for c in string.digits if c not in _AMBIGUOUS_CHARS)

# Full alphabet for filling remaining positions
_ALL_CHARS = _UPPERCASE + _LOWERCASE + _DIGITS

# Default password length
DEFAULT_PASSWORD_LENGTH = 10


def generate_password(length=DEFAULT_PASSWORD_LENGTH):
    """
    Generate a single cryptographically secure password.

    Guarantees at least 1 uppercase letter, 1 lowercase letter, and 1 digit.
    Excludes ambiguous characters (0, O, 1, l, I) for ease of manual entry.

    :param length: Password length (minimum 4)
    :return: Generated password string
    """
    if length < 4:
        length = 4

    while True:
        # Ensure at least one of each required character type
        password_chars = [
            secrets.choice(_UPPERCASE),
            secrets.choice(_LOWERCASE),
            secrets.choice(_DIGITS),
        ]

        # Fill remaining positions from the full character set
        for _ in range(length - 3):
            password_chars.append(secrets.choice(_ALL_CHARS))

        # Shuffle to randomize the position of guaranteed characters
        # Using Fisher-Yates shuffle with secrets for secure randomness
        for i in range(len(password_chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

        password = "".join(password_chars)

        # Verify the password meets all requirements (should always pass
        # but we verify for defense-in-depth)
        has_upper = any(c in _UPPERCASE for c in password)
        has_lower = any(c in _LOWERCASE for c in password)
        has_digit = any(c in _DIGITS for c in password)
        no_ambiguous = not any(c in _AMBIGUOUS_CHARS for c in password)

        if has_upper and has_lower and has_digit and no_ambiguous:
            return password


def generate_passwords(count, length=DEFAULT_PASSWORD_LENGTH):
    """
    Generate multiple unique passwords.

    :param count: Number of passwords to generate
    :param length: Password length
    :return: List of generated password strings
    """
    passwords = set()
    result = []

    for _ in range(count):
        # Generate unique passwords (collision is astronomically unlikely
        # but we handle it for correctness)
        password = generate_password(length)
        attempts = 0
        while password in passwords and attempts < 100:
            password = generate_password(length)
            attempts += 1
        passwords.add(password)
        result.append(password)

    return result
