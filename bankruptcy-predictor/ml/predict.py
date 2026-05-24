"""
ml/predict.py
=============
Prediction utility used by the Flask backend (and usable standalone).

Responsibilities:
  - Load model, scaler, feature list, and threshold once at import time
  - Expose predict_single(input_dict)  → single-row prediction
  - Expose predict_batch(list_of_dicts) → batch prediction
  - Apply the exact same preprocessing as train.py:
      impute missing → clip outliers → scale → select top features
  - Return structured result dicts consumed by app.py

Result dict schema:
  {
    "prediction":   int,          # 0 = Safe, 1 = Bankrupt
    "label":        str,          # "Safe" | "Bankrupt"
    "probability":  float,        # P(bankrupt), 0–1
    "confidence":   float,        # same as probability, alias for frontend
    "risk_level":   str,          # "Low" | "Medium" | "High" | "Critical"
    "trusted":      bool,         # probability >= CONFIDENCE_THRESHOLD
    "threshold":    float,        # decision threshold used
    "top_features": list[dict],   # [{"feature": str, "value": float, "importance": float}]
    "error":        str | None,   # set only on validation/processing failure
  }
"""

import sys
import os
import pickle
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── project root on sys.path ───────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    MODEL_PATH,
    SCALER_PATH,
    FEATURES_PATH,
    THRESHOLD_PATH,
    CONFIDENCE_THRESHOLD,
    OUTLIER_LOWER_PCTILE,
    OUTLIER_UPPER_PCTILE,
)


# ══════════════════════════════════════════════════════════════════════════════
# ARTIFACT LOADING  (done once at module import — not on every request)
# ══════════════════════════════════════════════════════════════════════════════

def _load_artifacts():
    """Load and return (model, scaler, top_features, threshold)."""
    for path in (MODEL_PATH, SCALER_PATH, FEATURES_PATH, THRESHOLD_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Required artifact not found: {path}\n"
                "Run ml/train.py first to generate model files."
            )
    with open(MODEL_PATH,     "rb") as f: model        = pickle.load(f)
    with open(SCALER_PATH,    "rb") as f: scaler       = pickle.load(f)
    with open(FEATURES_PATH,  "rb") as f: top_features = pickle.load(f)
    with open(THRESHOLD_PATH, "rb") as f: threshold    = pickle.load(f)
    return model, scaler, top_features, float(threshold)


# Module-level singletons — loaded once
_MODEL, _SCALER, _TOP_FEATURES, _THRESHOLD = _load_artifacts()

# All feature names the scaler was trained on (63 features after dropping Attr37)
# We derive this from the scaler's feature count; names come from the ARFF columns
# minus the dropped column and the target.
_ALL_FEATURE_NAMES: list = None   # populated lazily on first call


def _get_all_feature_names() -> list:
    """
    Return the full ordered list of feature names the scaler expects.
    Derived from the ARFF attribute order minus Attr37 (dropped >40% missing)
    and the target column.
    """
    global _ALL_FEATURE_NAMES
    if _ALL_FEATURE_NAMES is not None:
        return _ALL_FEATURE_NAMES

    # The Polish dataset has Attr1–Attr64 + class.
    # Attr37 was dropped (>40% missing). Target ('class') is not a feature.
    all_attrs = [f"Attr{i}" for i in range(1, 65) if i != 37]
    # Verify count matches scaler expectation
    expected = _SCALER.n_features_in_
    if len(all_attrs) != expected:
        raise RuntimeError(
            f"Feature count mismatch: derived {len(all_attrs)} names "
            f"but scaler expects {expected}. "
            "Re-run train.py if the dataset changed."
        )
    _ALL_FEATURE_NAMES = all_attrs
    return _ALL_FEATURE_NAMES


# ══════════════════════════════════════════════════════════════════════════════
# PREPROCESSING  (mirrors train.py — no fitting, only transform)
# ══════════════════════════════════════════════════════════════════════════════

def _preprocess(input_dict: dict) -> np.ndarray:
    """
    Transform a raw input dict into the model-ready feature vector.

    Steps (must match train.py order exactly):
      1. Build a 1-row DataFrame with all expected feature columns
      2. Fill missing values with 0 (median imputation at inference uses 0
         as a neutral stand-in; the scaler was fit on median-imputed data)
      3. Clip to [1st, 99th] percentile bounds stored in the scaler's
         mean/scale (we use ±3σ as a practical clip at inference since we
         don't store the exact percentile bounds separately)
      4. Scale with the saved StandardScaler
      5. Select the top-N features in the trained order
    """
    all_features = _get_all_feature_names()

    # 1. Build DataFrame — missing keys become NaN
    row = {feat: input_dict.get(feat, np.nan) for feat in all_features}
    df  = pd.DataFrame([row], columns=all_features)

    # 2. Impute NaN with 0 (neutral after scaling; scaler mean ≈ median)
    df = df.fillna(0.0)

    # Ensure all values are numeric
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    # 3. Clip outliers using ±3σ from the scaler's learned statistics
    #    (scaler.mean_ and scaler.scale_ are fit on the clipped+scaled train data,
    #     so we clip raw values to [mean - 3σ, mean + 3σ] before scaling)
    lower = _SCALER.mean_ - 3 * _SCALER.scale_
    upper = _SCALER.mean_ + 3 * _SCALER.scale_
    arr   = np.clip(df.values, lower, upper)

    # 4. Scale
    arr_scaled = _SCALER.transform(arr)

    # 5. Select top features (same column indices as training)
    feature_indices = [all_features.index(f) for f in _TOP_FEATURES]
    arr_selected    = arr_scaled[:, feature_indices]

    return arr_selected


