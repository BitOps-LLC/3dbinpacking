"""Shared test setup.

The repository root is not on sys.path when pytest collects `tests/` under its
default import mode, so put it there before any test module imports py3dbp.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
