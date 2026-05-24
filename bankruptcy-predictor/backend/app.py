"""
backend/app.py
==============
Flask REST API — main entry point.

Endpoints:
  GET  /health              → liveness check
  GET  /features            → list of expected feature names
  POST /predict             → single prediction
  POST /predict/batch       → batch prediction (up to 500 rows)
  GET  /history             → recent prediction history
  DELETE /history           → clear history

All responses are JSON. Errors follow:
  { "error": "message", "status": <http_code> }
"""

import sys
import os

# ── project root on sys.path ───────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, request, jsonify
from flask_cors import CORS

from validator import validate_single, validate_batch, ValidationError, VALID_FEATURES
from predictor import run_single, run_batch, get_history, clear_history

# ── app setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Allow all origins in development; tighten to your Vercel URL in production
# via the CORS_ORIGINS environment variable.
_CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
CORS(app, resources={r"/*": {"origins": _CORS_ORIGINS}})


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found.", "status": 404}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed.", "status": 405}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error.", "status": 500}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/", methods=["GET"])
def home():
    """Root route — satisfies Render's default health check on GET /"""
    return jsonify({
        "status":  "ok",
        "message": "BankruptcySense API is running",
        "docs": {
            "health":        "GET  /health",
            "features":      "GET  /features",
            "predict":       "POST /predict",
            "predict_batch": "POST /predict/batch",
            "history":       "GET  /history",
        }
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """
    Liveness check — used by Render health checks and the frontend status badge.

    Response 200:
      { "status": "ok", "model": "loaded" }
    """
    return jsonify({"status": "ok", "model": "loaded"}), 200


@app.route("/features", methods=["GET"])
def features():
    """
    Return the list of feature names the model expects.
    Useful for the frontend form to dynamically render inputs.

    Response 200:
      { "features": ["Attr1", "Attr2", ...], "count": 63 }
    """
    feature_list = sorted(VALID_FEATURES, key=lambda x: int(x.replace("Attr", "")))
    return jsonify({"features": feature_list, "count": len(feature_list)}), 200


@app.route("/predict", methods=["POST"])
def predict():
    """
    Single-company bankruptcy prediction.

    Request body (JSON):
      { "Attr1": 0.12, "Attr6": 1.5, ... }
      (any subset of Attr1–Attr64 excluding Attr37)

    Response 200:
      {
        "prediction":   0 | 1,
        "label":        "Safe" | "Bankrupt",
        "probability":  float,
        "confidence":   float,
        "risk_level":   "Low" | "Medium" | "High" | "Critical",
        "trusted":      bool,
        "threshold":    float,
        "top_features": [ { "feature": str, "value": float, "importance": float } ],
        "history_id":   str
      }

    Response 400:  validation error
    Response 422:  prediction error (model returned an error)
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON.", "status": 400}), 400

    try:
        clean = validate_single(data)
    except ValidationError as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    result = run_single(clean)

    if result.get("error"):
        return jsonify({"error": result["error"], "status": 422}), 422

    return jsonify(result), 200


@app.route("/predict/batch", methods=["POST"])
def predict_batch_route():
    """
    Batch bankruptcy prediction (CSV upload processed by frontend → JSON here).

    Request body (JSON):
      [ { "Attr1": 0.12, ... }, { "Attr1": 0.55, ... }, ... ]
      OR
      { "records": [ {...}, {...} ] }

    Response 200:
      {
        "total":    int,
        "bankrupt": int,
        "safe":     int,
        "errors":   int,
        "results":  [ <result_dict>, ... ],
        "summary":  { "bankrupt_rate": float, "safe_rate": float }
      }

    Response 400:  validation error
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON.", "status": 400}), 400

    try:
        records = validate_batch(data)
    except ValidationError as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    result = run_batch(records)
    return jsonify(result), 200


@app.route("/history", methods=["GET"])
def history():
    """
    Return recent prediction history (newest first).

    Query params:
      limit (int, default 50, max 200)

    Response 200:
      [
        {
          "id":        str,
          "timestamp": str,
          "input":     dict,
          "result":    dict
        },
        ...
      ]
    """
    try:
        limit = int(request.args.get("limit", 50))
    except (ValueError, TypeError):
        limit = 50

    entries = get_history(limit=limit)
    return jsonify(entries), 200


@app.route("/history", methods=["DELETE"])
def delete_history():
    """
    Clear all prediction history.

    Response 200:
      { "message": "History cleared.", "entries_deleted": int }
    """
    result = clear_history()
    return jsonify(result), 200


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Development server only — Render uses gunicorn (see Procfile)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
