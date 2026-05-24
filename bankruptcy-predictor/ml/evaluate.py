"""
ml/evaluate.py
==============
Standalone evaluation script — loads the saved model, scaler, and feature list,
then runs full evaluation on the held-out test set rebuilt from raw data.

Outputs:
  • Console: F1, Recall, ROC-AUC, classification report, CV stability
  • File:    ml/model/confusion_matrix.png

Usage:
    python ml/evaluate.py
"""

import sys
import os
import pickle
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend — safe on all platforms
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.io import arff
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    f1_score,
    recall_score,
    precision_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    roc_curve,
    auc,
)

warnings.filterwarnings("ignore")

# ── project root on sys.path ───────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    DATA_RAW_PATH,
    MODEL_PATH,
    SCALER_PATH,
    FEATURES_PATH,
    CONFUSION_MATRIX_PATH,
    TEST_SIZE,
    RANDOM_STATE,
    MISSING_DROP_THRESHOLD,
    OUTLIER_LOWER_PCTILE,
    OUTLIER_UPPER_PCTILE,
    CV_FOLDS,
    SCORING_METRIC,
)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def load_artifacts():
    """Load saved model, scaler, and feature list from disk."""
    print("[1/4] Loading saved artefacts …")
    for path in (MODEL_PATH, SCALER_PATH, FEATURES_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Artefact not found: {path}\n"
                "Run ml/train.py first to generate the model files."
            )
    with open(MODEL_PATH,    "rb") as f: model        = pickle.load(f)
    with open(SCALER_PATH,   "rb") as f: scaler       = pickle.load(f)
    with open(FEATURES_PATH, "rb") as f: top_features = pickle.load(f)

    print(f"    Model    : {MODEL_PATH}")
    print(f"    Scaler   : {SCALER_PATH}")
    print(f"    Features : {top_features}")
    return model, scaler, top_features


def rebuild_test_set(top_features: list):
    """
    Reproduce the exact same test set used during training:
      load → drop high-missing → stratified split → impute → clip → scale → select features
    All fitting steps use train data only (mirrors train.py exactly).
    """
    print("[2/4] Rebuilding held-out test set …")

    # Load raw data
    raw, _ = arff.loadarff(DATA_RAW_PATH)
    df = pd.DataFrame(raw)
    for col in df.select_dtypes([object]).columns:
        df[col] = df[col].str.decode("utf-8")
    if "class" in df.columns:
        df.rename(columns={"class": "target"}, inplace=True)
    df["target"] = pd.to_numeric(df["target"], errors="coerce").astype(int)

    # Drop high-missing columns
    missing_frac = df.isnull().mean()
    cols_to_drop = missing_frac[missing_frac > MISSING_DROP_THRESHOLD].index.tolist()
    df = df.drop(columns=cols_to_drop)

    # Stratified split (same seed → identical split as training)
    X = df.drop(columns=["target"])
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    # Impute (fit on train)
    imputer = SimpleImputer(strategy="median")
    imputer.fit(X_train)
    X_test_imp = pd.DataFrame(
        imputer.transform(X_test),
        columns=X_test.columns,
        index=X_test.index,
    )
    X_train_imp = pd.DataFrame(
        imputer.transform(X_train),
        columns=X_train.columns,
        index=X_train.index,
    )

    # Clip outliers (percentiles from train)
    lower = X_train_imp.quantile(OUTLIER_LOWER_PCTILE / 100)
    upper = X_train_imp.quantile(OUTLIER_UPPER_PCTILE / 100)
    X_test_clipped = X_test_imp.clip(lower=lower, upper=upper, axis=1)

    # Scale (load saved scaler — already fit on train)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    X_test_sc = scaler.transform(X_test_clipped)

    # Select top features (same column order as training)
    all_features = list(X_test.columns)
    feature_indices = [all_features.index(f) for f in top_features]
    X_test_sel = X_test_sc[:, feature_indices]

    print(f"    Test set shape : {X_test_sel.shape}  |  "
          f"Bankrupt rate: {y_test.mean():.2%}")
    return X_test_sel, y_test


# ══════════════════════════════════════════════════════════════════════════════
# METRICS
# ══════════════════════════════════════════════════════════════════════════════

