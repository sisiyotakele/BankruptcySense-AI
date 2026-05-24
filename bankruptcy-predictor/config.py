# config.py — single source of truth for all paths and constants
# Import this everywhere instead of hardcoding values

import os

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))

DATA_RAW_PATH    = os.path.join(BASE_DIR, "data", "raw", "5year.arff")
DATA_PROC_PATH   = os.path.join(BASE_DIR, "data", "processed")

MODEL_PATH       = os.path.join(BASE_DIR, "ml", "model", "rf_model.pkl")
SCALER_PATH      = os.path.join(BASE_DIR, "ml", "model", "scaler.pkl")
FEATURES_PATH    = os.path.join(BASE_DIR, "ml", "model", "features.pkl")

# Path where evaluate.py saves the confusion matrix plot
CONFUSION_MATRIX_PATH = os.path.join(BASE_DIR, "ml", "model", "confusion_matrix.png")

# Path where the optimal decision threshold is saved after training
THRESHOLD_PATH = os.path.join(BASE_DIR, "ml", "model", "threshold.pkl")

# ── Model / Training ───────────────────────────────────────────────────────────
IMAGE_SIZE           = (64, 64)   # not used here, kept for consistency
TOP_N_FEATURES       = 30         # number of features to keep after selection
TEST_SIZE            = 0.2        # 80/20 train-test split
RANDOM_STATE         = 42

# ── Prediction ─────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.60       # minimum probability to trust a prediction

# ── Preprocessing ──────────────────────────────────────────────────────────────
MISSING_DROP_THRESHOLD = 0.40     # drop columns with > 40 % missing values
OUTLIER_LOWER_PCTILE   = 1        # clip below this percentile
OUTLIER_UPPER_PCTILE   = 99       # clip above this percentile

# ── RandomizedSearchCV ─────────────────────────────────────────────────────────
N_ITER_SEARCH  = 30
CV_FOLDS       = 5
SCORING_METRIC = "recall"   # optimise recall directly — bankrupt class is the priority

# Minimum precision floor when tuning threshold (avoids flagging everything as bankrupt)
MIN_PRECISION_FLOOR = 0.20
# Minimum recall required when tuning threshold
MIN_RECALL_FLOOR    = 0.75

# Hyperparameter search space
RF_PARAM_DIST = {
    "n_estimators":      [100, 200, 300],
    "max_depth":         [10, 20, 30, None],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf":  [1, 2, 4],
    "max_features":      ["sqrt", "log2", 0.3],
    "bootstrap":         [True],           # False is much slower — keep True
    "class_weight":      ["balanced", "balanced_subsample"],
}
