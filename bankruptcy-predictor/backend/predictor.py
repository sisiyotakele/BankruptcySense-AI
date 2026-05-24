"""
backend/predictor.py
====================
Thin adapter between the Flask routes and ml/predict.py.

Responsibilities:
  - Re-export predict_single and predict_batch from ml/predict.py
  - Add prediction history persistence (history.json)
  - Provide get_history() and clear_history() for the history endpoints
  - Keep app.py clean — no ML logic lives there

History entry schema:
  {
    "id":          str,    # uuid4
    "timestamp":   str,    # ISO-8601 UTC
    "input":       dict,   # sanitised input features
    "result":      dict,   # full result dict from predict_single
  }
"""

import sys
import os
import json
import uuid
from datetime import datetime, timezone

# ── project root on sys.path ───────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── import ML prediction functions ────────────────────────────────────────────
from ml.predict import predict_single as _predict_single
from ml.predict import predict_batch  as _predict_batch

# ── history file path ──────────────────────────────────────────────────────────
_HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
_MAX_HISTORY  = 200   # cap stored entries to avoid unbounded growth


# ══════════════════════════════════════════════════════════════════════════════
# HISTORY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _load_history() -> list:
    """Load history from disk. Returns empty list on any read error."""
    try:
        with open(_HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_history(history: list) -> None:
    """Persist history list to disk. Silently swallows write errors."""
    try:
        with open(_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except OSError:
        pass   # non-fatal — history is a convenience feature


def _append_history(input_data: dict, result: dict) -> dict:
    """
    Create a history entry, append it to history.json, and return the entry.
    Caps history at _MAX_HISTORY entries (oldest dropped first).
    """
    entry = {
        "id":        str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input":     input_data,
        "result":    result,
    }
    history = _load_history()
    history.append(entry)
    if len(history) > _MAX_HISTORY:
        history = history[-_MAX_HISTORY:]
    _save_history(history)
    return entry


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def run_single(input_data: dict) -> dict:
    """
    Run a single prediction and persist it to history.

    Parameters
    ----------
    input_data : dict
        Sanitised feature dict from validator.validate_single().

    Returns
    -------
    dict  — result dict from predict_single, augmented with 'history_id'
    """
    result = _predict_single(input_data)
    if result.get("error") is None:
        entry  = _append_history(input_data, result)
        result["history_id"] = entry["id"]
    return result


def run_batch(records: list) -> dict:
    """
    Run batch predictions. History is NOT stored for batch (too noisy).

    Parameters
    ----------
    records : list[dict]
        Sanitised list from validator.validate_batch().

    Returns
    -------
    dict  — {
        "total":     int,
        "bankrupt":  int,
        "safe":      int,
        "results":   list[dict],
        "summary":   dict,
    }
    """
    results   = _predict_batch(records)
    bankrupt  = sum(1 for r in results if r.get("prediction") == 1)
    safe      = sum(1 for r in results if r.get("prediction") == 0)
    errors    = sum(1 for r in results if r.get("error") is not None)

    return {
        "total":    len(results),
        "bankrupt": bankrupt,
        "safe":     safe,
        "errors":   errors,
        "results":  results,
        "summary": {
            "bankrupt_rate": round(bankrupt / len(results), 4) if results else 0,
            "safe_rate":     round(safe     / len(results), 4) if results else 0,
        },
    }


def get_history(limit: int = 50) -> list:
    """
    Return the most recent `limit` history entries (newest first).

    Parameters
    ----------
    limit : int
        Max number of entries to return. Capped at _MAX_HISTORY.
    """
    limit   = min(max(1, limit), _MAX_HISTORY)
    history = _load_history()
    return list(reversed(history[-limit:]))


def clear_history() -> dict:
    """Delete all history entries. Returns confirmation dict."""
    _save_history([])
    return {"message": "History cleared.", "entries_deleted": len(_load_history())}
