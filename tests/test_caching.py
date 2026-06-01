from __future__ import annotations

import pandas as pd

from ds_skill.caching import _hash_args, cached_computation, clear_all_caches


def test_hash_args_is_stable_for_keyword_order() -> None:
    assert _hash_args(1, alpha="x", beta=2) == _hash_args(1, beta=2, alpha="x")


def test_hash_args_includes_dataframe_shape_columns_and_edges() -> None:
    left = pd.DataFrame({"a": [1, 2, 3, 4], "b": [5, 6, 7, 8]})
    right = pd.DataFrame({"a": [1, 2, 3, 999], "b": [5, 6, 7, 8]})

    assert _hash_args(left) != _hash_args(right)
    assert _hash_args(frame=left) == _hash_args(frame=left.copy())


def test_cached_computation_reuses_pickled_result(tmp_path) -> None:
    calls = {"count": 0}

    @cached_computation(cache_dir=tmp_path)
    def add_one(value: int) -> dict[str, int]:
        calls["count"] += 1
        return {"value": value + 1}

    assert add_one(4) == {"value": 5}
    assert add_one(4) == {"value": 5}
    assert calls["count"] == 1
    assert len(list(tmp_path.glob("add_one_*.pkl"))) == 1


def test_cached_computation_verbose_hit_miss_and_save(tmp_path, capsys) -> None:
    @cached_computation(cache_dir=tmp_path, verbose=True)
    def add_one(value: int) -> int:
        return value + 1

    assert add_one(2) == 3
    first_output = capsys.readouterr().out
    assert "[Cache MISS]" in first_output
    assert "[Cache SAVE]" in first_output

    assert add_one(2) == 3
    second_output = capsys.readouterr().out
    assert "[Cache HIT]" in second_output


def test_cached_computation_can_be_disabled(tmp_path) -> None:
    calls = {"count": 0}

    @cached_computation(cache_dir=tmp_path, enabled=False)
    def add_one(value: int) -> int:
        calls["count"] += 1
        return value + calls["count"]

    assert add_one(4) == 5
    assert add_one(4) == 6
    assert calls["count"] == 2
    assert not list(tmp_path.glob("*.pkl"))


def test_clear_cache_only_removes_files_for_wrapped_function(tmp_path) -> None:
    @cached_computation(cache_dir=tmp_path)
    def first(value: int) -> int:
        return value

    @cached_computation(cache_dir=tmp_path)
    def second(value: int) -> int:
        return value

    first(1)
    second(1)

    assert first.clear_cache() == 1  # type: ignore[attr-defined]
    assert list(tmp_path.glob("second_*.pkl"))
    assert first.clear_cache() == 0  # type: ignore[attr-defined]


def test_clear_cache_returns_zero_when_directory_missing(tmp_path) -> None:
    missing = tmp_path / "missing"

    @cached_computation(cache_dir=missing)
    def identity(value: int) -> int:
        return value

    assert identity.clear_cache() == 0  # type: ignore[attr-defined]


def test_clear_all_caches_counts_pickle_files_only(tmp_path) -> None:
    (tmp_path / "a.pkl").write_bytes(b"a")
    (tmp_path / "b.pkl").write_bytes(b"b")
    (tmp_path / "note.txt").write_text("keep", encoding="utf-8")

    assert clear_all_caches(tmp_path) == 2
    assert (tmp_path / "note.txt").is_file()
    assert clear_all_caches(tmp_path / "missing") == 0
