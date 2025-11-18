"""
Langfuse Integration Example

Demonstrates LLM observability and tracing with Langfuse.
"""

import os
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.integrations import LangfuseTracer

# Example 1: Basic tracing
def basic_tracing():
    """Basic chatbot with Langfuse tracing."""
    # Initialize tracer
    tracer = LangfuseTracer(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host="https://cloud.langfuse.com",  # Or self-hosted URL
    )

    # Create chatbot
    provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
    chatbot = Chatbot(provider=provider)

    # Wrap with tracing
    traced_chatbot = tracer.wrap_chatbot(chatbot)

    # All interactions automatically traced
    response = traced_chatbot.chat("What is machine learning?")
    print(response.content)

    # View traces in Langfuse dashboard


# Example 2: Custom metadata and tags
def custom_metadata():
    """Add custom metadata and tags to traces."""
    tracer = LangfuseTracer()
    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)

    # Manual tracing with metadata
    messages = [{"role": "user", "content": "Explain quantum computing"}]
    response = chatbot.chat("Explain quantum computing")

    tracer.trace_chat(
        messages=chatbot.conversation.messages,
        response=response,
        metadata={
            "user_type": "premium",
            "feature": "technical_support",
            "version": "1.0.0",
        },
        tags=["quantum", "technical", "education"],
        user_id="user_123",
        session_id=chatbot.conversation.id,
    )


# Example 3: RAG tracing
def rag_tracing():
    """Trace RAG retrieval operations."""
    from craft.rag import RAGSystem
    from craft.rag.vector_stores import ChromaVectorStore

    tracer = LangfuseTracer()

    # Setup RAG
    vector_store = ChromaVectorStore()
    rag = RAGSystem(vector_store=vector_store)

    # Add documents
    rag.add_documents([
        "Python is a programming language.",
        "Machine learning uses algorithms to learn from data.",
        "Neural networks are inspired by the brain.",
    ])

    # Query and trace
    query = "What is Python?"
    results = rag.query(query, top_k=2)

    # Trace retrieval
    tracer.trace_rag_query(
        query=query,
        retrieved_docs=[
            {"content": doc.content, "metadata": doc.metadata}
            for doc in results
        ],
        scores=[doc.score for doc in results],
        metadata={
            "vector_store": "chroma",
            "top_k": 2,
        },
    )


# Example 4: Function decorator
def decorator_example():
    """Use decorator for automatic tracing."""
    from craft.integrations.langfuse import trace_llm_call

    tracer = LangfuseTracer()
    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)

    @trace_llm_call
    def ask_question(question: str) -> str:
        """Traced function."""
        response = chatbot.chat(question)
        return response.content

    # Automatically traced
    answer = ask_question("What is AI?")
    print(answer)


# Example 5: Multi-turn conversation
def conversation_tracing():
    """Trace entire conversation."""
    tracer = LangfuseTracer()
    provider = AnthropicProvider()
    chatbot = Chatbot(provider=provider)

    traced_chatbot = tracer.wrap_chatbot(chatbot)

    # All turns traced with same session_id
    traced_chatbot.chat("Hello!")
    traced_chatbot.chat("What can you help me with?")
    traced_chatbot.chat("Tell me about Python")

    # Flush to ensure all traces sent
    tracer.flush()

    print(f"Session ID: {chatbot.conversation.id}")
    print("View complete conversation in Langfuse dashboard")


if __name__ == "__main__":
    print("Langfuse Integration Examples\n")

    # Run examples
    print("1. Basic tracing...")
    basic_tracing()

    print("\n2. Custom metadata...")
    custom_metadata()

    print("\n3. RAG tracing...")
    rag_tracing()

    print("\n4. Decorator example...")
    decorator_example()

    print("\n5. Conversation tracing...")
    conversation_tracing()

    print("\n✅ All examples completed!")
    print("View traces at: https://cloud.langfuse.com")
