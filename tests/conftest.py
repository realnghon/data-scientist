"""Pytest configuration for repo-level tests.

Puts the data-scientist skill's `scripts/` directory on `sys.path` so tests can
import `profile_dataset` and the `ds_skill` package without installing the
plugin. Test files keep their own `sys.path` insert as a fallback, but this
conftest makes the layout discoverable to any test added later.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "data-scientist" / "skills" / "data-scientist" / "scripts"

if SCRIPTS.exists():
    scripts_str = str(SCRIPTS)
    if scripts_str not in sys.path:
        sys.path.insert(0, scripts_str)
