"""Tests for commands/extract_rules.py."""
from cli_civileng.commands.extract_rules import _sanitize_filename


class TestSanitizeFilename:
    def test_spaces_become_hyphens(self):
        assert _sanitize_filename("hello world") == "hello-world"

    def test_portuguese_accents(self):
        result = _sanitize_filename("áéíóú çã")
        assert result == "aeiou-ca"  # space becomes hyphen

    def test_mixed_case(self):
        assert _sanitize_filename("Condomínio Teste") == "condominio-teste"

    def test_special_chars(self):
        result = _sanitize_filename("Mundo Moderno 2024")
        assert result == "mundo-moderno-2024"

    def test_multiple_spaces(self):
        assert _sanitize_filename("a  b") == "a--b"
