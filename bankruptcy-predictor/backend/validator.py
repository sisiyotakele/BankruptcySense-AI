"""
backend/validator.py
====================
Validates and sanitises incoming request payloads before they reach
the predictor. Used by both the single-prediction and batch endpoints.

Rules:
  - Input must be a dict (single) or list of dicts (batch)
  - Each dict must contain at least one recognised feature key
  - All values must be numeric (int or float); strings that parse as
    numbers are coerced; anything else is rejected
  - Batch size is capped at MAX_BATCH_SIZE
  - Unknown keys are silently ignored (predict.py handles missing features)
"""

import sys
import os

# ── project root on sys.path ───────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── constants ──────────────────────────────────────────────────────────────────
MAX_BATCH_SIZE = 500

# All valid feature names (Attr1–Attr64 minus Attr37 which was dropped in training)
VALID_FEATURES = {f"Attr{i}" for i in range(1, 65) if i != 37}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

class ValidationError(ValueError):
    """Raised when request data fails validation. Message is safe to return to client."""
    pass


def _coerce_numeric(value, key: str) -> float:
    """
    Coerce a value to float.
    Accepts int, float, and strings that represent numbers.
    Raises ValidationError for anything else.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            pass
    raise ValidationError(
        f"Feature '{key}' has non-numeric value: {value!r}. "
        "All feature values must be numbers."
    )


def _validate_record(record, record_index: int = None) -> dict:
    """
    Validate and sanitise a single input record (dict).

    Returns a clean dict with only recognised feature keys and float values.
    Raises ValidationError on any problem.
    """
    prefix = f"Record {record_index}: " if record_index is not None else ""

    if not isinstance(record, dict):
        raise ValidationError(
            f"{prefix}Expected a JSON object, got {type(record).__name__}."
        )

    if len(record) == 0:
        raise ValidationError(
            f"{prefix}Input object is empty. "
            "Provide at least one financial ratio (e.g. Attr1, Attr6, …)."
        )

    # Filter to recognised keys and coerce values
    clean = {}
    unknown_keys = []

    for key, value in record.items():
        if key in VALID_FEATURES:
            clean[key] = _coerce_numeric(value, key)
        else:
            unknown_keys.append(key)

    if not clean:
        raise ValidationError(
            f"{prefix}No recognised feature keys found. "
            f"Valid keys are Attr1–Attr64 (excluding Attr37). "
            f"Received: {list(record.keys())[:10]}"
        )

    return clean


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def validate_single(data) -> dict:
    """
    Validate a single-prediction payload.

    Parameters
    ----------
    data : any
        Parsed JSON body from the request.

    Returns
    -------
    dict  — clean, sanitised feature dict ready for predict_single()

    Raises
    ------
    ValidationError  — with a client-safe message
    """
    if not isinstance(data, dict):
        raise ValidationError(
            "Request body must be a JSON object with feature keys. "
            f"Got: {type(data).__name__}."
        )
    return _validate_record(data)


def validate_batch(data) -> list:
    """
    Validate a batch-prediction payload.

    Parameters
    ----------
    data : any
        Parsed JSON body — expected to be a list of dicts,
        or a dict with a 'records' key containing the list.

    Returns
    -------
    list[dict]  — list of clean, sanitised feature dicts

    Raises
    ------
    ValidationError  — with a client-safe message
    """
    # Accept both {"records": [...]} and bare [...]
    if isinstance(data, dict) and "records" in data:
        data = data["records"]

    if not isinstance(data, list):
        raise ValidationError(
            "Batch request body must be a JSON array of objects, "
            f"or a JSON object with a 'records' key. Got: {type(data).__name__}."
        )

    if len(data) == 0:
        raise ValidationError("Batch input is empty. Provide at least one record.")

    if len(data) > MAX_BATCH_SIZE:
        raise ValidationError(
            f"Batch size {len(data)} exceeds the maximum of {MAX_BATCH_SIZE}. "
            "Split your request into smaller batches."
        )

    return [_validate_record(record, i) for i, record in enumerate(data)]