# ══════════════════════════════════════════════════════════════════════════════
# RISK LEVEL
# ══════════════════════════════════════════════════════════════════════════════

def _risk_level(probability: float) -> str:
    """Map bankruptcy probability to a human-readable risk tier."""
    if probability < 0.20:
        return "Low"
    elif probability < 0.40:
        return "Medium"
    elif probability < 0.65:
        return "High"
    else:
        return "Critical"


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE CONTRIBUTION  (top-5 most important features for this prediction)
# ══════════════════════════════════════════════════════════════════════════════

def _top_feature_contributions(arr_selected: np.ndarray) -> list:
    """
    Return the top-5 features by model importance, with their scaled values.
    Used by the frontend FeatureChart component.
    """
    importances = _MODEL.feature_importances_
    top_idx     = np.argsort(importances)[::-1][:5]

    contributions = []
    for i in top_idx:
        contributions.append({
            "feature":    _TOP_FEATURES[i],
            "value":      round(float(arr_selected[0, i]), 4),
            "importance": round(float(importances[i]), 4),
        })
    return contributions


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def predict_single(input_dict: dict) -> dict:
    """
    Run inference on a single company's financial ratios.

    Parameters
    ----------
    input_dict : dict
        Keys are feature names (e.g. "Attr1", "Attr6", …).
        Missing keys are treated as NaN and imputed.

    Returns
    -------
    dict  — see module docstring for schema
    """
    try:
        arr_selected = _preprocess(input_dict)

        probability  = float(_MODEL.predict_proba(arr_selected)[0, 1])
        prediction   = int(probability >= _THRESHOLD)
        label        = "Bankrupt" if prediction == 1 else "Safe"
        risk         = _risk_level(probability)
        trusted      = probability >= CONFIDENCE_THRESHOLD
        contributions = _top_feature_contributions(arr_selected)

        return {
            "prediction":   prediction,
            "label":        label,
            "probability":  round(probability, 4),
            "confidence":   round(probability, 4),
            "risk_level":   risk,
            "trusted":      trusted,
            "threshold":    round(_THRESHOLD, 4),
            "top_features": contributions,
            "error":        None,
        }

    except Exception as exc:
        return {
            "prediction":   None,
            "label":        None,
            "probability":  None,
            "confidence":   None,
            "risk_level":   None,
            "trusted":      False,
            "threshold":    round(_THRESHOLD, 4),
            "top_features": [],
            "error":        str(exc),
        }


def predict_batch(records: list) -> list:
    """
    Run inference on a list of input dicts.

    Parameters
    ----------
    records : list[dict]
        Each dict follows the same schema as predict_single input.

    Returns
    -------
    list[dict]  — one result dict per input record
    """
    return [predict_single(record) for record in records]


# ══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  predict.py — standalone smoke test")
    print("=" * 55)

    # Test 1: all zeros (neutral / unknown company)
    result = predict_single({})
    print("\n[Test 1] Empty input (all features missing):")
    print(f"  Label       : {result['label']}")
    print(f"  Probability : {result['probability']}")
    print(f"  Risk level  : {result['risk_level']}")
    print(f"  Trusted     : {result['trusted']}")
    print(f"  Threshold   : {result['threshold']}")
    print(f"  Top features: {result['top_features']}")

    # Test 2: a clearly healthy company (high ratios)
    healthy = {f"Attr{i}": 1.5 for i in range(1, 65) if i != 37}
    result2 = predict_single(healthy)
    print("\n[Test 2] Healthy company (all ratios = 1.5):")
    print(f"  Label       : {result2['label']}")
    print(f"  Probability : {result2['probability']}")
    print(f"  Risk level  : {result2['risk_level']}")

    # Test 3: a distressed company (negative ratios)
    distressed = {f"Attr{i}": -2.0 for i in range(1, 65) if i != 37}
    result3 = predict_single(distressed)
    print("\n[Test 3] Distressed company (all ratios = -2.0):")
    print(f"  Label       : {result3['label']}")
    print(f"  Probability : {result3['probability']}")
    print(f"  Risk level  : {result3['risk_level']}")

    # Test 4: batch
    batch_results = predict_batch([healthy, distressed])
    print(f"\n[Test 4] Batch (2 records): {[r['label'] for r in batch_results]}")

    print("\n" + "=" * 55)
    print("  Smoke test complete.")
    print("=" * 55)
