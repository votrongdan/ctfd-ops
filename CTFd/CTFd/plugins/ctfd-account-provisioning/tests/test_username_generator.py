"""
Tests for the username generator module.
"""

import os
import sys

import pytest

# Allow running tests standalone without full CTFd installation
_plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

from services.username_generator import (
    _normalize_to_ascii,
    generate_single_username,
    generate_usernames,
)


class TestNormalizeToAscii:
    """Tests for the _normalize_to_ascii internal function."""

    def test_vietnamese_name_basic(self):
        assert _normalize_to_ascii("Nguyễn Văn An") == "nguyen_van_an"

    def test_vietnamese_name_with_d_stroke(self):
        assert _normalize_to_ascii("Đặng Thị Hương") == "dang_thi_huong"

    def test_vietnamese_name_with_d_stroke_2(self):
        assert _normalize_to_ascii("Phạm Minh Đức") == "pham_minh_duc"

    def test_english_name(self):
        assert _normalize_to_ascii("John Smith") == "john_smith"

    def test_empty_string_returns_empty(self):
        assert _normalize_to_ascii("") == ""


class TestGenerateSingleUsername:
    """Tests for generate_single_username."""

    def test_normal_name(self):
        assert generate_single_username("Alice Johnson") == "alice_johnson"


class TestGenerateUsernames:
    """Tests for generate_usernames batch function."""

    def test_unique_usernames(self):
        """Test that all generated usernames append the player_id correctly."""
        names = ["Alice", "Bob", "Charlie"]
        ids = ["P001", "P002", "P003"]
        usernames = generate_usernames(names, ids)
        assert usernames == ["alice_p001", "bob_p002", "charlie_p003"]

    def test_duplicate_names_get_numbered(self):
        """Test that duplicate names with different player IDs get their respective IDs."""
        names = ["Nguyễn Văn An", "Nguyen Van An", "John Smith"]
        ids = ["P001", "P002", "P003"]
        usernames = generate_usernames(names, ids)
        assert usernames == ["nguyen_van_an_p001", "nguyen_van_an_p002", "john_smith_p003"]

    def test_triple_duplicate_names(self):
        """Test three duplicate names."""
        names = ["Alice", "Alice", "Alice"]
        ids = ["P100", "P101", "P102"]
        usernames = generate_usernames(names, ids)
        assert usernames == ["alice_p100", "alice_p101", "alice_p102"]

    def test_existing_usernames_avoided(self):
        """Test that existing usernames get a numbered suffix."""
        names = ["Alice", "Bob"]
        ids = ["P001", "P002"]
        existing = {"alice_p001", "charlie_p001"}
        usernames = generate_usernames(names, ids, existing_usernames=existing)
        assert usernames == ["alice_p001_1", "bob_p002"]

    def test_mixed_names(self):
        """Test a mix of Vietnamese and English names."""
        names = [
            "Nguyễn Văn An",
            "John Smith",
            "Đặng Thị Hương",
        ]
        ids = ["A1", "B2", "C3"]
        usernames = generate_usernames(names, ids)
        assert usernames[0] == "nguyen_van_an_a1"
        assert usernames[1] == "john_smith_b2"
        assert usernames[2] == "dang_thi_huong_c3"
