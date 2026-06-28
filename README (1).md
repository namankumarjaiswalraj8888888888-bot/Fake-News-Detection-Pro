---
title: AI Fake News Detection & Live Verification System
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.33.0
app_file: app.py
pinned: false
license: mit
python_version: "3.11"
---

# 🔍 AI Fake News Detection & Live Verification System — Version 3

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Gradio](https://img.shields.io/badge/Gradio-4.x-orange?logo=gradio)](https://gradio.app)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-green)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HuggingFace Spaces](https://img.shields.io/badge/🤗%20HuggingFace-Spaces-purple)](https://huggingface.co/spaces)
[![100% Free](https://img.shields.io/badge/API%20Cost-100%25%20Free-brightgreen)](.)

> **AI & Machine Learning Internship Project 2026**
> Government Polytechnic West Champaran · Department of Computer Science & Engineering
> SBTE Bihar · Diploma Engineering · Session 2025–2028
> **Developed by: Naman Kumar & Parmeshwar**

---

## 📌 Overview

A production-ready, end-to-end **free real-time multi-source fact verification system** that combines multi-model machine learning with live evidence gathering from trusted publishers to classify any news article, headline, or URL as:

| Label | Meaning |
|-------|---------|
| ✅ **REAL** | Supported by trusted sources + ML model |
| ❌ **FAKE** | Contradicted by trusted sources + ML signals |
| ⚠️ **UNVERIFIED** | Insufficient evidence — system never guesses |

The system **never blindly trusts** a single model. It cross-references live results from multiple trusted sources before delivering a verdict. **Zero paid APIs required.**

---

## 🆕 What's New in Version 3

| Feature | V2 | V3 |
|---------|----|----|
| Input modes | Text only | Text **+ News URL** |
| ML models | Logistic Regression (fixed) | **4-model comparison**, auto-select best |
| Confidence | Single score | **ML Confidence + Evidence Confidence + Overall** |
| Search | DuckDuckGo + RSS | **Parallel** RSS + DDG + PIB Fact-Check, LRU cache |
| Source trust | Binary (trusted / not) | **Weighted trust scores (0–100)** |
| Claim extraction | Sentence split | **Factual claim heuristic** (primary claim surfaced) |
| Evidence scoring | Count-based | **Trust-weighted evidence score** |
| Display | Single confidence bar | **Three confidence bars + trust badge** |
| Publication date | Not shown | Extracted and displayed per article |
| Error handling | Basic try/catch | **Retry logic, TTL cache, graceful degradation** |

---

## 🏗️ Architecture

```
User Input (Text or URL)
         ↓
URL? → Fetch article text (extract_article_text)
         ↓
Text Cleaning & Preprocessing (utils.py)
         ↓
Factual Claim Extraction (extract_primary_claim)
         ↓
Keyword Mining (extract_keywords)
         ↓
Linguistic Signal Analysis (analyze_linguistic_signals)
         ↓
Parallel Live Search (search.py — ThreadPoolExecutor)
  ├── Google News RSS  (Priority 1)
  ├── DuckDuckGo Lite  (Priority 2 / fallback)
  └── PIB Fact-Check   (supplementary)
         ↓
Trusted-Source Filtering & Trust-Weighted Evidence Scoring
         ↓
Best ML Model Prediction (TF-IDF + auto-selected classifier)
         ↓
Weighted Decision Fusion
  (ML 45% + Evidence 35% + Linguistics 20%)
         ↓
Separate Confidence Scores
  (ML Confidence · Evidence Confidence · Overall Confidence)
         ↓
AI Reasoning Generation
         ↓
   REAL / FAKE / UNVERIFIED
```

---

## 📁 Project Structure

```
fake-news-detector/
├── app.py              # Gradio UI & event handlers
├── fact_checker.py     # Pipeline orchestrator (URL support)
├── search.py           # Multi-source search, trust scores, cache, URL extractor
├── utils.py            # Text processing, claim extraction, ML, decision engine
├── train_model.py      # 4-model comparison & auto-selection training script
├── dataset.csv         # Labeled training dataset (REAL / FAKE)
├── model.pkl           # Best trained model (auto-selected)
├── vectorizer.pkl      # Fitted TF-IDF vectorizer
├── model_name.txt      # Name of the selected best model
├── model_metrics.txt   # Training & comparison report
├── requirements.txt    # Python dependencies (all free)
├── README.md           # This file
├── LICENSE             # MIT License
└── .github/
    └── workflows/
        └── deploy.yml  # Auto-deploy to Hugging Face Spaces
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/fake-news-detector.git
cd fake-news-detector
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Train the Model (optional — pre-trained pkl files included)

```bash
python train_model.py
```

This runs all 4 classifiers, selects the best one, and saves `model.pkl`, `vectorizer.pkl`, `model_name.txt`, and `model_metrics.txt`.

### 4. Run the Application

```bash
python app.py
```

Open your browser at `http://localhost:7860`

---

## 🌐 Live Verification Engine

### Search Priority Order

| Priority | Source | Method |
|----------|--------|--------|
| 1 | Google News RSS | Free RSS feed (no API key) |
| 2 | DuckDuckGo Lite | Free HTML scrape (no API key) |
| 3 | PIB Fact-Check | Government portal scrape |

All queries run **in parallel** via `ThreadPoolExecutor`. Results are **deduplicated by URL** and **cached (5-minute TTL)** to avoid redundant network calls.

### Fallback Chain

```
Google News RSS
    ↓ (if no results)
DuckDuckGo Lite
    ↓ (if no results)
ML model + linguistic analysis only → UNVERIFIED
```

The system **never hallucinates** — if no reliable evidence is found, it returns UNVERIFIED with a clear explanation.

---

## 🏅 Trusted Source Whitelist & Trust Scores

Only sources in the whitelist contribute to the evidence score. Unknown websites are ignored.

| Category | Sources | Trust Score |
|----------|---------|-------------|
| Government / Official | PIB, pib.gov.in, nic.in, india.gov.in | 100 |
| International Bodies | WHO, United Nations | 100 |
| Government Regulators | RBI, SEBI, ICMR, ISRO, ECI | 100 |
| Wire Services | Reuters, Associated Press | 98 |
| Broadcast | BBC, Al Jazeera | 95–97 |
| Indian Press | The Hindu, Indian Express, NDTV | 90–95 |
| Fact-Check Sites | FactCheck.org, Snopes, AltNews, Boom Live | 96–99 |

---

## 🤖 Machine Learning Details

### Model Comparison (V3)

Four classifiers are evaluated on 5-fold stratified CV (training data only — no test leakage). The highest-scoring model is automatically selected:

| Classifier | Notes |
|-----------|-------|
| Logistic Regression | Primary baseline (C=2.0, balanced) |
| Linear SVM (Calibrated) | Wrapped in CalibratedClassifierCV for probabilities |
| Passive Aggressive (Calibrated) | Fast online learner |
| Multinomial Naive Bayes | Classic text classifier (alpha=0.1) |

### Vectorizer

| Component | Configuration |
|-----------|--------------|
| Type | TF-IDF |
| N-grams | 1–3 |
| Max Features | 15,000 |
| Sublinear TF | Yes |
| Min DF | 1 |
| Max DF | 95% |

---

## 📊 Confidence Scores

V3 produces **three independent confidence scores**:

| Score | Source | Weight in Final Decision |
|-------|--------|------------------------|
| ML Confidence | Model prediction probability | 45% |
| Evidence Confidence | Agreement strength of trusted sources | 35% |
| Overall Confidence | Weighted combination | — |

---

## 🔗 URL Support

Paste any news article URL:

```
https://www.thehindu.com/news/national/...
https://www.reuters.com/world/...
https://pib.gov.in/...
```

The system will:
1. Fetch the page (retries on failure)
2. Extract article title and body text
3. Detect the publication date
4. Run full verification on the extracted text

---

## ⚠️ Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `ImportError: sklearn` | Missing dependency | `pip install scikit-learn>=1.4.0` |
| `FileNotFoundError: dataset.csv` | Missing training data | Ensure `dataset.csv` is in project root |
| URL fetch returns empty | Paywalled or JS-rendered page | Use text paste instead |
| All results UNVERIFIED | No network access | Check connectivity; ML still runs offline |
| `model.pkl` missing | First run after clone | Run `python train_model.py` |

---

## 🤗 Deploy to Hugging Face Spaces

### Manual Deployment

```bash
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/fake-news-detector
git push space main
```

### Automatic (GitHub Actions)

Set three GitHub Secrets (`Settings → Secrets → Actions`):

| Secret | Value |
|--------|-------|
| `HF_TOKEN` | Hugging Face write token |
| `HF_USERNAME` | Hugging Face username |
| `HF_SPACE_NAME` | Space name |

Every push to `main` trains the model, selects the best classifier, and deploys automatically.

---

## 🔮 Future Scope

- [ ] Expand dataset to 10,000+ samples
- [ ] Add Hindi / regional language support
- [ ] Image & video fake-news detection
- [ ] Real-time Twitter/X fact-checking
- [ ] Browser extension version
- [ ] Mobile app (Flutter / React Native)
- [ ] GPT-based evidence summarization

---

## ⚠️ Disclaimer

This tool is an AI assistant designed for educational and research purposes.
It should **not** be the sole basis for determining the veracity of any news.
Always cross-reference with multiple authoritative sources.
The system never claims 100% certainty and never hallucinates evidence.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Developers

| Developer | Institution |
|-----------|-------------|
| **Naman Kumar** | Government Polytechnic West Champaran |
| **Parmeshwar** | Government Polytechnic West Champaran |

**Department:** Computer Science & Engineering
**Board:** SBTE Bihar
**Programme:** Diploma Engineering
**Session:** 2025–2028
**Project Type:** AI & Machine Learning Internship 2026

---

*© 2026 Naman Kumar & Parmeshwar · Government Polytechnic West Champaran · AI & ML Internship Project — Version 3*
