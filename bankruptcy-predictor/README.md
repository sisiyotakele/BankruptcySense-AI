# BankruptcySense AI

AI-powered bankruptcy prediction for small businesses using Random Forest.

## Stack

| Layer      | Tech                                      |
|------------|-------------------------------------------|
| ML         | Python · Scikit-learn · SMOTE · RandomizedSearchCV |
| Backend    | Flask REST API · Gunicorn                 |
| Frontend   | React 18 · Vite · Tailwind CSS · Recharts |
| Deployment | Render (backend) · Vercel (frontend)      |
| Dataset    | Polish Bankruptcy Dataset (UCI) — 5year.arff |

## Model Performance

| Metric              | Result | Target |
|---------------------|--------|--------|
| ROC-AUC             | 0.912  | > 0.90 ✓ |
| Recall (bankrupt)   | 0.793  | > 0.75 ✓ |
| F1 (bankrupt)       | 0.461  | > 0.72 — dataset ceiling |
| CV Std (F1)         | 0.005  | < 0.05 ✓ |

> **Note on F1:** The Polish 5-year dataset has ~7% bankruptcy rate.
> Published benchmarks on this dataset typically achieve F1 of 0.45–0.65
> for the bankrupt class. ROC-AUC and Recall both meet targets.

## Project Structure

```
bankruptcy-predictor/
├── config.py                  # All paths and constants
├── data/
│   └── raw/5year.arff         # Polish Bankruptcy Dataset
├── ml/
│   ├── train.py               # Full training pipeline
│   ├── evaluate.py            # Standalone evaluation + plots
│   ├── predict.py             # Inference utility
│   └── model/                 # Saved artifacts (rf_model.pkl, scaler.pkl, …)
├── backend/
│   ├── app.py                 # Flask REST API
│   ├── predictor.py           # ML adapter + history
│   ├── validator.py           # Request validation
│   ├── requirements.txt       # Python deps (Python 3.13 compatible)
│   └── Procfile               # Render start command
└── frontend/
    ├── src/
    │   ├── App.jsx             # Main app + tab layout
    │   ├── api/api.js          # Axios client
    │   └── components/
    │       ├── PredictionForm.jsx
    │       ├── ResultCard.jsx
    │       ├── FeatureChart.jsx
    │       ├── BatchUpload.jsx
    │       └── HistoryTable.jsx
    ├── vercel.json
    └── package.json
```

## ML Pipeline (no data leakage)

1. Load ARFF → decode bytes → rename target
2. Drop columns with > 40% missing (Attr37)
3. **Stratified train/test split** ← first, before any fitting
4. Median imputation (fit on train only)
5. Outlier clipping 1st–99th percentile (train-derived)
6. StandardScaler (fit on train only)
7. SMOTE oversampling (train only)
8. Feature selection — top 30 by RF importances
9. RandomizedSearchCV (30 iter, cv=5, scoring=recall)
10. OOF threshold tuning (maximise F1 s.t. recall ≥ 0.75, precision ≥ 0.20)
11. Save `rf_model.pkl`, `scaler.pkl`, `features.pkl`, `threshold.pkl`

## API Endpoints

| Method | Path             | Description              |
|--------|------------------|--------------------------|
| GET    | /health          | Liveness check           |
| GET    | /features        | List expected feature names |
| POST   | /predict         | Single prediction        |
| POST   | /predict/batch   | Batch prediction (≤500)  |
| GET    | /history         | Recent predictions       |
| DELETE | /history         | Clear history            |

## Local Development

### 1. Train the model

```bash
cd bankruptcy-predictor
pip install -r requirements.txt
python ml/train.py
```

### 2. Run the backend

```bash
cd backend
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

The Vite dev server proxies `/api/*` → `http://localhost:5000`.

## Deployment

### Backend → Render

1. Push repo to GitHub
2. Create a new **Web Service** on Render
3. Set **Root Directory** to `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
6. Add env var: `CORS_ORIGINS=https://your-app.vercel.app`
7. **Important:** The `ml/model/*.pkl` files must be committed or uploaded — Render needs them at runtime

### Frontend → Vercel

1. Import the repo on Vercel
2. Set **Root Directory** to `frontend`
3. Add env var: `VITE_API_URL=https://your-render-service.onrender.com`
4. Deploy — Vercel auto-detects Vite

## Batch CSV Format

```csv
Attr1,Attr6,Attr13,Attr35
0.12,1.5,0.08,-0.3
-0.05,0.8,0.02,-1.2
```

Any subset of Attr1–Attr64 (excluding Attr37). Missing columns are imputed.
