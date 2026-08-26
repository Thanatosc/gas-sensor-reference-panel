"""Model factories and budgeted recalibration strategies."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.base import clone
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .metrics import calibration_slope


def make_model(name: str, seed: int):
    if name == "pls":
        return make_pipeline(StandardScaler(), PLSRegression(n_components=2))
    if name == "random_forest":
        return RandomForestRegressor(n_estimators=200, random_state=seed, n_jobs=-1)
    if name == "xgboost":
        try:
            from xgboost import XGBRegressor
        except ImportError as exc:
            raise ImportError("xgboost is required for the xgboost model") from exc
        return XGBRegressor(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=seed,
            n_jobs=-1,
        )
    raise ValueError(f"unknown model: {name}")


@dataclass
class FittedStrategy:
    model: object
    strategy: str
    calibration_intercept: float = 0.0
    calibration_slope: float = 1.0

    def predict(self, x):
        prediction = np.asarray(self.model.predict(x), dtype=float).reshape(-1)
        return self.calibration_intercept + self.calibration_slope * prediction


def fit_strategy(
    strategy: str,
    base_model,
    source_x,
    source_y,
    reference_x,
    reference_y,
) -> FittedStrategy:
    if strategy == "frozen":
        model = clone(base_model).fit(source_x, source_y)
        return FittedStrategy(model=model, strategy=strategy)

    if strategy == "full_retrain":
        model = clone(base_model).fit(
            np.concatenate([source_x, reference_x]),
            np.concatenate([source_y, reference_y]),
        )
        return FittedStrategy(model=model, strategy=strategy)

    if strategy == "target_finetune":
        if len(reference_y) < 2 or np.ptp(reference_y) <= 0:
            return fit_strategy("frozen", base_model, source_x, source_y, reference_x, reference_y)
        model = clone(base_model).fit(reference_x, reference_y)
        return FittedStrategy(model=model, strategy=strategy)

    if strategy == "calibrator_update":
        model = clone(base_model).fit(source_x, source_y)
        if len(reference_y) == 0:
            return FittedStrategy(model=model, strategy=strategy)
        reference_prediction = np.asarray(model.predict(reference_x), dtype=float).reshape(-1)
        if len(reference_y) < 2 or np.ptp(reference_y) <= 0 or np.ptp(reference_prediction) <= 0:
            return FittedStrategy(
                model=model,
                strategy=strategy,
                calibration_intercept=float(np.mean(reference_y - reference_prediction)),
            )
        calibrator = LinearRegression().fit(reference_prediction.reshape(-1, 1), reference_y)
        return FittedStrategy(
            model=model,
            strategy=strategy,
            calibration_intercept=float(calibrator.intercept_),
            calibration_slope=float(calibrator.coef_[0]),
        )

    raise ValueError(f"unknown strategy: {strategy}")
