"""Core Chatbot class."""

from typing import Any, AsyncIterator, Optional, Union, TYPE_CHECKING
from craft.providers.base import Provider, ChatResponse, StreamChunk, Role
from craft.core.conversation import Conversation
from craft.core.context import Context
from craft.core.memory import Memory
from craft.utils.logging import get_logger

if TYPE_CHECKING:
    from craft.rag.retrieval import RetrievalEngine


class Chatbot:
    """
    Main Chatbot class that orchestrates providers, conversations, and RAG.

    This is the primary interface for building chatbots with CRAFT.
    """

    def __init__(
        self,
        provider: Provider,
        system_prompt: Optional[str] = None,
        memory: Optional[Union[bool, Memory]] = None,
        context: Optional[Context] = None,
        conversation: Optional[Conversation] = None,
        rag: Optional["RetrievalEngine"] = None,
        log_level: str = "INFO",
    ):
        """
        Initialize Chatbot.

        Args:
            provider: LLM provider instance
            system_prompt: Optional system prompt
            memory: Memory instance or True to use default in-memory storage
            context: Optional context for RAG
            conversation: Optional existing conversation
            rag: Optional RAG retrieval engine
            log_level: Logging level
        """
        self.provider = provider
        self.system_prompt = system_prompt
        self.rag = rag
        self.logger = get_logger("craft.chatbot", level=log_level)

        # Initialize memory
        if memory is True:
            self.memory = Memory()
        elif isinstance(memory, Memory):
            self.memory = memory
        else:
            self.memory = None

        # Initialize context
        self.context = context or Context()
        if system_prompt:
            self.context.system_prompt = system_prompt

        # Initialize conversation
        if conversation:
            self.conversation = conversation
        else:
            self.conversation = Conversation()
            if system_prompt:
                self.conversation.add_system_message(system_prompt)

        rag_status = "enabled" if rag else "disabled"
        self.logger.info(f"Chatbot initialized with {self.provider.name} provider (RAG: {rag_status})")

    def chat(
        self,
        message: str,
        stream: bool = False,
        save_history: bool = True,
        use_rag: bool = True,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk], str]:
        """
        Send a message and get a response.

        Args:
            message: User message
            stream: Whether to stream the response
            save_history: Whether to save messages to conversation history
            use_rag: Whether to use RAG for this query (if available)
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse, StreamChunk iterator, or string content
        """
        # Retrieve relevant context if RAG is enabled
        if self.rag and use_rag:
            self.logger.debug("Retrieving relevant context with RAG")
            retrieved_docs = self.rag.retrieve(message)

            if retrieved_docs:
                # Format context and inject into conversation
                context_text = self.rag.format_context(retrieved_docs)

                # Add context as a temporary system message
                enhanced_message = f"{context_text}\n\nUser question: {message}"

                # Add to conversation history
                if save_history:
                    self.conversation.add_user_message(message)

                # Create temporary conversation with context
                temp_conversation = Conversation()
                if self.system_prompt:
                    temp_conversation.add_system_message(self.system_prompt)

                # Add previous messages
                for msg in self.conversation.messages[:-1]:  # Exclude the last message we just added
                    temp_conversation.messages.append(msg)

                # Add enhanced message
                temp_conversation.add_user_message(enhanced_message)
                messages = temp_conversation.get_messages()
            else:
                # No relevant docs found, proceed normally
                if save_history:
                    self.conversation.add_user_message(message)
                messages = self.conversation.get_messages()
        else:
            # No RAG, proceed normally
            if save_history:
                self.conversation.add_user_message(message)
            messages = self.conversation.get_messages()

        # Get response from provider
        self.logger.debug(f"Sending message to {self.provider.name}")
        response = self.provider.chat(messages, stream=stream, **kwargs)

        if stream:
            # Handle streaming response
            return self._handle_stream(response, save_history)
        else:
            # Handle complete response
            if save_history:
                self.conversation.add_assistant_message(response.content)

            # Save to memory if enabled
            if self.memory:
                self.memory.save(self.conversation)

            self.logger.debug(f"Response received: {len(response.content)} chars")
            return response

    def _handle_stream(
        self,
        stream: AsyncIterator[StreamChunk],
        save_history: bool
    ) -> AsyncIterator[StreamChunk]:
        """Handle streaming response and save to history."""
        accumulated_content = []

        for chunk in stream:
            accumulated_content.append(chunk.content)
            yield chunk

            if chunk.finished and save_history:
                # Save complete response to history
                full_content = "".join(accumulated_content)
                self.conversation.add_assistant_message(full_content)

                # Save to memory
                if self.memory:
                    self.memory.save(self.conversation)

    async def achat(
        self,
        message: str,
        stream: bool = False,
        save_history: bool = True,
        use_rag: bool = True,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Async version of chat.

        Args:
            message: User message
            stream: Whether to stream the response
            save_history: Whether to save messages to conversation history
            use_rag: Whether to use RAG for this query (if available)
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse or async iterator of StreamChunk
        """
        # Retrieve relevant context if RAG is enabled
        if self.rag and use_rag:
            self.logger.debug("Retrieving relevant context with RAG (async)")
            retrieved_docs = await self.rag.aretrieve(message)

            if retrieved_docs:
                # Format context and inject into conversation
                context_text = self.rag.format_context(retrieved_docs)

                # Add context as a temporary system message
                enhanced_message = f"{context_text}\n\nUser question: {message}"

                # Add to conversation history
                if save_history:
                    self.conversation.add_user_message(message)

                # Create temporary conversation with context
                temp_conversation = Conversation()
                if self.system_prompt:
                    temp_conversation.add_system_message(self.system_prompt)

                # Add previous messages
                for msg in self.conversation.messages[:-1]:
                    temp_conversation.messages.append(msg)

                # Add enhanced message
                temp_conversation.add_user_message(enhanced_message)
                messages = temp_conversation.get_messages()
            else:
                # No relevant docs found, proceed normally
                if save_history:
                    self.conversation.add_user_message(message)
                messages = self.conversation.get_messages()
        else:
            # No RAG, proceed normally
            if save_history:
                self.conversation.add_user_message(message)
            messages = self.conversation.get_messages()

        # Get response from provider
        self.logger.debug(f"Sending async message to {self.provider.name}")
        response = await self.provider.achat(messages, stream=stream, **kwargs)

        if stream:
            # Handle async streaming response
            return self._handle_astream(response, save_history)
        else:
            # Handle complete response
            if save_history:
                self.conversation.add_assistant_message(response.content)

            # Save to memory if enabled
            if self.memory:
                self.memory.save(self.conversation)

            self.logger.debug(f"Response received: {len(response.content)} chars")
            return response

    async def _handle_astream(
        self,
        stream: AsyncIterator[StreamChunk],
        save_history: bool
    ) -> AsyncIterator[StreamChunk]:
        """Handle async streaming response and save to history."""
        accumulated_content = []

        async for chunk in stream:
            accumulated_content.append(chunk.content)
            yield chunk

            if chunk.finished and save_history:
                # Save complete response to history
                full_content = "".join(accumulated_content)
                self.conversation.add_assistant_message(full_content)

                # Save to memory
                if self.memory:
                    self.memory.save(self.conversation)

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation.clear()
        if self.system_prompt:
            self.conversation.add_system_message(self.system_prompt)
        self.logger.info("Conversation cleared")

    def new_conversation(self) -> None:
        """Start a new conversation."""
        self.conversation = Conversation()
        if self.system_prompt:
            self.conversation.add_system_message(self.system_prompt)
        self.logger.info("Started new conversation")

    def reset(self) -> None:
        """Reset chatbot to initial state."""
        self.conversation = Conversation()
        if self.system_prompt:
            self.conversation.add_system_message(self.system_prompt)
        self.context.clear()
        self.logger.info("Chatbot reset")

    def load_conversation(self, conversation_id: str) -> bool:
        """
        Load a conversation from memory.

        Args:
            conversation_id: Conversation ID to load

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.memory:
            self.logger.warning("Memory not enabled, cannot load conversation")
            return False

        conversation = self.memory.load(conversation_id)
        if conversation:
            self.conversation = conversation
            self.logger.info(f"Loaded conversation {conversation_id}")
            return True
        else:
            self.logger.warning(f"Conversation {conversation_id} not found")
            return False

    def save_conversation(self) -> str:
        """
        Save current conversation to memory.

        Returns:
            Conversation ID
        """
        if not self.memory:
            self.logger.warning("Memory not enabled, cannot save conversation")
            return self.conversation.id

        self.memory.save(self.conversation)
        self.logger.info(f"Saved conversation {self.conversation.id}")
        return self.conversation.id

    @property
    def conversation_id(self) -> str:
        """Get current conversation ID."""
        return self.conversation.id

    @property
    def message_count(self) -> int:
        """Get number of messages in conversation."""
        return len(self.conversation)

    def __repr__(self) -> str:
        return (
            f"Chatbot(provider={self.provider.name}, "
            f"messages={self.message_count}, "
            f"memory={'enabled' if self.memory else 'disabled'}, "
            f"rag={'enabled' if self.rag else 'disabled'})"
        )
