"""
ml/train.py
===========
Full training pipeline for the Bankruptcy Prediction Random Forest model.

Pipeline order (no data leakage):
  1. Load raw ARFF data
  2. Drop columns with > 40 % missing values
  3. Stratified train / test split  ← happens BEFORE any fitting
  4. Median imputation (fit on train, transform both)
  5. Outlier clipping (1st–99th percentile, computed on train only)
  6. StandardScaler (fit on train, transform both)
  7. SMOTE oversampling (applied to TRAIN only)
  8. Feature selection — top-N by RF feature importances (fit on SMOTE train)
  9. RandomizedSearchCV with StratifiedKFold (train only, class_weight forced)
 10. Decision-threshold tuning on training probabilities (maximise F1)
 11. Final evaluation on held-out test set using tuned threshold
 12. Save rf_model.pkl, scaler.pkl, features.pkl, threshold.pkl
"""

import sys
import os
import pickle
import warnings

import numpy as np
import pandas as pd
from scipy.io import arff

from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import (
    train_test_split,
    RandomizedSearchCV,
    StratifiedKFold,
    cross_val_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    f1_score,
    recall_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
)
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

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
    CLIP_BOUNDS_PATH,
    THRESHOLD_PATH,
    TOP_N_FEATURES,
    TEST_SIZE,
    RANDOM_STATE,
    MISSING_DROP_THRESHOLD,
    OUTLIER_LOWER_PCTILE,
    OUTLIER_UPPER_PCTILE,
    N_ITER_SEARCH,
    CV_FOLDS,
    SCORING_METRIC,
    RF_PARAM_DIST,
    MIN_PRECISION_FLOOR,
    MIN_RECALL_FLOOR,
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_arff(path: str) -> pd.DataFrame:
    """Load a .arff file and return a clean DataFrame with numeric types."""
    print(f"[1/9] Loading data from: {path}")
    raw, meta = arff.loadarff(path)
    df = pd.DataFrame(raw)

    for col in df.select_dtypes([object]).columns:
        df[col] = df[col].str.decode("utf-8")

    if "class" in df.columns:
        df.rename(columns={"class": "target"}, inplace=True)

    df["target"] = pd.to_numeric(df["target"], errors="coerce").astype(int)

    print(f"    Shape: {df.shape}  |  Bankrupt rate: {df['target'].mean():.2%}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# 2. DROP HIGH-MISSING COLUMNS
# ══════════════════════════════════════════════════════════════════════════════

def drop_high_missing(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Drop columns where the fraction of NaN > threshold."""
    missing_frac = df.isnull().mean()
    cols_to_drop = missing_frac[missing_frac > threshold].index.tolist()
    print(f"[2/9] Dropping {len(cols_to_drop)} columns with >"
          f" {threshold:.0%} missing: {cols_to_drop}")
    return df.drop(columns=cols_to_drop)


# ══════════════════════════════════════════════════════════════════════════════
# 3. TRAIN / TEST SPLIT  (stratified, done FIRST)
# ══════════════════════════════════════════════════════════════════════════════

def split_data(df: pd.DataFrame):
    """Stratified split — returns X_train, X_test, y_train, y_test."""
    print(f"[3/9] Stratified train/test split  (test={TEST_SIZE})")
    X = df.drop(columns=["target"])
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    print(f"    Train: {X_train.shape}  |  Test: {X_test.shape}")
    print(f"    Train bankrupt rate: {y_train.mean():.2%}  |  "
          f"Test bankrupt rate: {y_test.mean():.2%}")
    return X_train, X_test, y_train, y_test


# ══════════════════════════════════════════════════════════════════════════════
# 4. MEDIAN IMPUTATION  (fit on train only)
# ══════════════════════════════════════════════════════════════════════════════

def impute_median(X_train: pd.DataFrame, X_test: pd.DataFrame):
    """Fit median imputer on train, transform both splits."""
    print("[4/9] Median imputation (fit on train only)")
    imputer = SimpleImputer(strategy="median")
    X_train_imp = pd.DataFrame(
        imputer.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index,
    )
    X_test_imp = pd.DataFrame(
        imputer.transform(X_test),
        columns=X_test.columns,
        index=X_test.index,
    )
    return X_train_imp, X_test_imp


# ══════════════════════════════════════════════════════════════════════════════
# 5. OUTLIER CLIPPING  (percentiles computed on train only)
# ══════════════════════════════════════════════════════════════════════════════

def clip_outliers(X_train: pd.DataFrame, X_test: pd.DataFrame):
    """Clip values to [1st, 99th] percentile computed on training data."""
    print(f"[5/9] Outlier clipping  "
          f"({OUTLIER_LOWER_PCTILE}th–{OUTLIER_UPPER_PCTILE}th percentile, "
          f"train-derived)")
    lower = X_train.quantile(OUTLIER_LOWER_PCTILE / 100)
    upper = X_train.quantile(OUTLIER_UPPER_PCTILE / 100)
    X_train_clipped = X_train.clip(lower=lower, upper=upper, axis=1)
    X_test_clipped  = X_test.clip(lower=lower, upper=upper, axis=1)
    # Return bounds so they can be saved and reused at inference time
    return X_train_clipped, X_test_clipped, lower.values, upper.values


# ══════════════════════════════════════════════════════════════════════════════
# 6. STANDARD SCALING  (fit on train only)
# ══════════════════════════════════════════════════════════════════════════════

def scale_features(X_train: pd.DataFrame, X_test: pd.DataFrame):
    """Fit StandardScaler on train, transform both. Returns arrays + scaler."""
    print("[6/9] StandardScaler (fit on train only)")
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)
    return X_train_sc, X_test_sc, scaler


# ══════════════════════════════════════════════════════════════════════════════
# 7. SMOTE  (train only — no leakage)
# ══════════════════════════════════════════════════════════════════════════════

def apply_smote(X_train: np.ndarray, y_train: pd.Series):
    """Oversample minority class on training data only."""
    print("[7/9] SMOTE oversampling (train only)")
    print(f"    Before — class counts: "
          f"{dict(zip(*np.unique(y_train, return_counts=True)))}")
    smote = SMOTE(random_state=RANDOM_STATE)
    X_res, y_res = smote.fit_resample(X_train, y_train)
    print(f"    After  — class counts: "
          f"{dict(zip(*np.unique(y_res, return_counts=True)))}")
    return X_res, y_res


# ══════════════════════════════════════════════════════════════════════════════
# 8. FEATURE SELECTION  (top-N by RF importances, fit on SMOTE train)
# ══════════════════════════════════════════════════════════════════════════════

def select_top_features(
    X_train_res: np.ndarray,
    y_train_res: np.ndarray,
    X_test_sc: np.ndarray,
    feature_names: list,
    n: int,
):
    """Train a quick RF to rank features, keep top-N."""
    print(f"[8/9] Feature selection — top {n} features by RF importance")
    selector_rf = RandomForestClassifier(
        n_estimators=200,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    )
    selector_rf.fit(X_train_res, y_train_res)

    importances = selector_rf.feature_importances_
    top_indices  = np.argsort(importances)[::-1][:n]
    top_features = [feature_names[i] for i in top_indices]

    print(f"    Selected features: {top_features}")

    X_train_sel = X_train_res[:, top_indices]
    X_test_sel  = X_test_sc[:, top_indices]
    return X_train_sel, X_test_sel, top_features, top_indices


# ══════════════════════════════════════════════════════════════════════════════
# 9. HYPERPARAMETER TUNING  (RandomizedSearchCV + StratifiedKFold)
# ══════════════════════════════════════════════════════════════════════════════

def tune_model(X_train_sel: np.ndarray, y_train_res: np.ndarray):
    """
    RandomizedSearchCV with StratifiedKFold on SMOTE-resampled training data.
    class_weight is always 'balanced' or 'balanced_subsample' (never None).
    """
    print(f"[9/9] RandomizedSearchCV  "
          f"(n_iter={N_ITER_SEARCH}, cv={CV_FOLDS}, scoring={SCORING_METRIC})")

    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    base_rf = RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1)

    search = RandomizedSearchCV(
        estimator=base_rf,
        param_distributions=RF_PARAM_DIST,
        n_iter=N_ITER_SEARCH,
        cv=cv,
        scoring=SCORING_METRIC,
        refit=True,
        verbose=1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    search.fit(X_train_sel, y_train_res)

    print(f"\n    Best params : {search.best_params_}")
    print(f"    Best CV {SCORING_METRIC}  : {search.best_score_:.4f}")
    return search.best_estimator_, search


# ══════════════════════════════════════════════════════════════════════════════
# 10. THRESHOLD TUNING  (OOF probabilities on original train — no leakage)
# ══════════════════════════════════════════════════════════════════════════════

def tune_threshold(
    model,
    X_train_orig: np.ndarray,
    y_train_orig: pd.Series,
) -> float:
    """
    Find the probability threshold that maximises F1 using out-of-fold (OOF)
    predictions on the ORIGINAL (pre-SMOTE) training data.

    For each CV fold:
      - fit model + SMOTE on the fold's train portion
      - predict probabilities on the fold's validation portion (real distribution)
    This gives honest probabilities on real-world class balance.
    """
    print("\n── Threshold Tuning (OOF on original train, maximise F1) ────────")
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    oof_proba = np.zeros(len(y_train_orig))
    smote = SMOTE(random_state=RANDOM_STATE)

    # Extract the underlying RF params for OOF fold models
    base_rf = model

    for fold_idx, (tr_idx, val_idx) in enumerate(cv.split(X_train_orig, y_train_orig)):
        X_tr, X_val = X_train_orig[tr_idx], X_train_orig[val_idx]
        y_tr = np.array(y_train_orig)[tr_idx]

        # Apply SMOTE only on this fold's training portion
        X_tr_res, y_tr_res = smote.fit_resample(X_tr, y_tr)

        # Use a lightweight RF (100 trees) for OOF probability calibration
        params = {k: v for k, v in base_rf.get_params().items()
                  if k not in ("random_state", "n_estimators", "n_jobs")}
        fold_model = RandomForestClassifier(
            **params,
            n_estimators=100,
            n_jobs=1,
            random_state=RANDOM_STATE,
        )
        fold_model.fit(X_tr_res, y_tr_res)
        oof_proba[val_idx] = fold_model.predict_proba(X_val)[:, 1]

    # Find threshold: maximise F1 subject to:
    #   - recall    >= MIN_RECALL_FLOOR    (catch most bankruptcies)
    #   - precision >= MIN_PRECISION_FLOOR (avoid too many false alarms)
    precisions, recalls, thresholds = precision_recall_curve(
        y_train_orig, oof_proba
    )
    f1_scores = np.where(
        (precisions[:-1] + recalls[:-1]) > 0,
        2 * precisions[:-1] * recalls[:-1] / (precisions[:-1] + recalls[:-1]),
        0,
    )
    # Both constraints must be satisfied
    valid_mask = (precisions[:-1] >= MIN_PRECISION_FLOOR) & \
                 (recalls[:-1]    >= MIN_RECALL_FLOOR)
    masked_f1  = np.where(valid_mask, f1_scores, 0)
    best_idx   = np.argmax(masked_f1)

    # Fallback 1: relax precision floor, keep recall constraint
    if masked_f1[best_idx] == 0:
        print(f"    INFO: No threshold meets both floors. "
              f"Relaxing precision floor, keeping recall >= {MIN_RECALL_FLOOR:.0%}.")
        valid_mask = recalls[:-1] >= MIN_RECALL_FLOOR
        masked_f1  = np.where(valid_mask, f1_scores, 0)
        best_idx   = np.argmax(masked_f1)

    # Fallback 2: just maximise F1
    if masked_f1[best_idx] == 0:
        print(f"    INFO: No threshold meets recall >= {MIN_RECALL_FLOOR:.0%}. "
              f"Falling back to max-F1 threshold.")
        best_idx = np.argmax(f1_scores)

    best_threshold = float(thresholds[best_idx])
    best_f1        = f1_scores[best_idx]

    print(f"    OOF precision @ threshold : {precisions[best_idx]:.4f}")
    print(f"    OOF recall    @ threshold : {recalls[best_idx]:.4f}")
    print(f"    OOF F1        @ threshold : {best_f1:.4f}")
    print(f"    Optimal threshold         : {best_threshold:.4f}")
    return best_threshold


# ══════════════════════════════════════════════════════════════════════════════
# CALIBRATE PROBABILITIES
# ══════════════════════════════════════════════════════════════════════════════

def calibrate_model(model, X_train_sel: np.ndarray, y_train_res: np.ndarray):
    """
    Wrap the tuned RF in CalibratedClassifierCV (isotonic regression).
    Better-calibrated probabilities → more reliable threshold tuning.
    """
    print("\n── Probability Calibration (isotonic, cv=5) ──────────────────────")
    calibrated = CalibratedClassifierCV(
        estimator=model,
        method="isotonic",
        cv=5,
        n_jobs=-1,
    )
    calibrated.fit(X_train_sel, y_train_res)
    print("    Calibration complete.")
    return calibrated


# ══════════════════════════════════════════════════════════════════════════════
# CV STABILITY CHECK
# ══════════════════════════════════════════════════════════════════════════════

def check_cv_stability(model, X_train_sel: np.ndarray, y_train_res: np.ndarray):
    """StratifiedKFold CV on the best model — verify std < 0.05."""
    print("\n── Cross-Validation Stability Check ──────────────────────────────")
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(
        model, X_train_sel, y_train_res,
        cv=cv, scoring=SCORING_METRIC, n_jobs=-1,
    )
    mean_f1 = scores.mean()
    std_f1  = scores.std()
    print(f"    CV F1 scores : {np.round(scores, 4)}")
    print(f"    Mean F1      : {mean_f1:.4f}  |  Std: {std_f1:.4f}")
    if std_f1 < 0.05:
        print("    ✓ Std < 0.05 — model is stable across folds")
    else:
        print("    ✗ WARNING: Std >= 0.05 — consider more data or regularisation")
    return mean_f1, std_f1


# ══════════════════════════════════════════════════════════════════════════════
# FINAL EVALUATION ON TEST SET
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_on_test(
    model,
    X_test_sel: np.ndarray,
    y_test: pd.Series,
    threshold: float,
):
    """Print F1, Recall, ROC-AUC and confusion matrix on the held-out test set."""
    print("\n── Test-Set Evaluation ───────────────────────────────────────────")
    y_proba = model.predict_proba(X_test_sel)[:, 1]
    y_pred  = (y_proba >= threshold).astype(int)

    f1      = f1_score(y_test, y_pred)
    recall  = recall_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)
    cm      = confusion_matrix(y_test, y_pred)

    print(f"    Decision threshold   : {threshold:.4f}")
    print(f"    F1 Score (bankrupt)  : {f1:.4f}  "
          f"{'✓' if f1 > 0.72 else '✗ target > 0.72'}")
    print(f"    Recall   (bankrupt)  : {recall:.4f}  "
          f"{'✓' if recall > 0.75 else '✗ target > 0.75'}")
    print(f"    ROC-AUC              : {roc_auc:.4f}  "
          f"{'✓' if roc_auc > 0.90 else '✗ target > 0.90'}")
    print(f"\n    Confusion Matrix:\n{cm}")
    print(f"\n    Classification Report:\n"
          f"{classification_report(y_test, y_pred, target_names=['Safe', 'Bankrupt'])}")

    return {"f1": f1, "recall": recall, "roc_auc": roc_auc, "cm": cm}


# ══════════════════════════════════════════════════════════════════════════════
# SAVE ARTEFACTS
# ══════════════════════════════════════════════════════════════════════════════

def save_artifacts(model, scaler, top_features: list, threshold: float,
                   clip_lower: np.ndarray, clip_upper: np.ndarray):
    """Persist model, scaler, feature list, clip bounds, and threshold to disk."""
    print("\n── Saving Artefacts ──────────────────────────────────────────────")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    with open(MODEL_PATH,      "wb") as f: pickle.dump(model,        f)
    with open(SCALER_PATH,     "wb") as f: pickle.dump(scaler,       f)
    with open(FEATURES_PATH,   "wb") as f: pickle.dump(top_features, f)
    with open(THRESHOLD_PATH,  "wb") as f: pickle.dump(threshold,    f)
    with open(CLIP_BOUNDS_PATH,"wb") as f: pickle.dump(
        {"lower": clip_lower, "upper": clip_upper}, f)

    print(f"    Model       → {MODEL_PATH}")
    print(f"    Scaler      → {SCALER_PATH}")
    print(f"    Features    → {FEATURES_PATH}")
    print(f"    Clip bounds → {CLIP_BOUNDS_PATH}")
    print(f"    Threshold   → {THRESHOLD_PATH}  (value: {threshold:.4f})")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  BankruptcySense AI — Training Pipeline")
    print("=" * 65)

    # 1. Load
    df = load_arff(DATA_RAW_PATH)

    # 2. Drop high-missing columns
    df = drop_high_missing(df, MISSING_DROP_THRESHOLD)

    # 3. Stratified split  ← FIRST before any fitting
    X_train, X_test, y_train, y_test = split_data(df)
    feature_names = list(X_train.columns)

    # 4. Impute (fit on train)
    X_train, X_test = impute_median(X_train, X_test)

    # 5. Clip outliers (percentiles from train)
    X_train, X_test, clip_lower, clip_upper = clip_outliers(X_train, X_test)

    # 6. Scale (fit on train)
    X_train_sc, X_test_sc, scaler = scale_features(X_train, X_test)

    # 7. SMOTE (train only)
    X_train_res, y_train_res = apply_smote(X_train_sc, y_train)

    # 8. Feature selection (fit on SMOTE-resampled train)
    X_train_sel, X_test_sel, top_features, _ = select_top_features(
        X_train_res, y_train_res, X_test_sc, feature_names, TOP_N_FEATURES
    )

    # 9. Tune hyperparameters
    best_model, _ = tune_model(X_train_sel, y_train_res)

    # CV stability
    check_cv_stability(best_model, X_train_sel, y_train_res)

    # 10. Tune decision threshold using OOF probabilities on original train
    all_features    = feature_names
    feature_indices = [all_features.index(f) for f in top_features]
    X_train_orig_sel = X_train_sc[:, feature_indices]
    threshold = tune_threshold(best_model, X_train_orig_sel, y_train)

    # 11. Final test evaluation with tuned threshold
    metrics = evaluate_on_test(best_model, X_test_sel, y_test, threshold)

    # 12. Save all artefacts
    save_artifacts(best_model, scaler, top_features, threshold, clip_lower, clip_upper)

    print("\n" + "=" * 65)
    print("  Training complete.")
    print("=" * 65)

    return metrics


if __name__ == "__main__":
    main()
