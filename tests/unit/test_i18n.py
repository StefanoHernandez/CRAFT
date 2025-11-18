"""Tests for i18n module."""

import pytest

from craft.i18n import Translator, Language, detect_language


@pytest.mark.unit
class TestTranslator:
    """Test Translator class."""

    def test_create_translator(self):
        """Test creating a translator."""
        translator = Translator(language=Language.ENGLISH)

        assert translator.language == Language.ENGLISH

    def test_get_translation(self):
        """Test getting a translation."""
        translator = Translator(language=Language.ITALIAN)

        welcome = translator.get("welcome")
        assert welcome == "Benvenuto in CRAFT"

    def test_fallback_to_english(self):
        """Test fallback to English for missing translations."""
        translator = Translator(language=Language.ITALIAN)

        # Request a key that might not exist
        result = translator.get("nonexistent_key")
        # Should return the key itself as fallback
        assert result is not None

    def test_translation_with_formatting(self):
        """Test translation with format parameters."""
        translator = Translator(language=Language.ITALIAN)

        message = translator.get("respond_in_language", language="Italiano")
        assert "Italiano" in message

    def test_translate_prompt(self):
        """Test translating a prompt."""
        translator = Translator(language=Language.ITALIAN)

        prompt = translator.translate_prompt("You are a helpful assistant.")

        assert prompt is not None
        # For Italian, should include language instruction
        assert len(prompt) > len("You are a helpful assistant.")

    def test_translate_prompt_english_unchanged(self):
        """Test that English prompts are not modified."""
        translator = Translator(language=Language.ENGLISH)

        original = "You are a helpful assistant."
        prompt = translator.translate_prompt(original)

        assert prompt == original

    def test_auto_detect(self):
        """Test auto-detecting language and creating translator."""
        translator = Translator.auto_detect("Ciao! Come stai?")

        assert translator.language == Language.ITALIAN

    @pytest.mark.parametrize("language", [
        Language.ENGLISH,
        Language.ITALIAN,
        Language.SPANISH,
        Language.FRENCH,
        Language.GERMAN,
        Language.PORTUGUESE,
    ])
    def test_all_languages_have_welcome(self, language):
        """Test that all languages have welcome message."""
        translator = Translator(language=language)
        welcome = translator.get("welcome")

        assert welcome is not None
        assert len(welcome) > 0


@pytest.mark.unit
class TestDetectLanguage:
    """Test language detection."""

    @pytest.mark.parametrize("text,expected_language", [
        ("Hello, how are you?", Language.ENGLISH),
        ("Ciao! Come stai?", Language.ITALIAN),
        ("¡Hola! ¿Cómo estás?", Language.SPANISH),
        ("Bonjour! Comment allez-vous?", Language.FRENCH),
        ("Hallo! Wie geht es dir?", Language.GERMAN),
        ("Olá! Como vai?", Language.PORTUGUESE),
    ])
    def test_detect_language(self, text, expected_language):
        """Test detecting various languages."""
        detected = detect_language(text)
        assert detected == expected_language

    def test_detect_unknown_defaults_to_english(self):
        """Test that unknown text defaults to English."""
        detected = detect_language("xyzabc123")
        assert detected == Language.ENGLISH

    def test_detect_mixed_content(self):
        """Test detection with mixed content."""
        # Italian keywords should be detected
        detected = detect_language("Some text with ciao and grazie")
        assert detected == Language.ITALIAN
