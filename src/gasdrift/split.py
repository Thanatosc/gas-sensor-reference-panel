"""Time-ordered source/target splitting and deterministic reference sampling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Split:
    source: pd.DataFrame
    target: pd.DataFrame
    reference_pool: pd.DataFrame
    references: pd.DataFrame
    test: pd.DataFrame


def validate_temporal_order(frame: pd.DataFrame, group_columns: list[str]) -> list[str]:
    issues: list[str] = []
    numeric = pd.to_numeric(frame["timestamp"], errors="coerce")
    if numeric.notna().all():
        order = numeric
    else:
        order = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    if order.isna().any():
        return ["timestamp contains unparseable values"]
    checked = frame[group_columns].copy()
    checked["_timestamp_order"] = order.to_numpy()
    for group, part in checked.groupby(group_columns, dropna=False, sort=False):
        values = part["_timestamp_order"].tolist()
        if any(left > right for left, right in zip(values, values[1:])):
            issues.append(f"non-monotonic timestamp in sequence {group!r}")
    return issues


def make_split(
    frame: pd.DataFrame,
    source_batches: list,
    target_batches: list,
    budget: float,
    seed: int,
    group_columns: list[str],
    holdout_fraction: float = 0.30,
    holdout_target_bins: int | None = None,
    min_reference_rows: int = 2,
    budget_mode: str = "fraction",
) -> Split:
    source = frame[frame["batch_id"].isin(source_batches)].copy()
    target = frame[frame["batch_id"].isin(target_batches)].copy()
    if source.empty or target.empty:
        raise ValueError("source or target split is empty")

    if not 0 < holdout_fraction < 1:
        raise ValueError("holdout_fraction must be between 0 and 1")
    if budget_mode not in {"fraction", "absolute"}:
        raise ValueError("budget_mode must be 'fraction' or 'absolute'")

    test_indices: list[int] = []
    pool_order: list[int] = []
    pool_by_sequence: dict[tuple, list[int]] = {}
    rng = np.random.default_rng(seed)
    for sequence, sequence_part in target.groupby(group_columns, dropna=False, sort=False):
        sequence_key = sequence if isinstance(sequence, tuple) else (sequence,)
        sequence_part = sequence_part.copy()
        if holdout_target_bins:
            quantiles = min(holdout_target_bins, sequence_part["target"].nunique())
            sequence_part["_holdout_stratum"] = pd.qcut(
                sequence_part["target"],
                q=quantiles,
                labels=False,
                duplicates="drop",
            )
            stratum_column = "_holdout_stratum"
        else:
            stratum_column = "target"
        level_pools: dict[float, list[int]] = {}
        for level, part in sequence_part.groupby(stratum_column, dropna=False, sort=True):
            permutation = rng.permutation(part.index.to_numpy()).tolist()
            n_test = max(1, int(round(len(part) * holdout_fraction)))
            # A singleton concentration stays in the reference pool because it
            # cannot be represented in both calibration and evaluation sets.
            n_test = min(n_test, max(0, len(part) - 1))
            test_indices.extend(permutation[:n_test])
            level_pools[level] = permutation[n_test:]

        levels = sorted(level_pools)
        spread_levels: list[float] = []
        left, right = 0, len(levels) - 1
        while left <= right:
            spread_levels.append(levels[left])
            left += 1
            if left <= right:
                spread_levels.append(levels[right])
                right -= 1
        sequence_pool: list[int] = []
        max_level_rows = max((len(indices) for indices in level_pools.values()), default=0)
        for offset in range(max_level_rows):
            for level in spread_levels:
                if offset < len(level_pools[level]):
                    sequence_pool.append(level_pools[level][offset])
        pool_by_sequence[sequence_key] = sequence_pool
        pool_order.extend(sequence_pool)

    reference_pool = target.loc[sorted(pool_order)].copy()
    test = target.loc[sorted(test_indices)].copy()
    reference_indices: list[int] = []
    for sequence, target_part in target.groupby(group_columns, dropna=False, sort=False):
        sequence_key = sequence if isinstance(sequence, tuple) else (sequence,)
        part_order = pool_by_sequence[sequence_key]
        if budget_mode == "absolute":
            if budget < 0 or int(budget) != budget:
                raise ValueError("absolute reference budgets must be non-negative integers")
            n = int(budget)
        else:
            n = int(round(len(target_part) * budget))
        if budget > 0:
            n = max(min_reference_rows, n)
        n = min(n, len(part_order))
        if n:
            reference_indices.extend(part_order[:n])

    reference_indices = sorted(set(reference_indices))
    references = target.loc[reference_indices].copy()
    if test.empty or reference_pool.empty:
        raise ValueError("target split cannot support both a reference pool and holdout")
    if set(references.index) & set(test.index):
        raise AssertionError("reference/test leakage detected")
    return Split(
        source=source,
        target=target,
        reference_pool=reference_pool,
        references=references,
        test=test,
    )
