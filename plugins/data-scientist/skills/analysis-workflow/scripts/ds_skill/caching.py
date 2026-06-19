"""Caching utilities for expensive computations.

Provides optional disk-based caching for bootstrap, permutation tests,
and other computationally expensive operations.

Usage:
    from ds_skill.caching import cached_computation

    @cached_computation(cache_dir=".cache/bootstrap")
    def expensive_bootstrap(data, n_iterations=10000):
        # ... expensive computation
        return result
"""

from __future__ import annotations

import functools
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Callable, TypeVar

import numpy as np
import pandas as pd
from pandas.util import hash_pandas_object

F = TypeVar('F', bound=Callable[..., Any])


def _fingerprint(obj: Any) -> Any:
    """Content-based, JSON-stable fingerprint of a single argument.

    DataFrames / Series are hashed over their FULL contents and ndarrays over
    their full bytes. (The previous head/tail-of-3 sketch collided whenever two
    datasets shared their first and last rows — e.g. same shape, different middle
    — silently returning one dataset's cached statistic for another.) Anything
    else is returned as-is for ``json.dumps(default=str)`` to render.
    """
    if isinstance(obj, pd.DataFrame):
        row_hash = hash_pandas_object(obj, index=True).to_numpy()
        return {
            'type': 'DataFrame',
            'shape': list(obj.shape),
            'columns': [str(c) for c in obj.columns],
            'content': hashlib.sha256(np.ascontiguousarray(row_hash).tobytes()).hexdigest(),
        }
    if isinstance(obj, pd.Series):
        row_hash = hash_pandas_object(obj, index=True).to_numpy()
        return {
            'type': 'Series',
            'name': str(obj.name),
            'content': hashlib.sha256(np.ascontiguousarray(row_hash).tobytes()).hexdigest(),
        }
    if isinstance(obj, np.ndarray):
        return {
            'type': 'ndarray',
            'shape': list(obj.shape),
            'dtype': str(obj.dtype),
            'content': hashlib.sha256(np.ascontiguousarray(obj).tobytes()).hexdigest(),
        }
    return obj


def _hash_args(*args: Any, **kwargs: Any) -> str:
    """Create a stable, content-aware hash of function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Hex digest of the arguments
    """
    stable_repr: list[Any] = [_fingerprint(arg) for arg in args]
    for key, value in sorted(kwargs.items()):
        stable_repr.append({key: _fingerprint(value)})

    # Hash the JSON representation
    json_repr = json.dumps(stable_repr, sort_keys=True, default=str)
    return hashlib.sha256(json_repr.encode()).hexdigest()[:16]


def cached_computation(
    cache_dir: str | Path = ".cache",
    *,
    enabled: bool = True,
    verbose: bool = False,
) -> Callable[[F], F]:
    """Decorator to cache expensive computations to disk.

    Security note: cache entries are loaded with ``pickle``, which executes
    arbitrary code on unpickling. Only point ``cache_dir`` at a location you
    trust (not a world-writable or shared directory).

    Args:
        cache_dir: Directory to store cache files
        enabled: Whether caching is enabled (set to False to disable)
        verbose: Whether to print cache hit/miss messages

    Returns:
        Decorated function

    Example:
        @cached_computation(cache_dir=".cache/bootstrap", verbose=True)
        def bootstrap_ci(data, n_iterations=10000):
            # ... expensive computation
            return result

        # First call: computes and caches
        result1 = bootstrap_ci(df, n_iterations=10000)

        # Second call with same args: loads from cache
        result2 = bootstrap_ci(df, n_iterations=10000)
    """
    cache_path = Path(cache_dir)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not enabled:
                return func(*args, **kwargs)

            # Create cache directory
            cache_path.mkdir(parents=True, exist_ok=True)

            # Generate cache key
            arg_hash = _hash_args(*args, **kwargs)
            cache_file = cache_path / f"{func.__name__}_{arg_hash}.pkl"

            # Check cache
            if cache_file.exists():
                if verbose:
                    print(f"[Cache HIT] Loading {func.__name__} from {cache_file.name}")
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)

            # Compute
            if verbose:
                print(f"[Cache MISS] Computing {func.__name__}...")
            result = func(*args, **kwargs)

            # Save to cache
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)

            if verbose:
                print(f"[Cache SAVE] Saved to {cache_file.name}")

            return result

        # Add cache management methods
        def clear_cache() -> int:
            """Clear all cache files for this function."""
            if not cache_path.exists():
                return 0
            count = 0
            for cache_file in cache_path.glob(f"{func.__name__}_*.pkl"):
                cache_file.unlink()
                count += 1
            return count

        wrapper.clear_cache = clear_cache  # type: ignore
        return wrapper  # type: ignore

    return decorator


def clear_all_caches(cache_dir: str | Path = ".cache") -> int:
    """Clear all cache files in a directory.

    Args:
        cache_dir: Directory containing cache files

    Returns:
        Number of files deleted
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return 0

    count = 0
    for cache_file in cache_path.glob("*.pkl"):
        cache_file.unlink()
        count += 1

    return count