def print_metrics(model, X_test_sel: np.ndarray, y_test: pd.Series) -> dict:
    """Compute and print all evaluation metrics."""
    print("[3/4] Computing metrics …\n")

    y_pred  = model.predict(X_test_sel)
    y_proba = model.predict_proba(X_test_sel)[:, 1]

    f1        = f1_score(y_test, y_pred)
    recall    = recall_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    roc_auc   = roc_auc_score(y_test, y_proba)
    cm        = confusion_matrix(y_test, y_pred)

    # ── Target thresholds ──────────────────────────────────────────────────
    targets = {
        "ROC-AUC > 0.90": (roc_auc,   0.90),
        "F1      > 0.72": (f1,        0.72),
        "Recall  > 0.75": (recall,    0.75),
    }

    print("┌─────────────────────────────────────────────────────────┐")
    print("│              TEST-SET EVALUATION RESULTS                │")
    print("├─────────────────────────────────────────────────────────┤")
    for label, (value, threshold) in targets.items():
        status = "✓ PASS" if value > threshold else "✗ FAIL"
        print(f"│  {label}   →  {value:.4f}   {status:<8}              │")
    print(f"│  Precision              →  {precision:.4f}                        │")
    print("└─────────────────────────────────────────────────────────┘")

    print(f"\nConfusion Matrix:\n{cm}")
    tn, fp, fn, tp = cm.ravel()
    print(f"  TN={tn}  FP={fp}  FN={fn}  TP={tp}")
    print(f"  False Negative Rate (missed bankruptcies): {fn/(fn+tp):.2%}")

    print(f"\nClassification Report:\n"
          f"{classification_report(y_test, y_pred, target_names=['Safe (0)', 'Bankrupt (1)'])}")

    return {
        "f1": f1, "recall": recall, "precision": precision,
        "roc_auc": roc_auc, "cm": cm,
        "y_pred": y_pred, "y_proba": y_proba,
    }


def check_cv_stability(model, X_test_sel: np.ndarray, y_test: pd.Series):
    """
    StratifiedKFold CV on the test set to verify stability.
    (Small set — informational only; primary CV was done during training.)
    """
    print("── Cross-Validation Stability (test set) ─────────────────────────")
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(
        model, X_test_sel, y_test,
        cv=cv, scoring=SCORING_METRIC, n_jobs=-1,
    )
    mean_f1 = scores.mean()
    std_f1  = scores.std()
    print(f"    CV F1 scores : {np.round(scores, 4)}")
    print(f"    Mean F1      : {mean_f1:.4f}  |  Std: {std_f1:.4f}")
    if std_f1 < 0.05:
        print("    ✓ Std < 0.05 — stable\n")
    else:
        print("    ✗ WARNING: Std >= 0.05\n")


# ══════════════════════════════════════════════════════════════════════════════
# PLOTS
# ══════════════════════════════════════════════════════════════════════════════

def save_plots(metrics: dict, top_features: list, model):
    """Save confusion matrix + ROC curve + feature importance chart."""
    print(f"[4/4] Saving plots …")
    os.makedirs(os.path.dirname(CONFUSION_MATRIX_PATH), exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("BankruptcySense AI — Model Evaluation", fontsize=14, fontweight="bold")

    # ── Confusion Matrix ───────────────────────────────────────────────────
    ax = axes[0]
    cm = metrics["cm"]
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=["Safe", "Bankrupt"],
        yticklabels=["Safe", "Bankrupt"],
        ax=ax,
    )
    ax.set_title("Confusion Matrix")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

    # ── ROC Curve ─────────────────────────────────────────────────────────
    ax = axes[1]
    fpr, tpr, _ = roc_curve(metrics["y_pred"], metrics["y_proba"])
    roc_auc_val = auc(fpr, tpr)
    ax.plot(fpr, tpr, color="darkorange", lw=2,
            label=f"ROC (AUC = {roc_auc_val:.3f})")
    ax.plot([0, 1], [0, 1], color="navy", lw=1, linestyle="--")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend(loc="lower right")

    # ── Feature Importances ────────────────────────────────────────────────
    ax = axes[2]
    importances = model.feature_importances_
    sorted_idx  = np.argsort(importances)
    ax.barh(
        [top_features[i] for i in sorted_idx],
        importances[sorted_idx],
        color="steelblue",
    )
    ax.set_title(f"Top {len(top_features)} Feature Importances")
    ax.set_xlabel("Importance")

    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    Saved → {CONFUSION_MATRIX_PATH}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  BankruptcySense AI — Evaluation Script")
    print("=" * 65 + "\n")

    model, scaler, top_features = load_artifacts()
    X_test_sel, y_test          = rebuild_test_set(top_features)
    metrics                     = print_metrics(model, X_test_sel, y_test)
    check_cv_stability(model, X_test_sel, y_test)
    save_plots(metrics, top_features, model)

    print("\n" + "=" * 65)
    print("  Evaluation complete.")
    print("=" * 65)


if __name__ == "__main__":
    main()
