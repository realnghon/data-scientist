"""Make the ``ds_skill`` package importable from any agent runtime.

The reusable analysis helpers live in this directory as the ``ds_skill``
package. When the plugin is installed into a tool's cache (Claude Code,
Codex, OpenCode, ...) the package is **not** automatically on ``sys.path``,
which is the usual reason an agent ends up re-writing statistics by hand
instead of calling the tested helpers.

This module removes that friction. It is intentionally dependency-free and
self-locating, so a single line makes the whole helper library available:

    # If you can run this file's directory, ds_skill is already importable.
    # Otherwise, drop the self-contained snippet from SKILL.md, or:
    import sys; sys.path.insert(0, "<this-dir>")
    import ds_bootstrap            # adds <this-dir> to sys.path (idempotent)
    from ds_skill.correlation import pairwise_correlation

Resolution order used by :func:`ensure_importable`:

1. ``ds_skill`` already importable (e.g. ``pip install -e .`` was run) -> done.
2. This file's own directory (it sits next to ``ds_skill/``).
3. ``$CLAUDE_PLUGIN_ROOT/skills/analysis-workflow/scripts`` (Claude Code/Codex).
4. ``$DS_SKILL_ROOT`` (manual override for any other runtime).
5. Walk up from the current working directory looking for the scripts dir.

Run it directly for a one-line environment smoke test::

    python ds_bootstrap.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# This file lives inside the scripts directory, alongside the ds_skill package.
SCRIPTS_DIR = Path(__file__).resolve().parent

# Relative path from a plugin root (CLAUDE_PLUGIN_ROOT / DS_SKILL_ROOT) to here.
_SKILL_SUBPATH = ("skills", "analysis-workflow", "scripts")


def _candidate_dirs() -> list[Path]:
    """Build the ordered list of directories that may contain ``ds_skill``."""
    candidates: list[Path] = [SCRIPTS_DIR]

    for env_var in ("CLAUDE_PLUGIN_ROOT", "DS_SKILL_ROOT"):
        root = os.environ.get(env_var)
        if root:
            candidates.append(Path(root, *_SKILL_SUBPATH))
            # DS_SKILL_ROOT may also point straight at the scripts dir.
            candidates.append(Path(root))

    # Walk up from the working directory; handles "running inside the repo".
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents][:10]:
        candidates.append(parent.joinpath("plugins", "data-scientist", *_SKILL_SUBPATH))
        candidates.append(parent.joinpath(*_SKILL_SUBPATH))

    return candidates


def ensure_importable() -> str:
    """Ensure ``ds_skill`` can be imported; return the scripts directory used.

    Idempotent and safe to call repeatedly. Raises :class:`ImportError` with a
    concrete fix if the package genuinely cannot be located.
    """
    try:  # Already importable (installed, or path already set up).
        import ds_skill  # noqa: F401

        return str(Path(ds_skill.__file__).resolve().parent.parent)
    except ImportError:
        pass

    for candidate in _candidate_dirs():
        if (candidate / "ds_skill" / "__init__.py").is_file():
            resolved = str(candidate.resolve())
            if resolved not in sys.path:
                sys.path.insert(0, resolved)
            return resolved

    raise ImportError(
        "Could not locate the 'ds_skill' package. Fix with one of:\n"
        "  - run `pip install -e .` in the data-scientist repo, or\n"
        "  - set DS_SKILL_ROOT to the plugin root, or\n"
        "  - add this directory to sys.path:\n"
        f"      {SCRIPTS_DIR}"
    )


# Run on import so `import ds_bootstrap` is enough to set things up.
ensure_importable()


def _check_optional_dependencies() -> dict[str, str | None]:
    """Report versions of optional analysis dependencies (None if missing)."""
    versions: dict[str, str | None] = {}
    for mod_name in ("pandas", "numpy", "scipy", "sklearn", "statsmodels", "matplotlib", "seaborn"):
        try:
            mod = __import__(mod_name)
            versions[mod_name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[mod_name] = None
    return versions


def main() -> int:
    scripts_dir = ensure_importable()
    print(f"ds_skill importable from: {scripts_dir}")
    try:
        import ds_skill

        print(f"ds_skill version: {getattr(ds_skill, '__version__', 'unknown')}")
    except ImportError as exc:  # pragma: no cover - defensive
        print(f"ds_skill import failed: {exc}")
        return 1

    print("optional dependencies:")
    for name, version in _check_optional_dependencies().items():
        status = version if version else "MISSING"
        print(f"  {name:<12} {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
