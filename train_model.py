"""
train_model.py
==============
Version 3 — Multi-model comparison with automatic best-model selection.

Classifiers compared
--------------------
1. Logistic Regression  (L2, C=2.0, balanced)
2. Linear SVM           (LinearSVC, C=1.0, balanced)
3. Passive Aggressive   (C=0.5)
4. Multinomial Naive Bayes (alpha=0.1)

Winner (highest 5-fold Stratified CV accuracy on training data) is saved
as model.pkl.  Its name is saved to model_name.txt so the app can display it.

AI Fake News Detection & Live Verification System — Version 3
Government Polytechnic West Champaran — AI & ML Internship 2026
Developed by: Naman Kumar & Parmeshwar
"""

from __future__ import annotations

import logging
import os
import pickle
import re
import warnings

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Text Preprocessing ────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]",      " ", text)
    text = re.sub(r"\s+",              " ", text).strip()
    return text


# ── Candidate Classifier Definitions ─────────────────────────────────────────

def _build_candidates() -> list[tuple[str, object]]:
    """
    Return list of (name, estimator) pairs.
    LinearSVC and PassiveAggressive are wrapped in CalibratedClassifierCV
    so they expose predict_proba (needed for soft confidence scores).
    """
    lr  = LogisticRegression(
        C=2.0, solver="lbfgs", max_iter=1000,
        class_weight="balanced", random_state=42,
    )
    svm = CalibratedClassifierCV(
        LinearSVC(C=1.0, class_weight="balanced",
                  max_iter=2000, random_state=42),
        cv=3,
    )
    pac = CalibratedClassifierCV(
        PassiveAggressiveClassifier(
            C=0.5, max_iter=1000, random_state=42,
            class_weight="balanced",
        ),
        cv=3,
    )
    mnb = MultinomialNB(alpha=0.1)

    return [
        ("Logistic Regression",       lr),
        ("Linear SVM (Calibrated)",   svm),
        ("Passive Aggressive (Cal.)", pac),
        ("Multinomial Naive Bayes",   mnb),
    ]


# ── Dataset Loader ────────────────────────────────────────────────────────────

