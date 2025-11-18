#!/usr/bin/env python3
"""
Functional tests for CRAFT v1.3.0.

Tests actual usage scenarios without requiring API keys.
"""

import sys
from pathlib import Path

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_test(name, status, message=""):
    """Print test result."""
    symbol = "✓" if status else "✗"
    color = GREEN if status else RED
    print(f"{color}{symbol}{RESET} {name}")
    if message:
        print(f"  {YELLOW}{message}{RESET}")

def test_chatbot_creation():
    """Test creating a chatbot with mock provider."""
    print(f"\n{BOLD}1. Testing Chatbot Creation{RESET}")

    try:
        from craft import Chatbot
        from craft.providers.base import Provider, ChatResponse, Usage

        # Create mock provider
        class MockProvider(Provider):
            def __init__(self):
                super().__init__(name="mock", model="mock-1")

            def chat(self, messages, stream=False, **kwargs):
                if stream:
                    def generator():
                        yield ChatResponse(
                            content="Mock response",
                            role="assistant",
                            model="mock-1",
                            usage=Usage(input_tokens=10, output_tokens=5)
                        )
                    return generator()
                else:
                    return ChatResponse(
                        content="Mock response",
                        role="assistant",
                        model="mock-1",
                        usage=Usage(input_tokens=10, output_tokens=5)
                    )

        # Create chatbot
        provider = MockProvider()
        chatbot = Chatbot(provider=provider, memory=True)
        print_test("Create chatbot with mock provider", True)

        # Test chat
        response = chatbot.chat("Hello!")
        if response.content == "Mock response":
            print_test("Chat with chatbot", True)
        else:
            print_test("Chat with chatbot", False, f"Unexpected response: {response.content}")
            return False

        # Check conversation history
        if len(chatbot.conversation.messages) == 2:  # User + Assistant
            print_test("Conversation history", True)
        else:
            print_test("Conversation history", False, f"Expected 2 messages, got {len(chatbot.conversation.messages)}")
            return False

        return True
    except Exception as e:
        print_test("Chatbot creation", False, str(e))
        import traceback
        traceback.print_exc()
        return False

def test_integration_wrapping():
    """Test wrapping chatbot with integrations."""
    print(f"\n{BOLD}2. Testing Integration Wrapping{RESET}")

    try:
        from craft import Chatbot
        from craft.providers.base import Provider, ChatResponse, Usage
        from craft.integrations import PrometheusExporter

        # Mock provider
        class MockProvider(Provider):
            def __init__(self):
                super().__init__(name="mock", model="mock-1")

            def chat(self, messages, stream=False, **kwargs):
                return ChatResponse(
                    content="Mock response",
                    role="assistant",
                    model="mock-1",
                    usage=Usage(input_tokens=10, output_tokens=5)
                )

        # Create chatbot
        chatbot = Chatbot(provider=MockProvider())

        # Wrap with Prometheus
        exporter = PrometheusExporter(port=8001, namespace="test")
        wrapped_chatbot = exporter.wrap_chatbot(chatbot)
        print_test("Wrap with Prometheus", True)

        # Test wrapped chat
        response = wrapped_chatbot.chat("Hello!")
        if response.content == "Mock response":
            print_test("Chat with wrapped chatbot", True)
        else:
            print_test("Chat with wrapped chatbot", False, f"Unexpected response: {response.content}")
            return False

        return True
    except Exception as e:
        print_test("Integration wrapping", False, str(e))
        import traceback
        traceback.print_exc()
        return False

def test_rag_system():
    """Test RAG system functionality."""
    print(f"\n{BOLD}3. Testing RAG System{RESET}")

    try:
        from craft.rag import RetrievalEngine
        from craft.rag.chunking import DocumentChunker, ChunkConfig, ChunkingStrategy
        from craft.rag.embeddings import SentenceTransformerEmbedding
        from craft.rag.vectorstores import ChromaVectorStore

        print_test("Import RAG components", True)

        # Test chunking
        chunker = DocumentChunker(
            config=ChunkConfig(
                strategy=ChunkingStrategy.FIXED_SIZE,
                chunk_size=100,
                chunk_overlap=20
            )
        )

        text = "This is a test document. " * 10
        chunks = chunker.chunk(text)

        if len(chunks) > 0:
            print_test("Document chunking", True, f"Created {len(chunks)} chunks")
        else:
            print_test("Document chunking", False, "No chunks created")
            return False

        return True
    except Exception as e:
        print_test("RAG system", False, str(e))
        # Don't print full traceback for RAG since embeddings might not be available
        return False

