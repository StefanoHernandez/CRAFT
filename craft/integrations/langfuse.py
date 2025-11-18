"""
Langfuse Integration for LLM Observability

Langfuse is an open-source LLM engineering platform for debugging, analyzing, and iterating on LLM apps.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import os

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

from craft.providers.base import Message, ChatResponse


class LangfuseTracer:
    """
    Langfuse integration for CRAFT.

    Provides LLM observability, tracing, and analytics.

    Examples:
        # Initialize
        tracer = LangfuseTracer(
            public_key="pk-lf-...",
            secret_key="sk-lf-...",
        )

        # Wrap chatbot
        chatbot = Chatbot(provider=provider)
        traced_chatbot = tracer.wrap_chatbot(chatbot)

        # Use normally - traces automatically sent to Langfuse
        response = traced_chatbot.chat("Hello!")
    """

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: str = "https://cloud.langfuse.com",
        enabled: bool = True,
    ):
        """
        Initialize Langfuse tracer.

        Args:
            public_key: Langfuse public key (or set LANGFUSE_PUBLIC_KEY env var)
            secret_key: Langfuse secret key (or set LANGFUSE_SECRET_KEY env var)
            host: Langfuse host URL
            enabled: Enable/disable tracing
        """
        if not LANGFUSE_AVAILABLE:
            raise ImportError(
                "Langfuse is not installed. Install with: pip install langfuse"
            )

        self.enabled = enabled
        if not self.enabled:
            return

        self.client = Langfuse(
            public_key=public_key or os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=secret_key or os.getenv("LANGFUSE_SECRET_KEY"),
            host=host,
        )

    def trace_chat(
        self,
        messages: List[Message],
        response: ChatResponse,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Trace a chat interaction.

        Args:
            messages: Input messages
            response: Chat response
            metadata: Additional metadata
            tags: Tags for filtering
            user_id: User identifier
            session_id: Session identifier
        """
        if not self.enabled:
            return

        # Create trace
        trace = self.client.trace(
            name="chat",
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            tags=tags or [],
        )

        # Add generation
        trace.generation(
            name="llm_call",
            model=response.model or "unknown",
            input=[msg.to_dict() for msg in messages],
            output=response.content,
            usage={
                "input": response.usage.get("input_tokens", 0) if response.usage else 0,
                "output": response.usage.get("output_tokens", 0) if response.usage else 0,
            },
            metadata={
                "finish_reason": response.finish_reason,
                **(metadata or {}),
            },
        )

    def wrap_chatbot(self, chatbot):
        """
        Wrap a chatbot to automatically trace all interactions.

        Args:
            chatbot: CRAFT Chatbot instance

        Returns:
            Wrapped chatbot with tracing
        """
        if not self.enabled:
            return chatbot

        original_chat = chatbot.chat

        def traced_chat(message: str, **kwargs):
            # Call original
            response = original_chat(message, **kwargs)

            # Trace
            self.trace_chat(
                messages=chatbot.conversation.messages[-2:],  # Last user + assistant
                response=response,
                metadata={
                    "conversation_id": chatbot.conversation.id,
                    "provider": chatbot.provider.name,
                },
                session_id=chatbot.conversation.id,
            )

            return response

        chatbot.chat = traced_chat
        return chatbot

    def trace_rag_query(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        scores: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Trace a RAG retrieval.

        Args:
            query: Search query
            retrieved_docs: Retrieved documents
            scores: Relevance scores
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        trace = self.client.trace(
            name="rag_retrieval",
            metadata=metadata or {},
        )

        trace.span(
            name="retrieval",
            input={"query": query},
            output={
                "documents": retrieved_docs,
                "scores": scores or [],
                "count": len(retrieved_docs),
            },
        )

    def flush(self) -> None:
        """Flush pending traces."""
        if self.enabled:
            self.client.flush()


# Decorator for automatic tracing
def trace_llm_call(func):
    """
    Decorator to automatically trace LLM calls.

    Examples:
        @trace_llm_call
        def my_chat_function(message):
            return chatbot.chat(message)
    """
    if not LANGFUSE_AVAILABLE:
        return func

    return observe()(func)
