"""
CSV parser for CTFd Account Provisioning plugin.
Reads .csv files containing a 'Name' column and returns parsed player data.
"""

import csv
import logging
from dataclasses import dataclass, field
import codecs

logger = logging.getLogger("ctfd-account-provisioning")


@dataclass
class ParsedPlayer:
    """Represents a single parsed player from the Excel file."""
    row_number: int
    player_id: str
    name: str


@dataclass
class ParseResult:
    """Result of parsing a CSV file."""
    success: bool
    players: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    error_message: str = ""


def parse_csv(file_stream):
    """
    Parse a CSV file and extract player names.

    :param file_stream: File-like object (bytes) of a .csv file
    :return: ParseResult with parsed players or error information
    """
    try:
        # Wrap the byte stream to read as text (utf-8)
        text_stream = codecs.iterdecode(file_stream, 'utf-8-sig')
        reader = csv.reader(text_stream)
        
        # Get header row
        try:
            header_row = next(reader)
        except StopIteration:
            return ParseResult(
                success=False,
                error_message="error_no_name_column",
            )
            
        # Find the 'Name' and 'Player ID' columns (case-insensitive)
        name_col_index = None
        player_id_col_index = None
        for i, cell in enumerate(header_row):
            if cell and str(cell).strip().lower() == "name":
                name_col_index = i
            elif cell and str(cell).strip().lower() == "player id":
                player_id_col_index = i
                
        if name_col_index is None:
            return ParseResult(
                success=False,
                error_message="error_no_name_column",
            )
            
        if player_id_col_index is None:
            return ParseResult(
                success=False,
                error_message="error_no_player_id_column",
            )
            
        players = []
        errors = []
        seen_ids = set()
        
        for row_num, row in enumerate(reader, start=2):
            if not row:
                continue
                
            name_value = row[name_col_index] if name_col_index < len(row) else ""
            player_id_value = row[player_id_col_index] if player_id_col_index < len(row) else ""
            
            # Skip completely empty rows
            if not name_value.strip() and not player_id_value.strip():
                if all(not str(c).strip() for c in row):
                    continue
                # Row is not entirely empty but Name or Player ID is empty
                errors.append({
                    "row": row_num,
                    "error": "error_empty_fields",
                })
                continue
                
            if not name_value.strip() or not player_id_value.strip():
                errors.append({"row": row_num, "error": "error_required_fields"})
                continue
            identity = player_id_value.strip().casefold()
            if identity in seen_ids:
                errors.append({"row": row_num, "error": "error_duplicate_player_id"})
                continue
            seen_ids.add(identity)
            name = str(name_value).strip()
            player_id = str(player_id_value).strip()
            players.append(ParsedPlayer(row_number=row_num, player_id=player_id, name=name))
            
        return ParseResult(
            success=True,
            players=players,
            errors=errors,
        )
    except UnicodeDecodeError:
        return ParseResult(
            success=False,
            error_message="error_invalid_file",
        )
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        return ParseResult(
            success=False,
            error_message="error_unreadable_file",
        )