def load_dataset(path: str = "dataset.csv") -> pd.DataFrame:
    logger.info("Loading dataset from: %s", path)
    df = pd.read_csv(path)
    required = {"text", "label"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {missing}")

    df = df.dropna(subset=["text", "label"])
    df["text"]         = df["text"].astype(str).str.strip()
    df["label"]        = df["label"].str.upper().str.strip()
    df["text_clean"]   = df["text"].apply(clean_text)
    df["label_binary"] = (df["label"] == "FAKE").astype(int)

    logger.info(
        "Dataset — %d samples | REAL: %d | FAKE: %d",
        len(df),
        (df["label"] == "REAL").sum(),
        (df["label"] == "FAKE").sum(),
    )
    return df


# ── Training & Model Selection ────────────────────────────────────────────────

def train(df: pd.DataFrame) -> tuple:
    """
    1. Split into train/test (80/20 stratified).
    2. Fit TF-IDF vectorizer on training data only.
    3. Run 5-fold CV for each candidate on (X_train_vec, y_train).
    4. Select the model with the highest CV mean accuracy.
    5. Evaluate winner on held-out test set.

    Returns (best_model, vectorizer, best_name, metrics_dict)
    """
    X = df["text_clean"].values
    y = df["label_binary"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y,
    )
    logger.info("Train: %d | Test: %d", len(X_train), len(X_test))

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=15_000,
        sublinear_tf=True,
        min_df=1,
        max_df=0.95,
        analyzer="word",
        token_pattern=r"\b[a-z][a-z0-9]*\b",
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec  = vectorizer.transform(X_test)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    candidates = _build_candidates()

    best_name  = ""
    best_score = -1.0
    best_model = None
    results_log: list[str] = []

    logger.info("=" * 55)
    logger.info("  Model Comparison (5-fold CV on training data)")
    logger.info("=" * 55)

    for name, clf in candidates:
        try:
            cv_scores = cross_val_score(
                clf, X_train_vec, y_train,
                cv=cv, scoring="accuracy",
            )
            mean_cv = cv_scores.mean()
            std_cv  = cv_scores.std()
            line    = f"  {name:<35} CV: {mean_cv:.4f} ± {std_cv:.4f}"
            logger.info(line)
            results_log.append(line)

            if mean_cv > best_score:
                best_score = mean_cv
                best_name  = name
                best_model = clf
        except Exception as exc:
            logger.warning("  %s FAILED: %s", name, exc)

    logger.info("=" * 55)
    logger.info("  ✅ Best model: %s (CV: %.4f)", best_name, best_score)
    logger.info("=" * 55)

    # Final fit of winner on full training data
    best_model.fit(X_train_vec, y_train)

    # Evaluate on test set
    y_pred = best_model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    report   = classification_report(y_test, y_pred, target_names=["REAL", "FAKE"])
    cm       = confusion_matrix(y_test, y_pred)

    if hasattr(best_model, "predict_proba"):
        y_prob = best_model.predict_proba(X_test_vec)[:, 1]
        roc    = roc_auc_score(y_test, y_prob)
    else:
        roc = 0.0

    logger.info("Test Accuracy : %.4f", accuracy)
    logger.info("ROC-AUC       : %.4f", roc)
    logger.info("\n%s", report)

    metrics = {
        "best_model_name":  best_name,
        "best_cv_score":    round(best_score, 4),
        "accuracy":         round(accuracy, 4),
        "roc_auc":          round(roc, 4),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "train_samples":    len(X_train),
        "test_samples":     len(X_test),
        "model_comparison": results_log,
    }

    return best_model, vectorizer, best_name, metrics


# ── Save Artifacts ────────────────────────────────────────────────────────────

def save_artifacts(
    model,
    vectorizer,
    model_name: str,
    metrics:    dict,
    out_dir:    str = ".",
) -> None:
    model_path = os.path.join(out_dir, "model.pkl")
    vec_path   = os.path.join(out_dir, "vectorizer.pkl")
    name_path  = os.path.join(out_dir, "model_name.txt")
    metrics_path = os.path.join(out_dir, "model_metrics.txt")

    with open(model_path, "wb") as f:
        pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(vec_path, "wb") as f:
        pickle.dump(vectorizer, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(name_path, "w") as f:
        f.write(model_name)

    with open(metrics_path, "w") as f:
        f.write("=" * 62 + "\n")
        f.write("  AI Fake News Detection — V3 Model Training Report\n")
        f.write("=" * 62 + "\n\n")
        f.write(f"  Best Model     : {metrics['best_model_name']}\n")
        f.write(f"  Best CV Score  : {metrics['best_cv_score']}\n")
        f.write(f"  Test Accuracy  : {metrics['accuracy']}\n")
        f.write(f"  ROC-AUC        : {metrics['roc_auc']}\n")
        f.write(f"  Train Samples  : {metrics['train_samples']}\n")
        f.write(f"  Test Samples   : {metrics['test_samples']}\n\n")
        f.write("  Model Comparison Results:\n")
        for line in metrics.get("model_comparison", []):
            f.write(line + "\n")
        f.write("\n")
        f.write(metrics["classification_report"])
        f.write("\nConfusion Matrix:\n")
        for row in metrics["confusion_matrix"]:
            f.write(f"  {row}\n")
        f.write("\n" + "=" * 62 + "\n")
        f.write("  Developed by: Naman Kumar & Parmeshwar\n")
        f.write("  Government Polytechnic West Champaran\n")
        f.write("  AI & ML Internship 2026\n")
        f.write("=" * 62 + "\n")

    logger.info("Artifacts saved: model.pkl, vectorizer.pkl, model_name.txt, model_metrics.txt")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 62)
    logger.info("  AI Fake News Detection V3 — Multi-Model Training")
    logger.info("  Government Polytechnic West Champaran")
    logger.info("  Developed by: Naman Kumar & Parmeshwar")
    logger.info("=" * 62)

    script_dir   = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(script_dir, "dataset.csv")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"dataset.csv not found at {dataset_path}")

    df = load_dataset(dataset_path)
    best_model, vectorizer, best_name, metrics = train(df)
    save_artifacts(best_model, vectorizer, best_name, metrics, out_dir=script_dir)

    logger.info(
        "Training complete! Best: %s | Accuracy: %.2f%%",
        best_name, metrics["accuracy"] * 100,
    )


if __name__ == "__main__":
    main()
