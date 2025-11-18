#!/usr/bin/env python3
"""
Smoke tests for CRAFT v1.3.0.

Quick sanity checks to verify basic functionality before publication.
"""

import sys

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

def test_basic_imports():
    """Test that all major components can be imported."""
    print(f"\n{BOLD}Testing Basic Imports{RESET}")

    all_passed = True

    # Core
    try:
        from craft import Chatbot, Conversation, Message, Context, __version__
        print_test("craft core", True, f"v{__version__}")
    except Exception as e:
        print_test("craft core", False, str(e))
        all_passed = False

    # Providers
    try:
        from craft.providers import AnthropicProvider, OpenAIProvider, GoogleProvider
        print_test("providers", True)
    except Exception as e:
        print_test("providers", False, str(e))
        all_passed = False

    # RAG
    try:
        from craft.rag import RetrievalEngine
        from craft.rag.chunking import DocumentChunker
        print_test("RAG system", True)
    except Exception as e:
        print_test("RAG system", False, str(e))
        all_passed = False

    # Storage
    try:
        from craft.storage import SQLiteStorage
        print_test("storage", True)
    except Exception as e:
        print_test("storage", False, str(e))
        all_passed = False

    # i18n
    try:
        from craft.i18n import Translator, Language
        print_test("i18n", True)
    except Exception as e:
        print_test("i18n", False, str(e))
        all_passed = False

    # Analytics
    try:
        from craft.analytics import AnalyticsTracker
        print_test("analytics", True)
    except Exception as e:
        print_test("analytics", False, str(e))
        all_passed = False

    # Monitoring
    try:
        from craft.monitoring import HealthCheck
        print_test("monitoring", True)
    except Exception as e:
        print_test("monitoring", False, str(e))
        all_passed = False

    return all_passed

def test_integrations():
    """Test that integrations can be imported."""
    print(f"\n{BOLD}Testing Production Integrations{RESET}")

    all_passed = True

    # Langfuse
    try:
        from craft.integrations.langfuse import LangfuseTracer, LANGFUSE_AVAILABLE
        status_msg = "available" if LANGFUSE_AVAILABLE else "library not installed (OK)"
        print_test("Langfuse", True, status_msg)
    except Exception as e:
        print_test("Langfuse", False, str(e))
        all_passed = False

    # Prometheus
    try:
        from craft.integrations.prometheus import PrometheusExporter, PROMETHEUS_AVAILABLE
        status_msg = "available" if PROMETHEUS_AVAILABLE else "library not installed (OK)"
        print_test("Prometheus", True, status_msg)
    except Exception as e:
        print_test("Prometheus", False, str(e))
        all_passed = False

    # OpenTelemetry
    try:
        from craft.integrations.opentelemetry import OpenTelemetryTracer, OPENTELEMETRY_AVAILABLE
        status_msg = "available" if OPENTELEMETRY_AVAILABLE else "library not installed (OK)"
        print_test("OpenTelemetry", True, status_msg)
    except Exception as e:
        print_test("OpenTelemetry", False, str(e))
        all_passed = False

    # Sentry
    try:
        from craft.integrations.sentry import SentryIntegration, SENTRY_AVAILABLE
        status_msg = "available" if SENTRY_AVAILABLE else "library not installed (OK)"
        print_test("Sentry", True, status_msg)
    except Exception as e:
        print_test("Sentry", False, str(e))
        all_passed = False

    return all_passed

def test_react_package():
    """Test React package exists and is built."""
    print(f"\n{BOLD}Testing React Package{RESET}")

    from pathlib import Path

    all_passed = True

    react_dir = Path("craft-react")
    if not react_dir.exists():
        print_test("craft-react directory", False, "not found")
        return False

    # Check dist files
    dist_files = [
        "dist/index.js",
        "dist/index.mjs",
        "dist/style.css",
        "dist/index.d.ts",
    ]

    for file in dist_files:
        path = react_dir / file
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print_test(file, True, f"{size_kb:.1f} KB")
        else:
            print_test(file, False, "not found")
            all_passed = False

    return all_passed

def test_documentation():
    """Test that documentation files exist."""
    print(f"\n{BOLD}Testing Documentation{RESET}")

    from pathlib import Path

    all_passed = True

    docs = [
        ("README.md", "Main documentation"),
        ("CHANGELOG.md", "Version history"),
        ("INTEGRATIONS.md", "Integration guide"),
        ("craft-react/README.md", "React docs"),
    ]

    for filepath, description in docs:
        path = Path(filepath)
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print_test(f"{filepath}", True, f"{size_kb:.1f} KB")
        else:
            print_test(f"{filepath}", False, "not found")
            all_passed = False

    return all_passed

def test_examples():
    """Test that example files exist and have valid syntax."""
    print(f"\n{BOLD}Testing Integration Examples{RESET}")

    from pathlib import Path

    all_passed = True

    examples = [
        "integrations_langfuse.py",
        "integrations_prometheus.py",
        "integrations_otel.py",
        "integrations_sentry.py",
    ]

    examples_dir = Path("examples")

    for example in examples:
        filepath = examples_dir / example
        if not filepath.exists():
            print_test(example, False, "not found")
            all_passed = False
            continue

        try:
            with open(filepath, 'r') as f:
                code = f.read()
            compile(code, str(filepath), 'exec')
            lines = len(code.splitlines())
            print_test(example, True, f"{lines} lines")
        except SyntaxError as e:
            print_test(example, False, f"syntax error: {e}")
            all_passed = False

    return all_passed

def main():
    """Run all smoke tests."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}CRAFT v1.3.0 - Smoke Test Suite{RESET}")
    print(f"{BOLD}Quick sanity checks before publication{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    tests = [
        ("Basic Imports", test_basic_imports),
        ("Production Integrations", test_integrations),
        ("React Package", test_react_package),
        ("Documentation", test_documentation),
        ("Integration Examples", test_examples),
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
    print(f"{BOLD}Summary{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        symbol = "✓" if result else "✗"
        color = GREEN if result else RED
        print(f"{color}{symbol}{RESET} {name}")

    print(f"\n{BOLD}Results: {passed}/{total} test suites passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}{BOLD}✅ ALL SMOKE TESTS PASSED!{RESET}")
        print(f"{GREEN}CRAFT v1.3.0 is ready for publication.{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ Some tests failed.{RESET}")
        print(f"{RED}Please review failures before publishing.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
