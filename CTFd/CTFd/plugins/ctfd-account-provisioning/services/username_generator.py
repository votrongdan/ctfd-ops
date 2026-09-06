"""
Username generator for CTFd Account Provisioning plugin.
Converts Unicode display names to ASCII-only usernames.
Handles Vietnamese diacritics, duplicate detection, and normalization.
"""

import re
import unicodedata


# Vietnamese special character mappings that unicodedata normalization
# does not handle correctly (đ/Đ are single characters, not decomposable)
_VIETNAMESE_SPECIAL = {
    "đ": "d",
    "Đ": "D",
}


def _normalize_to_ascii(name):
    """
    Convert a Unicode name to an ASCII-safe username.

    Steps:
    1. Replace Vietnamese đ/Đ with d/D
    2. Unicode NFKD normalization
    3. Remove combining marks (diacritics)
    4. Lowercase
    5. Replace spaces, hyphens, dots with underscores
    6. Remove all characters that are not [a-z0-9_]
    7. Collapse consecutive underscores
    8. Strip leading/trailing underscores
    """
    # Step 1: Handle đ/Đ before normalization
    for char, replacement in _VIETNAMESE_SPECIAL.items():
        name = name.replace(char, replacement)

    # Step 2: NFKD normalization — decomposes characters into base + combining marks
    normalized = unicodedata.normalize("NFKD", name)

    # Step 3: Remove combining marks (category 'Mn' = Mark, Nonspacing)
    ascii_name = "".join(
        c for c in normalized if unicodedata.category(c) != "Mn"
    )

    # Step 4: Lowercase
    ascii_name = ascii_name.lower()

    # Step 5: Replace spaces, hyphens, dots with underscores
    ascii_name = re.sub(r"[\s\-\.]+", "_", ascii_name)

    # Step 6: Remove invalid characters (keep only a-z, 0-9, underscore)
    ascii_name = re.sub(r"[^a-z0-9_]", "", ascii_name)

    # Step 7: Collapse consecutive underscores
    ascii_name = re.sub(r"_+", "_", ascii_name)

    # Step 8: Strip leading/trailing underscores
    ascii_name = ascii_name.strip("_")

    return ascii_name


def generate_usernames(names, player_ids, existing_usernames=None):
    """
    Generate unique usernames for a list of display names.

    :param names: List of Unicode display names
    :param player_ids: List of string player IDs from CSV
    :param existing_usernames: Set of usernames that already exist (e.g., in DB)
    :return: List of generated usernames, same order as input names
    """
    if existing_usernames is None:
        existing_usernames = set()
    else:
        existing_usernames = set(existing_usernames)

    # Track usage counts within this batch
    username_counts = {}
    results = []

    for name, player_id in zip(names, player_ids):
        base_username = _normalize_to_ascii(name)

        # Fallback for names that produce empty usernames
        if not base_username:
            base_username = "player"

        safe_player_id = re.sub(r"[^a-z0-9_]", "", str(player_id).lower())
        if not safe_player_id:
            safe_player_id = "p000"

        candidate = f"{base_username}_{safe_player_id}"
        counter = 1

        # Check against both existing DB usernames and batch-allocated usernames
        while candidate in existing_usernames or candidate in username_counts:
            candidate = f"{base_username}_{safe_player_id}_{counter}"
            counter += 1

        username_counts[candidate] = True
        results.append(candidate)

    return results


def generate_single_username(name):
    """
    Generate a single username from a display name (without duplicate handling).

    :param name: Unicode display name
    :return: ASCII username string
    """
    result = _normalize_to_ascii(name)
    return result if result else "player"
