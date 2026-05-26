"""
ml/predict.py
=============
Prediction utility used by the Flask backend.

Preprocessing at inference mirrors train.py exactly:
  1. Build 63-feature DataFrame (missing → 0)
  2. Clip using saved 1st/99th percentile bounds (clip_bounds.pkl)
  3. Scale with saved StandardScaler (fit on 63 features)
  4. Select top-30 features by index
  5. Run RF inference
"""

import sys, os, pickle, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    MODEL_PATH, SCALER_PATH, FEATURES_PATH,
    CLIP_BOUNDS_PATH, THRESHOLD_PATH, CONFIDENCE_THRESHOLD,
)

# ── Load artifacts once at import ─────────────────────────────────────────────
def _load_artifacts():
    for path in (MODEL_PATH, SCALER_PATH, FEATURES_PATH, CLIP_BOUNDS_PATH, THRESHOLD_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Artifact not found: {path}\nRun ml/train.py first.")
    with open(MODEL_PATH,       "rb") as f: model        = pickle.load(f)
    with open(SCALER_PATH,      "rb") as f: scaler       = pickle.load(f)
    with open(FEATURES_PATH,    "rb") as f: top_features = pickle.load(f)
    with open(CLIP_BOUNDS_PATH, "rb") as f: clip_bounds  = pickle.load(f)
    with open(THRESHOLD_PATH,   "rb") as f: threshold    = pickle.load(f)
    return model, scaler, top_features, clip_bounds, float(threshold)

_MODEL, _SCALER, _TOP_FEATURES, _CLIP_BOUNDS, _THRESHOLD = _load_artifacts()

# Full 63-feature list (Attr1–Attr64 minus Attr37)
_ALL_FEATURES = [f"Attr{i}" for i in range(1, 65) if i != 37]
assert len(_ALL_FEATURES) == _SCALER.n_features_in_, (
    f"Feature count mismatch: {len(_ALL_FEATURES)} vs scaler expects {_SCALER.n_features_in_}"
)

# ── Preprocessing ──────────────────────────────────────────────────────────────
def _preprocess(input_dict: dict) -> np.ndarray:
    # 1. Build full 63-feature row
    row = {f: input_dict.get(f, np.nan) for f in _ALL_FEATURES}
    df  = pd.DataFrame([row], columns=_ALL_FEATURES)
    df  = df.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    # 2. Clip using exact training bounds (1st/99th percentile)
    arr = np.clip(df.values, _CLIP_BOUNDS["lower"], _CLIP_BOUNDS["upper"])

    # 3. Scale (scaler was fit on all 63 features)
    arr_scaled = _SCALER.transform(arr)

    # 4. Select top-30 features by index
    indices      = [_ALL_FEATURES.index(f) for f in _TOP_FEATURES]
    arr_selected = arr_scaled[:, indices]
    return arr_selected

# ── Risk level ─────────────────────────────────────────────────────────────────
def _risk_level(p: float) -> str:
    if p < 0.20:  return "Low"
    if p < 0.40:  return "Medium"
    if p < 0.65:  return "High"
    return "Critical"

# ── Risk percentage label ──────────────────────────────────────────────────────
def _risk_percentage(p: float) -> str:
    return f"{round(p * 100)}%"

# ── AI Recommendations ─────────────────────────────────────────────────────────
_RECOMMENDATIONS = {
    "Low": [
        "Business appears financially healthy. Maintain current liquidity ratios.",
        "Continue monitoring cash flow and debt-to-equity ratio quarterly.",
        "Consider reinvesting profits to strengthen retained earnings.",
        "Low bankruptcy risk — suitable for expansion or new credit lines.",
    ],
    "Medium": [
        "Monitor short-term liabilities closely — ensure coverage ratio stays above 1.5.",
        "Review operating expenses and identify areas to reduce overhead.",
        "Strengthen working capital by improving accounts receivable turnover.",
        "Consider refinancing short-term debt to longer terms to ease cash pressure.",
        "Build a 3–6 month cash reserve as a financial buffer.",
    ],
    "High": [
        "⚠ Immediate action required: review and reduce total liabilities.",
        "Prioritise improving net profit margin — target at least 5% within 2 quarters.",
        "Negotiate extended payment terms with suppliers to improve cash flow.",
        "Consider asset liquidation to reduce debt burden.",
        "Engage a financial advisor to restructure debt obligations.",
        "Suspend non-essential capital expenditure until ratios improve.",
    ],
    "Critical": [
        "🚨 Critical risk — seek professional financial or legal counsel immediately.",
        "Explore debt restructuring or insolvency protection options.",
        "Prioritise paying secured creditors to avoid asset seizure.",
        "Conduct an emergency cash flow audit — identify all outflows within 30 days.",
        "Consider voluntary administration as a protective measure.",
        "Communicate proactively with lenders to negotiate forbearance agreements.",
    ],
}

def _get_recommendations(risk_level: str, probability: float, top_features: list) -> dict:
    """Return structured AI recommendations based on risk level and top features."""
    tips = _RECOMMENDATIONS.get(risk_level, _RECOMMENDATIONS["Medium"])

    # Feature-specific advice
    feature_advice = []
    feature_map = {
        "Attr35": "High debt-to-EBITDA ratio detected — focus on reducing total liabilities.",
        "Attr39": "Low profit on operating activities — review pricing and cost structure.",
        "Attr21": "Weak net profit margin — target operational efficiency improvements.",
        "Attr1":  "Net profit/assets ratio is a key driver — improve asset utilisation.",
        "Attr6":  "Retained earnings are low — reduce dividend payouts to build reserves.",
        "Attr13": "EBIT/assets ratio is critical — improve earnings before interest and tax.",
        "Attr15": "High total liabilities ratio — prioritise debt reduction.",
        "Attr22": "Gross profit/assets is low — review pricing strategy.",
        "Attr27": "Operating profit vs financial expenses is unfavourable — reduce interest burden.",
        "Attr41": "Working capital efficiency needs improvement.",
    }
    for feat in top_features[:3]:
        fname = feat.get("feature", "")
        if fname in feature_map:
            feature_advice.append(feature_map[fname])

    return {
        "risk_level":      risk_level,
        "probability_pct": _risk_percentage(probability),
        "summary":         f"This business has a {_risk_percentage(probability)} bankruptcy probability, indicating {risk_level.lower()} financial risk.",
        "recommendations": tips,
        "feature_advice":  feature_advice,
        "action_urgency":  {
            "Low":      "Monitor quarterly",
            "Medium":   "Review within 30 days",
            "High":     "Act within 2 weeks",
            "Critical": "Immediate action required",
        }.get(risk_level, "Review soon"),
    }

# ── Feature contributions ──────────────────────────────────────────────────────
def _top_feature_contributions(arr_selected: np.ndarray) -> list:
    importances = _MODEL.feature_importances_
    top_idx     = np.argsort(importances)[::-1][:5]
    return [
        {
            "feature":    _TOP_FEATURES[i],
            "value":      round(float(arr_selected[0, i]), 4),
            "importance": round(float(importances[i]), 4),
        }
        for i in top_idx
    ]

# ── Public API ─────────────────────────────────────────────────────────────────
def predict_single(input_dict: dict) -> dict:
    try:
        arr          = _preprocess(input_dict)
        probability  = float(_MODEL.predict_proba(arr)[0, 1])
        prediction   = int(probability >= _THRESHOLD)
        label        = "Bankrupt" if prediction == 1 else "Safe"
        risk         = _risk_level(probability)
        trusted      = probability >= CONFIDENCE_THRESHOLD
        contributions = _top_feature_contributions(arr)
        recommendations = _get_recommendations(risk, probability, contributions)

        return {
            "prediction":       prediction,
            "label":            label,
            "probability":      round(probability, 4),
            "confidence":       round(probability, 4),
            "risk_level":       risk,
            "risk_percentage":  _risk_percentage(probability),
            "trusted":          trusted,
            "threshold":        round(_THRESHOLD, 4),
            "top_features":     contributions,
            "recommendations":  recommendations,
            "error":            None,
        }
    except Exception as exc:
        return {
            "prediction": None, "label": None, "probability": None,
            "confidence": None, "risk_level": None, "risk_percentage": None,
            "trusted": False, "threshold": round(_THRESHOLD, 4),
            "top_features": [], "recommendations": None, "error": str(exc),
        }

def predict_batch(records: list) -> list:
    return [predict_single(r) for r in records]

# ── Smoke test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    for name, data in [
        ("Empty input",    {}),
        ("Healthy (1.5)",  {f"Attr{i}": 1.5 for i in range(1,65) if i!=37}),
        ("Distressed (-2)",{f"Attr{i}":-2.0 for i in range(1,65) if i!=37}),
    ]:
        r = predict_single(data)
        print(f"\n[{name}]")
        print(f"  Label      : {r['label']}  ({r['risk_percentage']} | {r['risk_level']} risk)")
        print(f"  Threshold  : {r['threshold']}  Trusted: {r['trusted']}")
        print(f"  Urgency    : {r['recommendations']['action_urgency'] if r['recommendations'] else 'N/A'}")
    print("\n" + "=" * 55)
    print("Smoke test complete.")
