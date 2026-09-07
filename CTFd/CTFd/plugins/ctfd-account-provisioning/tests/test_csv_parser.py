"""
Tests for the CSV parser module.
"""

import os
import sys
import tempfile
import codecs

import pytest

_plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

from services.csv_parser import (
    ParseResult,
    parse_csv,
)


def _create_csv(rows, headers=None):
    """Helper: create a temporary .csv file with given data."""
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    with codecs.open(tmp.name, 'w', 'utf-8-sig') as f:
        if headers:
            f.write(",".join(headers) + "\n")
        for row in rows:
            f.write(",".join(row) + "\n")
    return tmp.name


def _cleanup(path):
    """Remove temporary file."""
    try:
        os.unlink(path)
    except OSError:
        pass


class TestCsvParser:
    """Tests for parse_csv function."""

    def test_valid_file_with_names_and_ids(self):
        """Test parsing a valid file with Player IDs and Names."""
        path = _create_csv(
            [["P001", "Nguyễn Văn An"], ["P002", "John Smith"], ["P003", "Lê Quốc Việt"]],
            headers=["Player ID", "Name"],
        )
        try:
            with open(path, 'rb') as f:
                result = parse_csv(f)
            assert result.success is True
            assert len(result.players) == 3
            assert result.players[0].name == "Nguyễn Văn An"
            assert result.players[0].player_id == "P001"
            assert result.players[1].name == "John Smith"
            assert result.players[1].player_id == "P002"
        finally:
            _cleanup(path)

    def test_missing_name_column(self):
        """Test error when Name column is missing."""
        path = _create_csv(
            [["P001", "Alice"]],
            headers=["Player ID", "User"],
        )
        try:
            with open(path, 'rb') as f:
                result = parse_csv(f)
            assert result.success is False
            assert result.error_message == "error_no_name_column"
        finally:
            _cleanup(path)

    def test_missing_player_id_column(self):
        """Test error when Player ID column is missing."""
        path = _create_csv(
            [["Alice"]],
            headers=["Name"],
        )
        try:
            with open(path, 'rb') as f:
                result = parse_csv(f)
            assert result.success is False
            assert result.error_message == "error_no_player_id_column"
        finally:
            _cleanup(path)

    def test_case_insensitive_header(self):
        """Test that Name and Player ID column headers are case-insensitive."""
        path = _create_csv(
            [["p1", "Alice"]],
            headers=["PLAYER id", "NAME"],
        )
        try:
            with open(path, 'rb') as f:
                result = parse_csv(f)
            assert result.success is True
            assert len(result.players) == 1
            assert result.players[0].name == "Alice"
            assert result.players[0].player_id == "p1"
        finally:
            _cleanup(path)

    def test_empty_rows_skipped(self):
        """Test that completely empty rows are skipped."""
        path = _create_csv(
            [["P001", "Alice"], ["", ""], ["P002", "Bob"]],
            headers=["Player ID", "Name"],
        )
        try:
            with open(path, 'rb') as f:
                result = parse_csv(f)
            assert result.success is True
            assert len(result.players) == 2
            assert result.players[0].name == "Alice"
            assert result.players[1].name == "Bob"
        finally:
            _cleanup(path)

    def test_invalid_file_format(self):
        """Test error for non-csv file (binary)."""
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        tmp.write(b"\x00\x01\x02\xffThis is not text")
        tmp.close()
        try:
            with open(tmp.name, 'rb') as f:
                result = parse_csv(f)
            assert result.success is False
            assert result.error_message in ("error_invalid_file", "error_unreadable_file")
        finally:
            _cleanup(tmp.name)