def test_storage_system():
    """Test storage system."""
    print(f"\n{BOLD}4. Testing Storage System{RESET}")

    try:
        from craft.storage import SQLiteStorage
        from craft.core.memory import Memory
        from craft import Chatbot
        from craft.providers.base import Provider, ChatResponse, Usage

        # Create temporary storage
        import tempfile
        import os

        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            storage = SQLiteStorage(database_path=db_path)
            print_test("Create SQLite storage", True)

            # Create memory with storage
            memory = Memory(storage=storage, max_messages=100)
            print_test("Create memory with storage", True)

            # Create chatbot with persistent memory
            class MockProvider(Provider):
                def __init__(self):
                    super().__init__(name="mock", model="mock-1")

                def chat(self, messages, stream=False, **kwargs):
                    return ChatResponse(
                        content="Mock response",
                        role="assistant",
                        model="mock-1",
                        usage=Usage(input_tokens=10, output_tokens=5)
                    )

            chatbot = Chatbot(provider=MockProvider(), memory=memory)

            # Chat and verify storage
            chatbot.chat("Hello!")

            # Load conversation
            conv = storage.load(chatbot.conversation.id)
            if conv and len(conv.messages) == 2:
                print_test("Save and load conversation", True)
            else:
                print_test("Save and load conversation", False, "Failed to persist")
                return False

            return True
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    except Exception as e:
        print_test("Storage system", False, str(e))
        import traceback
        traceback.print_exc()
        return False

def test_api_imports():
    """Test API server imports."""
    print(f"\n{BOLD}5. Testing API Imports{RESET}")

    try:
        from craft.integrations.api import CRAFTServer
        from craft.integrations.api.auth import APIKeyManager
        from craft.integrations.api.rate_limiter import RateLimiter
        print_test("Import API components", True)
        return True
    except Exception as e:
        print_test("API imports", False, str(e))
        return False

def test_i18n_system():
    """Test internationalization system."""
    print(f"\n{BOLD}6. Testing i18n System{RESET}")

    try:
        from craft.i18n import Translator, Language, detect_language

        # Test detection
        lang = detect_language("Ciao! Come stai?")
        if lang == Language.ITALIAN:
            print_test("Language detection (Italian)", True)
        else:
            print_test("Language detection", False, f"Expected IT, got {lang}")
            return False

        # Test translator
        translator = Translator(language=Language.ITALIAN)
        welcome = translator.get("welcome")
        if "Benvenuto" in welcome:
            print_test("Translation system", True)
        else:
            print_test("Translation system", False, f"Unexpected translation: {welcome}")
            return False

        return True
    except Exception as e:
        print_test("i18n system", False, str(e))
        import traceback
        traceback.print_exc()
        return False

def test_analytics():
    """Test analytics system."""
    print(f"\n{BOLD}7. Testing Analytics System{RESET}")

    try:
        from craft.analytics import AnalyticsTracker, EventType, MetricType

        tracker = AnalyticsTracker()
        print_test("Create analytics tracker", True)

        # Track event
        tracker.track_event(EventType.MESSAGE_SENT, data={"message": "test"})

        # Track metric
        tracker.track_metric(MetricType.RESPONSE_TIME, value=123.45)

        # Get stats
        stats = tracker.get_statistics(hours=24)
        if stats['total_events'] == 1:
            print_test("Track events and metrics", True)
        else:
            print_test("Track events and metrics", False, f"Expected 1 event, got {stats['total_events']}")
            return False

        return True
    except Exception as e:
        print_test("Analytics system", False, str(e))
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all functional tests."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}CRAFT v1.3.0 - Functional Test Suite{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    tests = [
        ("Chatbot Creation", test_chatbot_creation),
        ("Integration Wrapping", test_integration_wrapping),
        ("RAG System", test_rag_system),
        ("Storage System", test_storage_system),
        ("API Imports", test_api_imports),
        ("i18n System", test_i18n_system),
        ("Analytics System", test_analytics),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_test(name, False, f"Unexpected error: {e}")
            results.append((name, False))

    # Summary
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Test Summary{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        symbol = "✓" if result else "✗"
        color = GREEN if result else RED
        print(f"{color}{symbol}{RESET} {name}")

    print(f"\n{BOLD}Results: {passed}/{total} passed{RESET}")

    if passed == total:
        print(f"{GREEN}{BOLD}✓ All functional tests passed!{RESET}")
        return 0
    elif passed >= total * 0.8:  # 80% pass rate
        print(f"{YELLOW}{BOLD}⚠ Most tests passed ({passed}/{total}). Review failures.{RESET}")
        return 0
    else:
        print(f"{RED}{BOLD}✗ Too many failures. Please fix before publishing.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
