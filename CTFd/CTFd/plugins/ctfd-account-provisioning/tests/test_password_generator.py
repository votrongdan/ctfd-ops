"""
Tests for the password generator module.
"""

import os
import string
import sys

import pytest

_plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

from services.password_generator import (
    _AMBIGUOUS_CHARS,
    DEFAULT_PASSWORD_LENGTH,
    generate_password,
    generate_passwords,
)


class TestGeneratePassword:
    """Tests for generate_password function."""

    def test_default_length(self):
        """Test that password has the default length."""
        password = generate_password()
        assert len(password) == DEFAULT_PASSWORD_LENGTH

    def test_custom_length(self):
        """Test password with custom length."""
        password = generate_password(length=16)
        assert len(password) == 16

    def test_minimum_length(self):
        """Test that length is at least 4."""
        password = generate_password(length=2)
        assert len(password) == 4

    def test_contains_uppercase(self):
        """Test that password contains at least one uppercase letter."""
        password = generate_password()
        assert any(c in string.ascii_uppercase for c in password)

    def test_contains_lowercase(self):
        """Test that password contains at least one lowercase letter."""
        password = generate_password()
        assert any(c in string.ascii_lowercase for c in password)

    def test_contains_digit(self):
        """Test that password contains at least one digit."""
        password = generate_password()
        assert any(c in string.digits for c in password)

    def test_no_ambiguous_characters(self):
        """Test that password does not contain ambiguous characters."""
        # Run multiple times for statistical confidence
        for _ in range(100):
            password = generate_password()
            for char in password:
                assert char not in _AMBIGUOUS_CHARS, (
                    f"Password '{password}' contains ambiguous char '{char}'"
                )

    def test_only_allowed_characters(self):
        """Test that password only contains allowed character types."""
        allowed = set(string.ascii_letters + string.digits) - _AMBIGUOUS_CHARS
        for _ in range(100):
            password = generate_password()
            for char in password:
                assert char in allowed, (
                    f"Password '{password}' contains disallowed char '{char}'"
                )

    def test_passwords_vary(self):
        """Test that generated passwords are not all the same (basic randomness)."""
        passwords = {generate_password() for _ in range(20)}
        # With 10-char passwords from a large alphabet, collisions are very unlikely
        assert len(passwords) > 15


class TestGeneratePasswords:
    """Tests for generate_passwords batch function."""

    def test_correct_count(self):
        """Test that correct number of passwords are generated."""
        passwords = generate_passwords(10)
        assert len(passwords) == 10

    def test_all_unique(self):
        """Test that all passwords in a batch are unique."""
        passwords = generate_passwords(50)
        assert len(set(passwords)) == 50

    def test_each_meets_requirements(self):
        """Test that each password in a batch meets requirements."""
        passwords = generate_passwords(50)
        for pw in passwords:
            assert len(pw) == DEFAULT_PASSWORD_LENGTH
            assert any(c in string.ascii_uppercase for c in pw)
            assert any(c in string.ascii_lowercase for c in pw)
            assert any(c in string.digits for c in pw)
            assert not any(c in _AMBIGUOUS_CHARS for c in pw)

    def test_empty_batch(self):
        """Test generating zero passwords."""
        passwords = generate_passwords(0)
        assert len(passwords) == 0
