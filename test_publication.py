#!/usr/bin/env python3
"""
Test suite to verify CRAFT v1.3.0 before publication.

Tests:
1. Core package imports
2. Integration imports (with graceful degradation)
3. Version consistency
4. Example file syntax
5. Package structure
"""

import sys
import os
from pathlib import Path

# Colors for output
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

def test_core_imports():
    """Test core CRAFT imports."""
    print(f"\n{BOLD}1. Testing Core Imports{RESET}")

    try:
        import craft
        print_test("Import craft", True)

        # Check version
        version = craft.__version__
        expected = "1.3.0"
        if version == expected:
            print_test(f"Version {version}", True)
        else:
            print_test(f"Version mismatch", False, f"Expected {expected}, got {version}")
            return False

        # Import core components
        from craft import Chatbot, Conversation, Message, Context
        print_test("Import core components", True)

        return True
    except Exception as e:
        print_test("Core imports", False, str(e))
        return False

def test_provider_imports():
    """Test provider imports."""
    print(f"\n{BOLD}2. Testing Provider Imports{RESET}")

    try:
        from craft.providers import AnthropicProvider, OpenAIProvider, GoogleProvider
        print_test("Import providers", True)
        return True
    except Exception as e:
        print_test("Provider imports", False, str(e))
        return False

def test_integration_imports():
    """Test integration imports with graceful degradation."""
    print(f"\n{BOLD}3. Testing Integration Imports (Graceful Degradation){RESET}")

    results = []

    # Test Langfuse
    try:
        from craft.integrations.langfuse import LangfuseTracer
        print_test("Langfuse import (with lib)", True)
        results.append(True)
    except ImportError as e:
        if "langfuse" in str(e).lower():
            print_test("Langfuse import (graceful)", True, "Library not installed (OK)")
            results.append(True)
        else:
            print_test("Langfuse import", False, str(e))
            results.append(False)

    # Test Prometheus
    try:
        from craft.integrations.prometheus import PrometheusExporter
        print_test("Prometheus import (with lib)", True)
        results.append(True)
    except ImportError as e:
        if "prometheus" in str(e).lower():
            print_test("Prometheus import (graceful)", True, "Library not installed (OK)")
            results.append(True)
        else:
            print_test("Prometheus import", False, str(e))
            results.append(False)

    # Test OpenTelemetry
    try:
        from craft.integrations.opentelemetry import OpenTelemetryTracer
        print_test("OpenTelemetry import (with lib)", True)
        results.append(True)
    except ImportError as e:
        if "opentelemetry" in str(e).lower():
            print_test("OpenTelemetry import (graceful)", True, "Library not installed (OK)")
            results.append(True)
        else:
            print_test("OpenTelemetry import", False, str(e))
            results.append(False)

    # Test Sentry
    try:
        from craft.integrations.sentry import SentryIntegration
        print_test("Sentry import (with lib)", True)
        results.append(True)
    except ImportError as e:
        if "sentry" in str(e).lower():
            print_test("Sentry import (graceful)", True, "Library not installed (OK)")
            results.append(True)
        else:
            print_test("Sentry import", False, str(e))
            results.append(False)

    return all(results)

def test_rag_imports():
    """Test RAG system imports."""
    print(f"\n{BOLD}4. Testing RAG System Imports{RESET}")

    try:
        from craft.rag import RetrievalEngine
        from craft.rag.chunking import DocumentChunker
        print_test("Import RAG components", True)
        return True
    except Exception as e:
        print_test("RAG imports", False, str(e))
        return False

def test_storage_imports():
    """Test storage adapter imports."""
    print(f"\n{BOLD}5. Testing Storage Imports{RESET}")

    try:
        from craft.storage import SQLiteStorage
        print_test("Import storage adapters", True)
        return True
    except Exception as e:
        print_test("Storage imports", False, str(e))
        return False

def test_example_syntax():
    """Test example files for syntax errors."""
    print(f"\n{BOLD}6. Testing Example File Syntax{RESET}")

    examples_dir = Path("examples")
    if not examples_dir.exists():
        print_test("Examples directory", False, "Directory not found")
        return False

    integration_examples = [
        "integrations_langfuse.py",
        "integrations_prometheus.py",
        "integrations_otel.py",
        "integrations_sentry.py"
    ]

    all_valid = True
    for example in integration_examples:
        filepath = examples_dir / example
        if not filepath.exists():
            print_test(f"{example}", False, "File not found")
            all_valid = False
            continue

        try:
            with open(filepath, 'r') as f:
                code = f.read()
            compile(code, str(filepath), 'exec')
            print_test(f"{example}", True)
        except SyntaxError as e:
            print_test(f"{example}", False, f"Syntax error: {e}")
            all_valid = False

    return all_valid

