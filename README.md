# 📉 BankruptcySense AI

<div align="center">

### 🤖 AI-Powered Bankruptcy Prediction for Small Businesses

Predict potential business bankruptcy using Machine Learning and financial indicators.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-RandomForest-orange?logo=scikitlearn)
![Flask](https://img.shields.io/badge/Flask-API-black?logo=flask)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![Vite](https://img.shields.io/badge/Vite-Frontend-purple?logo=vite)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-Styling-38B2AC?logo=tailwind-css)
![Render](https://img.shields.io/badge/Backend-Render-46E3B7)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)

</div>

---

## 🚀 Overview

**BankruptcySense AI** is a machine learning system that predicts the likelihood of a company going bankrupt within five years using financial statement indicators.

The project combines:

- 🤖 Machine Learning (Random Forest)
- 📊 Data Preprocessing & Feature Engineering
- 🌐 REST API Backend
- ⚛️ Interactive React Dashboard
- ☁️ Cloud Deployment

Built using the **Polish Bankruptcy Dataset** from UCI.

---

# 🛠 Tech Stack

| Layer | Technologies |
|---------|-------------|
| 🤖 Machine Learning | Python, Scikit-learn, SMOTE, RandomizedSearchCV |
| ⚙️ Backend | Flask, Gunicorn |
| 🎨 Frontend | React 18, Vite, Tailwind CSS, Recharts |
| ☁️ Deployment | Render, Vercel |
| 📂 Dataset | Polish Bankruptcy Dataset (5year.arff) |

---

# ✨ Features

### 🤖 AI Prediction Engine
- Bankruptcy risk prediction
- Probability scoring
- Optimized Random Forest model

### 📊 Data Processing
- Missing value handling
- Outlier clipping
- Feature selection
- Data scaling

### 📁 Batch Processing
- CSV upload support
- Batch predictions
- Export-ready results

### 📈 Analytics Dashboard
- Interactive charts
- Prediction history
- Feature visualization

### 🔌 REST API
- Single prediction endpoint
- Batch prediction endpoint
- Prediction history management

---

# 📊 Model Performance

| Metric | Score |
|---------|--------|
| ROC-AUC | **0.912** ✅ |
| Recall (Bankrupt) | **0.793** ✅ |
| F1 Score (Bankrupt) | **0.461** |
| CV Std (F1) | **0.005** ✅ |

### 📌 Dataset Notes

- Bankruptcy rate ≈ **7%**
- Highly imbalanced classification problem
- Published benchmarks typically achieve:
  - F1 = 0.45 – 0.65
  - ROC-AUC = 0.85 – 0.92

> Despite severe class imbalance, BankruptcySense AI achieves strong recall while maintaining competitive ROC-AUC performance.

---

# 🧠 ML Pipeline

```text
Load Dataset
      │
      ▼
Train/Test Split
      │
      ▼
Median Imputation
      │
      ▼
Outlier Clipping
      │
      ▼
Feature Scaling
      │
      ▼
SMOTE Oversampling
      │
      ▼
Feature Selection
      │
      ▼
RandomizedSearchCV
      │
      ▼
Threshold Optimization
      │
      ▼
Model Export
```

### Pipeline Details

1. Load ARFF dataset
2. Decode bytes & rename target
3. Stratified train/test split
4. Median imputation
5. Outlier clipping (1st–99th percentile)
6. StandardScaler
7. SMOTE oversampling
8. Top-30 feature selection
9. RandomizedSearchCV tuning
10. Threshold optimization
11. Save trained artifacts

✅ No Data Leakage

---

# 🏗 Project Structure

```text
bankruptcy-predictor/
│
├── config.py
│
├── data/
│   └── raw/
│       └── 5year.arff
│
├── ml/
│   ├── train.py
│   ├── evaluate.py
│   ├── predict.py
│   └── model/
│
├── backend/
│   ├── app.py
│   ├── predictor.py
│   ├── validator.py
│   ├── requirements.txt
│   └── Procfile
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api/
    │   └── components/
    ├── package.json
    └── vercel.json
```

---

# 🔌 API Endpoints

| Method | Endpoint | Description |
|----------|------------|-------------|
| GET | `/health` | Health Check |
| GET | `/features` | Available Features |
| POST | `/predict` | Single Prediction |
| POST | `/predict/batch` | Batch Prediction |
| GET | `/history` | Prediction History |
| DELETE | `/history` | Clear History |

---

# 💻 Local Development

## 1️⃣ Train Model

```bash
cd bankruptcy-predictor

pip install -r requirements.txt

python ml/train.py
```

---

## 2️⃣ Run Backend

```bash
cd backend

pip install -r requirements.txt

python app.py
```

Backend:

```text
http://localhost:5000
```

---

## 3️⃣ Run Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# ☁️ Deployment

## Backend (Render)

```bash
Build:
pip install -r requirements.txt

Start:
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### Required Environment Variables

```env
CORS_ORIGINS=https://your-app.vercel.app
```

---

## Frontend (Vercel)

### Environment Variable

```env
VITE_API_URL=https://your-render-service.onrender.com
```

Deploy normally — Vercel automatically detects Vite.

---

# 📁 Batch CSV Format

```csv
Attr1,Attr6,Attr13,Attr35
0.12,1.5,0.08,-0.3
-0.05,0.8,0.02,-1.2
```

✅ Any subset of Attr1–Attr64 is accepted

✅ Missing columns are automatically imputed

---

# 🎯 Future Improvements

- SHAP Explainability
- XGBoost Benchmark
- User Authentication
- Prediction Export Reports
- Docker Support
- CI/CD Pipeline

---

# 👨‍💻 Author

**Sisiyo Takele**

Machine Learning & Full Stack Developer

- Python
- React
- Flask
- Machine Learning
- Data Science

---

<div align="center">

### ⭐ If you found this project useful, give it a star!

📉 BankruptcySense AI

Predicting financial risk through Machine Learning.

</div>
