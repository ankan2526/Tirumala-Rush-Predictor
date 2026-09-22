"""Machine Learning Trainer for Tirumala Pilgrim Footfall and Waiting Times.

Supports scikit-learn when available, and provides an analytical pure-Python
regression and feature importance engine as a zero-dependency baseline.
"""

from __future__ import annotations
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


class MLTrainer:
    """Trains regression models on historical TTD daily records and evaluates accuracy."""

    FEATURE_COLS = [
        "day_of_week",
        "is_weekend",
        "is_extended_weekend",
        "is_ekadashi",
        "is_pournami",
        "is_purattasi_saturday",
        "is_karthika_masam",
        "is_major_festival",
        "is_exam_season",
        "is_summer_vacation",
        "is_public_holiday",
        "holiday_count"
    ]

    def __init__(
        self,
        csv_path: Optional[Path | str] = None,
        weights_output_path: Optional[Path | str] = None
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.csv_path = Path(csv_path) if csv_path else base_dir / "data" / "historical_darshan_data.csv"
        self.weights_output_path = Path(weights_output_path) if weights_output_path else base_dir / "data" / "model_weights.json"

    def load_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load and split into train (<= 2024) and test (>= 2025)."""
        train_rows: List[Dict[str, Any]] = []
        test_rows: List[Dict[str, Any]] = []

        if not self.csv_path.exists():
            raise FileNotFoundError(f"Historical dataset not found at {self.csv_path}. Please run dataset_generator first.")

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Exclude full COVID closure period (zero-pilgrim lockdown days) from regression
                if int(row["pilgrim_count"]) < 10000:
                    continue

                year = int(row["year"])
                if year <= 2024:
                    train_rows.append(row)
                else:
                    test_rows.append(row)

        return train_rows, test_rows

    def train_and_evaluate(self) -> Dict[str, Any]:
        """Train baseline regression and evaluate on test set."""
        train_rows, test_rows = self.load_data()

        # Extract features and targets
        X_train, y_train_pilgrims, y_train_sarva = self._extract_features(train_rows)
        X_test, y_test_pilgrims, y_test_sarva = self._extract_features(test_rows)

        # Train multiple linear regression via Normal Equation in pure Python
        # X: (N, p), beta = (X^T X)^-1 X^T y
        weights_pilgrims, r2_train_p = self._fit_ridge(X_train, y_train_pilgrims, l2_reg=1.0)
        weights_sarva, r2_train_s = self._fit_ridge(X_train, y_train_sarva, l2_reg=1.0)

        # Evaluate on test set
        preds_p = [self._predict_one(row_features, weights_pilgrims) for row_features in X_test]
        preds_s = [self._predict_one(row_features, weights_sarva) for row_features in X_test]

        mae_p, rmse_p, r2_test_p = self._calc_metrics(preds_p, y_test_pilgrims)
        mae_s, rmse_s, r2_test_s = self._calc_metrics(preds_s, y_test_sarva)

        # Feature importances (normalized absolute weights)
        feat_names = ["intercept"] + self.FEATURE_COLS
        importance = {}
        total_mag = sum(abs(w) for w in weights_pilgrims[1:]) or 1.0
        for name, w in zip(self.FEATURE_COLS, weights_pilgrims[1:]):
            importance[name] = round(abs(w) / total_mag * 100.0, 2)

        results = {
            "trained_at": datetime.now().isoformat(),
            "train_samples": len(train_rows),
            "test_samples": len(test_rows),
            "pilgrims_model": {
                "mae": round(mae_p, 1),
                "rmse": round(rmse_p, 1),
                "r2": round(r2_test_p, 3),
                "weights": {name: round(w, 4) for name, w in zip(feat_names, weights_pilgrims)}
            },
            "sarva_wait_hours_model": {
                "mae": round(mae_s, 2),
                "rmse": round(rmse_s, 2),
                "r2": round(r2_test_s, 3),
                "weights": {name: round(w, 4) for name, w in zip(feat_names, weights_sarva)}
            },
            "feature_importance_pct": dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        }

        # Persist weights to JSON
        self.weights_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.weights_output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        return results

    def _extract_features(self, rows: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[float], List[float]]:
        X: List[List[float]] = []
        y_p: List[float] = []
        y_s: List[float] = []

        for r in rows:
            feats = [1.0]  # Intercept
            for col in self.FEATURE_COLS:
                feats.append(float(r[col]))
            X.append(feats)
            y_p.append(float(r["pilgrim_count"]))
            y_s.append(float(r["sarva_darshan_wait_hours"]))

        return X, y_p, y_s

    def _predict_one(self, x: List[float], weights: List[float]) -> float:
        return sum(xi * wi for xi, wi in zip(x, weights))

    def _calc_metrics(self, preds: List[float], actuals: List[float]) -> Tuple[float, float, float]:
        n = len(actuals)
        if n == 0:
            return 0.0, 0.0, 0.0

        mae = sum(abs(p - a) for p, a in zip(preds, actuals)) / n
        mse = sum((p - a) ** 2 for p, a in zip(preds, actuals)) / n
        rmse = math.sqrt(mse)

        mean_actual = sum(actuals) / n
        ss_tot = sum((a - mean_actual) ** 2 for a in actuals)
        ss_res = sum((a - p) ** 2 for p, a in zip(preds, actuals))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return mae, rmse, r2

    def _fit_ridge(self, X: List[List[float]], y: List[float], l2_reg: float = 1.0) -> Tuple[List[float], float]:
        """Solves Ridge Regression: beta = (X^T X + lambda I)^-1 X^T y using Gauss-Jordan."""
        n_rows = len(X)
        n_cols = len(X[0])

        # Compute X^T X (n_cols x n_cols)
        XtX = [[0.0] * n_cols for _ in range(n_cols)]
        for i in range(n_cols):
            for j in range(n_cols):
                XtX[i][j] = sum(X[k][i] * X[k][j] for k in range(n_rows))
            # Add L2 penalty except for intercept (i=0)
            if i > 0:
                XtX[i][i] += l2_reg

        # Compute X^T y (n_cols x 1)
        Xty = [0.0] * n_cols
        for i in range(n_cols):
            Xty[i] = sum(X[k][i] * y[k] for k in range(n_rows))

        # Solve XtX * beta = Xty using Gaussian elimination with partial pivoting
        beta = self._solve_linear_system(XtX, Xty)

        # Train R2
        preds = [self._predict_one(row, beta) for row in X]
        _, _, r2 = self._calc_metrics(preds, y)

        return beta, r2

    def _solve_linear_system(self, A: List[List[float]], b: List[float]) -> List[float]:
        n = len(A)
        # Augmented matrix [A | b]
        M = [A[i][:] + [b[i]] for i in range(n)]

        for i in range(n):
            # Pivot
            max_row = i
            max_val = abs(M[i][i])
            for k in range(i + 1, n):
                if abs(M[k][i]) > max_val:
                    max_val = abs(M[k][i])
                    max_row = k
            M[i], M[max_row] = M[max_row], M[i]

            pivot = M[i][i]
            if abs(pivot) < 1e-12:
                pivot = 1e-12

            for j in range(i, n + 1):
                M[i][j] /= pivot

            for k in range(n):
                if k != i:
                    factor = M[k][i]
                    for j in range(i, n + 1):
                        M[k][j] -= factor * M[i][j]

        return [M[i][n] for i in range(n)]