def test_package_structure():
    """Test package structure and files."""
    print(f"\n{BOLD}7. Testing Package Structure{RESET}")

    required_files = [
        "craft/__init__.py",
        "craft/integrations/__init__.py",
        "craft/integrations/langfuse.py",
        "craft/integrations/prometheus.py",
        "craft/integrations/opentelemetry.py",
        "craft/integrations/sentry.py",
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        "INTEGRATIONS.md",
    ]

    all_exist = True
    for filepath in required_files:
        path = Path(filepath)
        if path.exists():
            print_test(f"{filepath}", True)
        else:
            print_test(f"{filepath}", False, "File missing")
            all_exist = False

    return all_exist

def test_version_consistency():
    """Test version consistency across files."""
    print(f"\n{BOLD}8. Testing Version Consistency{RESET}")

    expected_version = "1.3.0"

    # Check craft/__init__.py
    try:
        import craft
        craft_version = craft.__version__
        if craft_version == expected_version:
            print_test(f"craft/__init__.py: {craft_version}", True)
        else:
            print_test(f"craft/__init__.py", False, f"Expected {expected_version}, got {craft_version}")
            return False
    except Exception as e:
        print_test("craft version", False, str(e))
        return False

    # Check pyproject.toml
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()
            if f'version = "{expected_version}"' in content:
                print_test(f"pyproject.toml: {expected_version}", True)
            else:
                print_test("pyproject.toml", False, "Version mismatch")
                return False
    except Exception as e:
        print_test("pyproject.toml version", False, str(e))
        return False

    # Check CHANGELOG.md
    try:
        with open("CHANGELOG.md", "r") as f:
            content = f.read()
            if f"## [{expected_version}]" in content:
                print_test(f"CHANGELOG.md: {expected_version}", True)
            else:
                print_test("CHANGELOG.md", False, "Version not found")
                return False
    except Exception as e:
        print_test("CHANGELOG.md version", False, str(e))
        return False

    return True

def test_react_package():
    """Test React package structure."""
    print(f"\n{BOLD}9. Testing React Package{RESET}")

    react_dir = Path("craft-react")
    if not react_dir.exists():
        print_test("craft-react directory", False, "Directory not found")
        return False

    required_files = [
        "package.json",
        "dist/index.js",
        "dist/index.mjs",
        "dist/style.css",
        "dist/index.d.ts",
    ]

    all_exist = True
    for filepath in required_files:
        path = react_dir / filepath
        if path.exists():
            print_test(f"craft-react/{filepath}", True)
        else:
            print_test(f"craft-react/{filepath}", False, "File missing")
            all_exist = False

    # Check package.json version
    try:
        import json
        with open(react_dir / "package.json", "r") as f:
            pkg = json.load(f)
            if pkg.get("version") == "1.0.0":
                print_test("React package version: 1.0.0", True)
            else:
                print_test("React package version", False, f"Expected 1.0.0, got {pkg.get('version')}")
                all_exist = False
    except Exception as e:
        print_test("React package.json", False, str(e))
        all_exist = False

    return all_exist

def main():
    """Run all tests."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}CRAFT v1.3.0 - Pre-Publication Test Suite{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    # Change to CRAFT directory
    os.chdir("/home/user/CRAFT")

    tests = [
        ("Core Imports", test_core_imports),
        ("Provider Imports", test_provider_imports),
        ("Integration Imports", test_integration_imports),
        ("RAG Imports", test_rag_imports),
        ("Storage Imports", test_storage_imports),
        ("Example Syntax", test_example_syntax),
        ("Package Structure", test_package_structure),
        ("Version Consistency", test_version_consistency),
        ("React Package", test_react_package),
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
        print(f"{GREEN}{BOLD}✓ All tests passed! Ready for publication.{RESET}")
        return 0
    else:
        print(f"{RED}{BOLD}✗ Some tests failed. Please review before publishing.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
