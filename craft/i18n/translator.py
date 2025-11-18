"""Translation and i18n utilities."""

from enum import Enum
from typing import Dict, Optional
import json
from pathlib import Path


class Language(str, Enum):
    """Supported languages."""

    ENGLISH = "en"
    ITALIAN = "it"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    RUSSIAN = "ru"


class Translator:
    """
    Multi-language translation support.

    Provides translations for system messages, UI text, and error messages.

    Examples:
        translator = Translator(language=Language.ITALIAN)
        print(translator.get("welcome"))  # "Benvenuto in CRAFT"

        # Auto-detect language
        translator = Translator.auto_detect("Ciao, come stai?")
    """

    def __init__(self, language: Language = Language.ENGLISH):
        """
        Initialize translator.

        Args:
            language: Target language
        """
        self.language = language
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translation files."""
        translations_dir = Path(__file__).parent / "translations"

        if not translations_dir.exists():
            # Use built-in translations
            self.translations = _BUILTIN_TRANSLATIONS
            return

        # Load from files
        for lang_file in translations_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except Exception:
                pass

        # Fallback to built-in
        if not self.translations:
            self.translations = _BUILTIN_TRANSLATIONS

    def get(self, key: str, **kwargs) -> str:
        """
        Get translated text.

        Args:
            key: Translation key
            **kwargs: Format parameters

        Returns:
            Translated text
        """
        # Get translation for current language
        lang_dict = self.translations.get(self.language.value, {})
        text = lang_dict.get(key)

        # Fallback to English
        if not text:
            text = self.translations.get(Language.ENGLISH.value, {}).get(key, key)

        # Format with parameters
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass

        return text

    def translate_prompt(self, prompt: str, target_language: Optional[Language] = None) -> str:
        """
        Add language instruction to prompt.

        Args:
            prompt: Original prompt
            target_language: Target language (uses self.language if None)

        Returns:
            Prompt with language instruction
        """
        lang = target_language or self.language

        if lang == Language.ENGLISH:
            return prompt

        lang_instruction = self.get("respond_in_language", language=self.get(f"language_name_{lang.value}"))
        return f"{lang_instruction}\n\n{prompt}"

    @classmethod
    def auto_detect(cls, text: str) -> "Translator":
        """
        Auto-detect language and create translator.

        Args:
            text: Text to analyze

        Returns:
            Translator configured for detected language
        """
        language = detect_language(text)
        return cls(language=language)


def detect_language(text: str) -> Language:
    """
    Detect language from text (simple heuristic-based).

    Args:
        text: Text to analyze

    Returns:
        Detected language
    """
    text_lower = text.lower()

    # Simple keyword-based detection
    if any(word in text_lower for word in ["ciao", "grazie", "prego", "come stai"]):
        return Language.ITALIAN
    elif any(word in text_lower for word in ["hola", "gracias", "buenos días", "cómo estás"]):
        return Language.SPANISH
    elif any(word in text_lower for word in ["bonjour", "merci", "comment allez-vous", "s'il vous plaît"]):
        return Language.FRENCH
    elif any(word in text_lower for word in ["hallo", "danke", "wie geht", "bitte"]):
        return Language.GERMAN
    elif any(word in text_lower for word in ["olá", "obrigado", "como vai", "por favor"]):
        return Language.PORTUGUESE
    elif any(char >= '\u4e00' and char <= '\u9fff' for char in text):
        return Language.CHINESE
    elif any(char >= '\u3040' and char <= '\u30ff' for char in text):
        return Language.JAPANESE
    elif any(char >= '\uac00' and char <= '\ud7af' for char in text):
        return Language.KOREAN
    elif any(char >= '\u0400' and char <= '\u04ff' for char in text):
        return Language.RUSSIAN

    # Default to English
    return Language.ENGLISH


# Built-in translations
_BUILTIN_TRANSLATIONS = {
    "en": {
        "welcome": "Welcome to CRAFT",
        "goodbye": "Goodbye!",
        "error": "An error occurred",
        "conversation_started": "Conversation started",
        "conversation_ended": "Conversation ended",
        "message_sent": "Message sent",
        "message_received": "Message received",
        "respond_in_language": "Please respond in {language}.",
        "language_name_en": "English",
        "language_name_it": "Italian",
        "language_name_es": "Spanish",
        "language_name_fr": "French",
        "language_name_de": "German",
        "language_name_pt": "Portuguese",
        "language_name_zh": "Chinese",
        "language_name_ja": "Japanese",
        "language_name_ko": "Korean",
        "language_name_ru": "Russian",
        "connection_error": "Connection error",
        "timeout_error": "Request timeout",
        "rate_limit_error": "Rate limit exceeded",
        "invalid_api_key": "Invalid API key",
        "server_error": "Server error",
    },
    "it": {
        "welcome": "Benvenuto in CRAFT",
        "goodbye": "Arrivederci!",
        "error": "Si è verificato un errore",
        "conversation_started": "Conversazione iniziata",
        "conversation_ended": "Conversazione terminata",
        "message_sent": "Messaggio inviato",
        "message_received": "Messaggio ricevuto",
        "respond_in_language": "Per favore rispondi in {language}.",
        "language_name_en": "Inglese",
        "language_name_it": "Italiano",
        "language_name_es": "Spagnolo",
        "language_name_fr": "Francese",
        "language_name_de": "Tedesco",
        "language_name_pt": "Portoghese",
        "language_name_zh": "Cinese",
        "language_name_ja": "Giapponese",
        "language_name_ko": "Coreano",
        "language_name_ru": "Russo",
        "connection_error": "Errore di connessione",
        "timeout_error": "Timeout della richiesta",
        "rate_limit_error": "Limite di richieste superato",
        "invalid_api_key": "Chiave API non valida",
        "server_error": "Errore del server",
    },
    "es": {
        "welcome": "Bienvenido a CRAFT",
        "goodbye": "¡Adiós!",
        "error": "Ocurrió un error",
        "conversation_started": "Conversación iniciada",
        "conversation_ended": "Conversación finalizada",
        "message_sent": "Mensaje enviado",
        "message_received": "Mensaje recibido",
        "respond_in_language": "Por favor responde en {language}.",
        "language_name_en": "Inglés",
        "language_name_it": "Italiano",
        "language_name_es": "Español",
        "language_name_fr": "Francés",
        "language_name_de": "Alemán",
        "language_name_pt": "Portugués",
        "language_name_zh": "Chino",
        "language_name_ja": "Japonés",
        "language_name_ko": "Coreano",
        "language_name_ru": "Ruso",
        "connection_error": "Error de conexión",
        "timeout_error": "Tiempo de espera agotado",
        "rate_limit_error": "Límite de tasa excedido",
        "invalid_api_key": "Clave API inválida",
        "server_error": "Error del servidor",
    },
    "fr": {
        "welcome": "Bienvenue dans CRAFT",
        "goodbye": "Au revoir!",
        "error": "Une erreur s'est produite",
        "conversation_started": "Conversation démarrée",
        "conversation_ended": "Conversation terminée",
        "message_sent": "Message envoyé",
        "message_received": "Message reçu",
        "respond_in_language": "Veuillez répondre en {language}.",
        "language_name_en": "Anglais",
        "language_name_it": "Italien",
        "language_name_es": "Espagnol",
        "language_name_fr": "Français",
        "language_name_de": "Allemand",
        "language_name_pt": "Portugais",
        "language_name_zh": "Chinois",
        "language_name_ja": "Japonais",
        "language_name_ko": "Coréen",
        "language_name_ru": "Russe",
        "connection_error": "Erreur de connexion",
        "timeout_error": "Délai d'attente dépassé",
        "rate_limit_error": "Limite de taux dépassée",
        "invalid_api_key": "Clé API invalide",
        "server_error": "Erreur du serveur",
    },
    "de": {
        "welcome": "Willkommen bei CRAFT",
        "goodbye": "Auf Wiedersehen!",
        "error": "Ein Fehler ist aufgetreten",
        "conversation_started": "Gespräch gestartet",
        "conversation_ended": "Gespräch beendet",
        "message_sent": "Nachricht gesendet",
        "message_received": "Nachricht empfangen",
        "respond_in_language": "Bitte antworte auf {language}.",
        "language_name_en": "Englisch",
        "language_name_it": "Italienisch",
        "language_name_es": "Spanisch",
        "language_name_fr": "Französisch",
        "language_name_de": "Deutsch",
        "language_name_pt": "Portugiesisch",
        "language_name_zh": "Chinesisch",
        "language_name_ja": "Japanisch",
        "language_name_ko": "Koreanisch",
        "language_name_ru": "Russisch",
        "connection_error": "Verbindungsfehler",
        "timeout_error": "Zeitüberschreitung",
        "rate_limit_error": "Ratenlimit überschritten",
        "invalid_api_key": "Ungültiger API-Schlüssel",
        "server_error": "Serverfehler",
    },
    "pt": {
        "welcome": "Bem-vindo ao CRAFT",
        "goodbye": "Adeus!",
        "error": "Ocorreu um erro",
        "conversation_started": "Conversa iniciada",
        "conversation_ended": "Conversa encerrada",
        "message_sent": "Mensagem enviada",
        "message_received": "Mensagem recebida",
        "respond_in_language": "Por favor responda em {language}.",
        "language_name_en": "Inglês",
        "language_name_it": "Italiano",
        "language_name_es": "Espanhol",
        "language_name_fr": "Francês",
        "language_name_de": "Alemão",
        "language_name_pt": "Português",
        "language_name_zh": "Chinês",
        "language_name_ja": "Japonês",
        "language_name_ko": "Coreano",
        "language_name_ru": "Russo",
        "connection_error": "Erro de conexão",
        "timeout_error": "Tempo esgotado",
        "rate_limit_error": "Limite de taxa excedido",
        "invalid_api_key": "Chave API inválida",
        "server_error": "Erro do servidor",
    },
}
