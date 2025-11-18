"""
CRAFT - Chatbot & RAG Framework Toolkit

A flexible, provider-agnostic framework for building chatbots with RAG capabilities.
"""

__version__ = "1.1.0"

from craft.core.chatbot import Chatbot
from craft.core.conversation import Conversation, Message
from craft.core.context import Context

__all__ = [
    "Chatbot",
    "Conversation",
    "Message",
    "Context",
    "__version__",
]
