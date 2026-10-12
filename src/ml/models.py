"""
src/ml/models.py
Phase 3 — Strategy C: Machine learning model definitions.
Pre-registered models: Ridge, Gradient Boosting, Multi-Layer Perceptron (MLP).
Seeds pinned for full reproducibility (Failure Guard #5).
"""

import numpy as np
from sklearn.linear_model import RidgeCV, Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from typing import Dict, Any, Optional
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "config.yaml") as f:
    CFG = yaml.safe_load(f)

SEED = CFG.get("project", {}).get("seed", 42)
ML_MODELS = CFG.get("strategy_c", {}).get("models", {})


class BaseMLModel:
    def fit(self, X: np.ndarray, y: np.ndarray):
        raise NotImplementedError
    def predict(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class RidgeModel(BaseMLModel):
    def __init__(self, alphas: Optional[list] = None):
        alphas = alphas or ML_MODELS.get("ridge", {}).get("alpha_grid", [0.01, 0.1, 1.0, 10.0, 100.0])
        self.model = RidgeCV(alphas=alphas)

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)


class GradientBoostModel(BaseMLModel):
    def __init__(self, max_depth: int = 3, learning_rate: float = 0.05, max_iter: int = 150):
        self.model = HistGradientBoostingRegressor(
            max_depth=max_depth,
            learning_rate=learning_rate,
            max_iter=max_iter,
            random_state=SEED,
            min_samples_leaf=20
        )

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)


class MLPModel(BaseMLModel):
    def __init__(self, hidden_layers: tuple = (64, 32), max_iter: int = 200):
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            activation="relu",
            max_iter=max_iter,
            random_state=SEED,
            early_stopping=True,
            validation_fraction=0.1
        )

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)


def get_ml_model(name: str = "ridge", **kwargs) -> BaseMLModel:
    name = name.lower()
    if name == "ridge":
        return RidgeModel(**kwargs)
    elif name in ("gradient_boost", "gbm", "lightgbm"):
        return GradientBoostModel(**kwargs)
    elif name == "mlp":
        return MLPModel(**kwargs)
    else:
        raise ValueError(f"Unknown ML model type: {name}. Must be ridge, gradient_boost, or mlp.")
