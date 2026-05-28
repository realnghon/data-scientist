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

F = TypeVar('F', bound=Callable[..., Any])


def _hash_args(*args: Any, **kwargs: Any) -> str:
    """Create a stable hash of function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Hex digest of the arguments
    """
    # Convert args to a stable representation
    # For DataFrames, use shape + column names + first/last few rows
    stable_repr = []

    for arg in args:
        if hasattr(arg, 'shape') and hasattr(arg, 'columns'):
            # Likely a DataFrame
            stable_repr.append({
                'type': 'DataFrame',
                'shape': arg.shape,
                'columns': list(arg.columns),
                'head': arg.head(3).to_dict(),
                'tail': arg.tail(3).to_dict(),
            })
        else:
            stable_repr.append(arg)

    for key, value in sorted(kwargs.items()):
        if hasattr(value, 'shape') and hasattr(value, 'columns'):
            stable_repr.append({
                'key': key,
                'type': 'DataFrame',
                'shape': value.shape,
                'columns': list(value.columns),
                'head': value.head(3).to_dict(),
                'tail': value.tail(3).to_dict(),
            })
        else:
            stable_repr.append({key: value})

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
