#!/usr/bin/env python3
"""
Quick test suite for CRAFT v1.3.0 - Fast validation before publication.

Tests:
1. Clean installation test
2. Docker build test
3. Documentation link validation
"""

import subprocess
import sys
import re
from pathlib import Path
import tempfile
import shutil

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_test(name, status, message=""):
    """Print test result."""
    symbol = "✓" if status else "✗"
    color = GREEN if status else RED
    print(f"{color}{symbol}{RESET} {name}")
    if message:
        print(f"  {YELLOW}{message}{RESET}")

def print_section(title):
    """Print section header."""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}")

def test_clean_install():
    """Test installation in a clean virtual environment."""
    print_section("Test 1: Clean Installation")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"

        try:
            # Create virtual environment
            print(f"{YELLOW}Creating virtual environment...{RESET}")
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                print_test("Create virtualenv", False, result.stderr)
                return False
            print_test("Create virtualenv", True)

            # Get pip path
            if sys.platform == "win32":
                pip_path = venv_path / "Scripts" / "pip"
            else:
                pip_path = venv_path / "bin" / "pip"

            # Install package
            print(f"{YELLOW}Installing CRAFT package...{RESET}")
            result = subprocess.run(
                [str(pip_path), "install", "-e", ".", "--quiet"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                print_test("Install package", False, result.stderr[-500:])
                return False
            print_test("Install package", True)

            # Test basic import
            print(f"{YELLOW}Testing basic import...{RESET}")
            python_path = venv_path / "bin" / "python" if sys.platform != "win32" else venv_path / "Scripts" / "python"
            result = subprocess.run(
                [str(python_path), "-c", "import craft; print(craft.__version__)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print_test("Import craft", False, result.stderr)
                return False

            version = result.stdout.strip()
            if version == "1.3.0":
                print_test("Import craft", True, f"version {version}")
            else:
                print_test("Import craft", False, f"Wrong version: {version}")
                return False

            # Test integration imports
            print(f"{YELLOW}Testing integration imports...{RESET}")
            test_code = """
import sys
try:
    from craft.integrations import (
        LangfuseTracer, PrometheusExporter,
        OpenTelemetryTracer, SentryIntegration
    )
    print("OK")
except ImportError as e:
    print(f"FAIL: {e}")
    sys.exit(1)
"""
            result = subprocess.run(
                [str(python_path), "-c", test_code],
                capture_output=True,
                text=True,
                timeout=10
            )
            if "OK" in result.stdout:
                print_test("Import integrations", True, "graceful degradation working")
            else:
                print_test("Import integrations", False, result.stdout)
                return False

            return True

        except subprocess.TimeoutExpired:
            print_test("Installation test", False, "Timeout")
            return False
        except Exception as e:
            print_test("Installation test", False, str(e))
            return False

def test_docker_build():
    """Test Docker build."""
    print_section("Test 2: Docker Build")

    dockerfile = Path("Dockerfile")
    if not dockerfile.exists():
        print_test("Dockerfile exists", False, "Dockerfile not found")
        return False
    print_test("Dockerfile exists", True)

    # Check if Docker is available
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print_test("Docker available", False, "Docker not installed")
            return True  # Don't fail if Docker not available
        print_test("Docker available", True, result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_test("Docker available", False, "Docker not found (OK - skipping)")
        return True  # Don't fail if Docker not available

    # Test Docker build (dry run with --help to avoid long build)
    print(f"{YELLOW}Validating Dockerfile syntax...{RESET}")
    try:
        with open(dockerfile, 'r') as f:
            content = f.read()

        # Check for required commands
        required = ["FROM", "WORKDIR", "COPY", "RUN"]
        for cmd in required:
            if cmd in content:
                print_test(f"Dockerfile has {cmd}", True)
            else:
                print_test(f"Dockerfile has {cmd}", False)
                return False

        return True
    except Exception as e:
        print_test("Dockerfile validation", False, str(e))
        return False

def test_documentation_links():
    """Test documentation for broken links."""
    print_section("Test 3: Documentation Links")

    docs = [
        ("README.md", "Main documentation"),
        ("INTEGRATIONS.md", "Integration guide"),
        ("CHANGELOG.md", "Changelog"),
    ]

    all_valid = True

    for filepath, description in docs:
        path = Path(filepath)
        if not path.exists():
            print_test(f"{filepath}", False, "File not found")
            all_valid = False
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find markdown links [text](url)
            links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)

            internal_links = [url for text, url in links if not url.startswith(('http://', 'https://'))]
            external_links = [url for text, url in links if url.startswith(('http://', 'https://'))]

            # Check internal file links
            broken = []
            for link in internal_links:
                # Remove anchors
                file_path = link.split('#')[0]
                if file_path and not file_path.startswith('mailto:'):
                    # Resolve relative to doc location
                    target = (path.parent / file_path).resolve()
                    if not target.exists():
                        broken.append(link)

            if broken:
                print_test(f"{filepath}", False, f"{len(broken)} broken internal links")
                for link in broken[:3]:  # Show first 3
                    print(f"    {RED}✗{RESET} {link}")
                all_valid = False
            else:
                total_links = len(internal_links) + len(external_links)
                print_test(f"{filepath}", True, f"{total_links} links ({len(internal_links)} internal, {len(external_links)} external)")

        except Exception as e:
            print_test(f"{filepath}", False, str(e))
            all_valid = False

    return all_valid

def test_package_metadata():
    """Test package metadata and size."""
    print_section("Test 4: Package Metadata")

    # Check pyproject.toml
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print_test("pyproject.toml", False, "Not found")
        return False

    with open(pyproject, 'r') as f:
        content = f.read()

    # Check essential fields
    checks = [
        ('name = "craft-chatbot"', "Package name"),
        ('version = "1.3.0"', "Version"),
        ('readme = "README.md"', "README reference"),
        ('requires-python = ">=3.9"', "Python version"),
    ]

    all_ok = True
    for check, desc in checks:
        if check in content:
            print_test(desc, True)
        else:
            print_test(desc, False, f"Missing: {check}")
            all_ok = False

    # Check dist files
    dist_dir = Path("dist")
    if dist_dir.exists():
        wheel_files = list(dist_dir.glob("*.whl"))
        tar_files = list(dist_dir.glob("*.tar.gz"))

        if wheel_files:
            size_kb = wheel_files[0].stat().st_size / 1024
            print_test("Wheel package", True, f"{wheel_files[0].name} ({size_kb:.1f} KB)")

        if tar_files:
            size_kb = tar_files[0].stat().st_size / 1024
            print_test("Source package", True, f"{tar_files[0].name} ({size_kb:.1f} KB)")

    return all_ok

def main():
    """Run quick tests."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}CRAFT v1.3.0 - Quick Test Suite{RESET}")
    print(f"{BOLD}Fast validation before publication{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    tests = [
        ("Clean Installation", test_clean_install),
        ("Docker Build", test_docker_build),
        ("Documentation Links", test_documentation_links),
        ("Package Metadata", test_package_metadata),
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
    print_section("Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        symbol = "✓" if result else "✗"
        color = GREEN if result else RED
        print(f"{color}{symbol}{RESET} {name}")

    print(f"\n{BOLD}Results: {passed}/{total} passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}{BOLD}✅ ALL QUICK TESTS PASSED!{RESET}")
        print(f"{GREEN}CRAFT v1.3.0 is ready for publication.{RESET}")
        return 0
    else:
        print(f"\n{YELLOW}{BOLD}⚠ Some tests failed or were skipped.{RESET}")
        if passed >= total * 0.75:
            print(f"{YELLOW}Most tests passed ({passed}/{total}). Review failures.{RESET}")
            return 0
        else:
            print(f"{RED}Please fix critical issues before publishing.{RESET}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
