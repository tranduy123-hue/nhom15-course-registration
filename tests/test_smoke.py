"""
Smoke tests verifying project baseline configuration and environment.
Task: DKMH-1
Author: Trần Duy
"""
import sys
import src

def test_project_metadata():
    """Verify project package metadata and version string."""
    assert src.__version__ == "0.1.0"
    assert "CRMS" in src.__doc__

def test_python_runtime_compatibility():
    """Ensure runtime is running supported Python version (>= 3.10)."""
    assert sys.version_info >= (3, 10), "Project requires Python 3.10 or newer"

def test_test_framework_integrity():
    """Ensure basic assert semantics work as expected in test runner."""
    assert 1 + 1 == 2
    assert {"status": "ok"}["status"] == "ok"
