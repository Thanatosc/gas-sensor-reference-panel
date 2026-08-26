"""Metrics used by the pre-specified benchmark."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def mae(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    y_true = np.asarray(list(y_true), dtype=float)
    y_pred = np.asarray(list(y_pred), dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    y_true = np.asarray(list(y_true), dtype=float)
    y_pred = np.asarray(list(y_pred), dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def nrmse(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    y_true = np.asarray(list(y_true), dtype=float)
    scale = float(np.ptp(y_true))
    if not math.isfinite(scale) or scale <= 0:
        return float("nan")
    return rmse(y_true, y_pred) / scale


def calibration_slope(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    y_true = np.asarray(list(y_true), dtype=float)
    y_pred = np.asarray(list(y_pred), dtype=float)
    if len(y_true) < 2 or np.ptp(y_pred) <= 0:
        return float("nan")
    return float(np.polyfit(y_pred, y_true, deg=1)[0])


def recovered_loss(frozen_error: float, updated_error: float, oracle_error: float) -> float:
    denominator = frozen_error - oracle_error
    if not all(math.isfinite(v) for v in (frozen_error, updated_error, oracle_error)):
        return float("nan")
    if denominator <= 0:
        return float("nan")
    return (frozen_error - updated_error) / denominator
