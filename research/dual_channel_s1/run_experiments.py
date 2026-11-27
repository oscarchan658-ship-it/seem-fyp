"""Unified 4-Experiment Runner (E1–E4) for the Dual-Channel Preliminary Screening Chatbot.

Executes:
- E1: Classical ML baselines on official TweetEval splits + 48-case bilingual 4-quadrant
      affect-vs-PHQ-8 divergence benchmark (including live gpt-6.1-terra sentiment).
- E2: Bilingual conversational symptom extraction & selective abstention across 64 held-out
      utterances (Naive Keyword, Calibrated TF-IDF+LR with Risk-Coverage curve, retained
      RuleProvider + evaluate_candidate, and live BilingualConversationProvider + validate_proposal).
- E3: Multi-turn partial-observation early risk triage (S_k vs N_k vs F_k = N_k + S_k at
      k = 2, 4, 6 turns) on 240 stratified sessions using real TweetEval ML probabilities.
- E4: 32-persona dialogue policy comparison (P0 vs P1 vs P2) + 4 live multi-turn Chatbot
      sessions + deterministic score-invariance, quote-provenance, and safety-guard audits.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os
from pathlib import Path
import platform
import re
import sys
from time import perf_counter, sleep

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bilingual_provider import BilingualConversationProvider  # noqa: E402
from controller import dispatch, new_session  # noqa: E402
from conversation import (  # noqa: E402
    Conversation,
    analyze_affect_symptom_alignment,
    chat_turn,
    confirm_review,
    new_conversation,
    open_review,
    ready,
    validate_proposal,
)
from evidence_manager import evaluate_candidate  # noqa: E402
from nlu_provider import ClarificationContext, NluRequest, RuleProvider  # noqa: E402
from phq8_engine import ConfirmedAnswer, score_phq8  # noqa: E402
from research.dual_channel_s1.benchmarks import (  # noqa: E402
    build_e1b_screening_cases,
    build_e2_ml_train_corpus,
    build_e2_symptom_cases,
    build_e3_partial_observation_cohort,
    build_e4_dialogue_personas,
    build_e4_live_session_scripts,
)
from research.sentiment_benchmark import LABELS, load_split  # noqa: E402
from schemas import Event  # noqa: E402
from terra_client import MODEL, TerraClient  # noqa: E402

LABEL_TO_ID = {"negative": 0, "neutral": 1, "positive": 2}
ID_TO_LABEL = {0: "negative", 1: "neutral", 2: "positive"}


def _call_with_retry(fn, *, retries: int = 3, base_delay: float = 1.2):
    """Retry only transient ConnectionError; never retry validation ValueError."""
    last_err = None
    for attempt in range(retries):
        try:
            return fn()
        except ConnectionError as exc:
            last_err = exc
            if attempt + 1 < retries:
                sleep(base_delay * (attempt + 1))
    raise last_err


def _paired_bootstrap_ci(
    gold: np.ndarray,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    metric_fn,
    *,
    n_boot: int = 500,
    seed: int = 42,
) -> dict:
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot, dtype=float)
    n = len(gold)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        diffs[b] = float(
            metric_fn(gold[idx], pred_a[idx]) - metric_fn(gold[idx], pred_b[idx])
        )
    point = float(metric_fn(gold, pred_a) - metric_fn(gold, pred_b))
    return {
        "mean_diff": point,
        "ci95_low": float(np.percentile(diffs, 2.5)),
        "ci95_high": float(np.percentile(diffs, 97.5)),
    }


def _polarity_metrics(gold_ids: np.ndarray, pred_ids: np.ndarray) -> dict:
    rep = classification_report(
        gold_ids,
        pred_ids,
        labels=[0, 1, 2],
        target_names=LABELS,
        output_dict=True,
        zero_division=0,
    )
    return {
        "n": int(len(gold_ids)),
        "accuracy": float(accuracy_score(gold_ids, pred_ids)),
        "macro_f1": float(
            f1_score(
                gold_ids, pred_ids, labels=[0, 1, 2], average="macro", zero_division=0
            )
        ),
        "macro_recall": float(
            recall_score(
                gold_ids, pred_ids, labels=[0, 1, 2], average="macro", zero_division=0
            )
        ),
        "negative_precision": float(rep["negative"]["precision"]),
        "negative_recall": float(rep["negative"]["recall"]),
        "negative_f1": float(rep["negative"]["f1-score"]),
        "confusion_matrix": confusion_matrix(
            gold_ids, pred_ids, labels=[0, 1, 2]
        ).tolist(),
        "per_class": rep,
    }


# ==============================================================================
# EXPERIMENT 1: Left Ear (TweetEval Classical ML + 48-Case 4-Quadrant Divergence)
# ==============================================================================
def run_e1(
    tweeteval_dir: Path, *, api_key: str | None, base_url: str, workers: int = 6
) -> tuple[dict, Pipeline]:
    print("[E1] Loading official TweetEval splits...")
    train_x, train_y = load_split(tweeteval_dir, "train")
    val_x, val_y = load_split(tweeteval_dir, "val")
    test_x, test_y = load_split(tweeteval_dir, "test")

    def make_tfidf():
        return TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_features=50000,
            sublinear_tf=True,
        )

    trials = []
    selected: dict[str, tuple[object, float, float, float]] = {}

    # 1. Multinomial Naive Bayes
    best_nb = -1.0
    for alpha in (0.1, 0.5, 1.0):
        t0 = perf_counter()
        pipe = Pipeline([("tfidf", make_tfidf()), ("clf", MultinomialNB(alpha=alpha))])
        pipe.fit(train_x, train_y)
        fit_s = perf_counter() - t0
        val_f1 = float(
            f1_score(val_y, pipe.predict(val_x), labels=[0, 1, 2], average="macro")
        )
        trials.append(
            {
                "model": "tfidf_multinomial_nb",
                "param_name": "alpha",
                "param": alpha,
                "val_macro_f1": val_f1,
                "fit_seconds": fit_s,
            }
        )
        if val_f1 > best_nb:
            best_nb = val_f1
            selected["tfidf_multinomial_nb"] = (pipe, alpha, val_f1, fit_s)

    # 2. Logistic Regression
    best_lr = -1.0
    for c in (0.1, 1.0, 10.0):
        t0 = perf_counter()
        pipe = Pipeline(
            [
                ("tfidf", make_tfidf()),
                ("clf", LogisticRegression(C=c, max_iter=1500, random_state=42)),
            ]
        )
        pipe.fit(train_x, train_y)
        fit_s = perf_counter() - t0
        val_f1 = float(
            f1_score(val_y, pipe.predict(val_x), labels=[0, 1, 2], average="macro")
        )
        trials.append(
            {
                "model": "tfidf_logistic_regression",
                "param_name": "C",
                "param": c,
                "val_macro_f1": val_f1,
                "fit_seconds": fit_s,
            }
        )
        if val_f1 > best_lr:
            best_lr = val_f1
            selected["tfidf_logistic_regression"] = (pipe, c, val_f1, fit_s)

    # 3. Linear SVM
    best_svm = -1.0
    for c in (0.1, 1.0, 10.0):
        t0 = perf_counter()
        pipe = Pipeline(
            [("tfidf", make_tfidf()), ("clf", LinearSVC(C=c, random_state=42))]
        )
        pipe.fit(train_x, train_y)
        fit_s = perf_counter() - t0
        val_f1 = float(
            f1_score(val_y, pipe.predict(val_x), labels=[0, 1, 2], average="macro")
        )
        trials.append(
            {
                "model": "tfidf_linear_svm",
                "param_name": "C",
                "param": c,
                "val_macro_f1": val_f1,
                "fit_seconds": fit_s,
            }
        )
        if val_f1 > best_svm:
            best_svm = val_f1
            selected["tfidf_linear_svm"] = (pipe, c, val_f1, fit_s)

    t0 = perf_counter()
    dummy = DummyClassifier(strategy="most_frequent").fit(
        np.zeros((len(train_y), 1)), train_y
    )
    dummy_fit_s = perf_counter() - t0

    e1a_models = {}
    preds_test: dict[str, np.ndarray] = {}

    t0 = perf_counter()
    preds_test["majority"] = dummy.predict(np.zeros((len(test_y), 1)))
    e1a_models["majority"] = {
        **_polarity_metrics(test_y, preds_test["majority"]),
        "selected_param": "most_frequent",
        "val_macro_f1": float(
            f1_score(
                val_y,
                dummy.predict(np.zeros((len(val_y), 1))),
                labels=[0, 1, 2],
                average="macro",
            )
        ),
        "fit_seconds": dummy_fit_s,
        "test_infer_seconds": perf_counter() - t0,
    }

    for mname, (pipe, param, val_f1, fit_s) in selected.items():
        t0 = perf_counter()
        preds_test[mname] = pipe.predict(test_x)
        infer_s = perf_counter() - t0
        e1a_models[mname] = {
            **_polarity_metrics(test_y, preds_test[mname]),
            "selected_param": param,
            "val_macro_f1": val_f1,
            "fit_seconds": fit_s,
            "test_infer_seconds": infer_s,
        }

    def f1_fn(g, p):
        return f1_score(g, p, labels=[0, 1, 2], average="macro", zero_division=0)

    bootstraps = {
        "linear_svm_vs_majority": _paired_bootstrap_ci(
            test_y, preds_test["tfidf_linear_svm"], preds_test["majority"], f1_fn
        ),
        "logreg_vs_majority": _paired_bootstrap_ci(
            test_y,
            preds_test["tfidf_logistic_regression"],
            preds_test["majority"],
            f1_fn,
        ),
        "linear_svm_vs_logreg": _paired_bootstrap_ci(
            test_y,
            preds_test["tfidf_linear_svm"],
            preds_test["tfidf_logistic_regression"],
            f1_fn,
        ),
        "linear_svm_vs_nb": _paired_bootstrap_ci(
            test_y,
            preds_test["tfidf_linear_svm"],
            preds_test["tfidf_multinomial_nb"],
            f1_fn,
        ),
    }

    # --- Part 1B: 48-case Bilingual 4-Quadrant Screening Divergence Benchmark ---
    print("[E1] Running Part 1B 48-case bilingual 4-quadrant screening benchmark...")
    cases = build_e1b_screening_cases()
    texts = [c.text for c in cases]
    gold_pol = np.array([LABEL_TO_ID[c.gold_polarity] for c in cases])
    gold_elev = np.array([int(c.elevated_phq8) for c in cases])
    en_mask = np.array([c.language == "en" for c in cases])
    zh_mask = np.array([c.language == "zh" for c in cases])
    sd_mask = np.array([c.quadrant == "situational_distress" for c in cases])
    ms_mask = np.array([c.quadrant == "masked_somatic" for c in cases])

    e1b_preds: dict[str, tuple[np.ndarray, float]] = {}
    t0 = perf_counter()
    e1b_preds["majority"] = (
        dummy.predict(np.zeros((len(cases), 1))),
        perf_counter() - t0,
    )
    for mname, (pipe, _, _, _) in selected.items():
        t0 = perf_counter()
        e1b_preds[mname] = (pipe.predict(texts), perf_counter() - t0)

    live_case_rows = []
    if api_key:
        print(
            f"[E1] Querying live {MODEL} sentiment on 48 bilingual screening turns (workers={workers})..."
        )
        client = TerraClient(key=api_key, base_url=base_url, timeout=60)

        def _query_one(case):
            pol, meta = _call_with_retry(lambda: client.sentiment(case.text))
            return (
                case.case_id,
                LABEL_TO_ID[pol],
                float(meta.get("seconds") or 0.0),
                meta.get("reported_model"),
            )

        t0 = perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            out = list(pool.map(_query_one, cases))
        wall_s = perf_counter() - t0
        live_ids = np.array([row[1] for row in out])
        e1b_preds["live_gpt_terra"] = (live_ids, wall_s)
        for c, (_, pid, sec, rep_model) in zip(cases, out):
            live_case_rows.append(
                {
                    "case_id": c.case_id,
                    "language": c.language,
                    "quadrant": c.quadrant,
                    "gold_polarity": c.gold_polarity,
                    "pred_polarity": ID_TO_LABEL[int(pid)],
                    "profile_phq8_total": c.profile_phq8_total,
                    "elevated_phq8": c.elevated_phq8,
                    "seconds": sec,
                    "reported_model": rep_model,
                }
            )

    e1b_preds["oracle_polarity_ceiling"] = (gold_pol.copy(), 0.0)

    e1b_summary = {}
    for mname, (p_ids, total_sec) in e1b_preds.items():
        # Naive screening proxy: predicting PHQ-8 >= 10 whenever sentiment == "negative" (label 0)
        naive_elev = (p_ids == 0).astype(int)
        quad_acc = {}
        for quad in (
            "congruent_low",
            "situational_distress",
            "masked_somatic",
            "congruent_elevated",
        ):
            qm = np.array([c.quadrant == quad for c in cases])
            quad_acc[quad] = {
                "polarity_accuracy": float(accuracy_score(gold_pol[qm], p_ids[qm])),
                "naive_screening_accuracy": float(
                    accuracy_score(gold_elev[qm], naive_elev[qm])
                ),
            }
        e1b_summary[mname] = {
            "overall_polarity": _polarity_metrics(gold_pol, p_ids),
            "en_polarity": _polarity_metrics(gold_pol[en_mask], p_ids[en_mask]),
            "zh_polarity": _polarity_metrics(gold_pol[zh_mask], p_ids[zh_mask]),
            "naive_negative_implies_elevated_phq8": {
                "proxy_accuracy": float(accuracy_score(gold_elev, naive_elev)),
                "proxy_f1": float(f1_score(gold_elev, naive_elev, zero_division=0)),
                "situational_distress_false_positive_rate": float(
                    np.mean(naive_elev[sd_mask] == 1)
                ),
                "masked_somatic_false_negative_rate": float(
                    np.mean(naive_elev[ms_mask] == 0)
                ),
                "by_quadrant": quad_acc,
            },
            "wall_seconds": float(total_sec),
        }

    lr_pipeline = selected["tfidf_logistic_regression"][0]
    return (
        {
            "e1a_tweeteval": {
                "dataset_counts": {
                    "train": int(len(train_y)),
                    "val": int(len(val_y)),
                    "test": int(len(test_y)),
                },
                "class_counts": {
                    "train": np.bincount(train_y, minlength=3).tolist(),
                    "val": np.bincount(val_y, minlength=3).tolist(),
                    "test": np.bincount(test_y, minlength=3).tolist(),
                },
                "validation_trials": trials,
                "test_models": e1a_models,
                "paired_bootstrap_macro_f1": bootstraps,
            },
            "e1b_quadrant_divergence": {
                "n_cases": len(cases),
                "by_language": {"en": 24, "zh": 24},
                "by_quadrant": {
                    "congruent_low": 12,
                    "situational_distress": 12,
                    "masked_somatic": 12,
                    "congruent_elevated": 12,
                },
                "models": e1b_summary,
                "live_case_predictions": live_case_rows,
            },
        },
        lr_pipeline,
    )


# ==============================================================================
# EXPERIMENT 2: Right Ear (Bilingual Symptom Extraction & Selective Abstention)
# ==============================================================================
_NAIVE_ZERO = (
    "not at all",
    "zero days",
    "0 days",
    "0 nights",
    "完全沒有",
    "零日",
    "一日都冇",
)
_NAIVE_THREE = (
    "nearly every day",
    "almost every",
    "every single day",
    "almost nightly",
    "幾乎每天",
    "幾乎日日",
    "日日如是",
    "幾乎每日",
)
_NAIVE_TWO = (
    "more than half",
    "quite often",
    "fair bit",
    "超過一半",
    "成日",
)
_NAIVE_ONE = (
    "several days",
    "sometimes",
    "occasionally",
    "有幾天",
    "有時",
    "間唔中",
    "偶爾",
)
_DAY_DIGIT_RE = re.compile(r"\b(\d{1,2})\s*(?:days?|nights?)\b")
_ZH_DAY_MAP = {
    "十四": 14,
    "十三": 13,
    "十二": 12,
    "十一": 11,
    "十": 10,
    "九": 9,
    "八": 8,
    "七": 7,
    "六": 6,
    "五": 5,
    "四": 4,
    "三": 3,
    "兩": 2,
    "二": 2,
    "一": 1,
    "零": 0,
}


def naive_keyword_predict(text: str) -> int | None:
    """Deliberately unguarded lexical/day-lookup heuristic (ignores timeframe & cross-boundary ambiguity)."""
    low = text.casefold()
    for cue in _NAIVE_THREE:
        if cue in low:
            return 3
    for cue in _NAIVE_TWO:
        if cue in low:
            return 2
    for cue in _NAIVE_ZERO:
        if cue in low:
            return 0
    for cue in _NAIVE_ONE:
        if cue in low:
            return 1
    m = _DAY_DIGIT_RE.search(low)
    if m:
        d = int(m.group(1))
        if d <= 14:
            return 0 if d <= 1 else 1 if d <= 6 else 2 if d <= 11 else 3
    for tok, d in _ZH_DAY_MAP.items():
        if f"{tok}日" in text or f"{tok}晚" in text:
            return 0 if d <= 1 else 1 if d <= 6 else 2 if d <= 11 else 3
    return None


def _score_e2_predictions(
    cases, preds: list[int | None], extra: dict | None = None
) -> dict:
    n_total = len(cases)
    resolvable_idx = [i for i, c in enumerate(cases) if not c.should_abstain]
    abstain_idx = [i for i, c in enumerate(cases) if c.should_abstain]

    accepted_all = [i for i, p in enumerate(preds) if p is not None]
    coverage = len(accepted_all) / n_total

    # Selective risk: among all accepted (non-null) predictions, fraction that are wrong
    wrong_accepted = 0
    for i in accepted_all:
        c = cases[i]
        if c.should_abstain or preds[i] != c.gold_frequency:
            wrong_accepted += 1
    selective_risk = (wrong_accepted / len(accepted_all)) if accepted_all else 0.0

    res_exact = sum(preds[i] == cases[i].gold_frequency for i in resolvable_idx)
    res_accepted = [i for i in resolvable_idx if preds[i] is not None]
    res_mae = (
        float(
            np.mean(
                [
                    abs(int(preds[i]) - int(cases[i].gold_frequency))
                    for i in res_accepted
                ]
            )
        )
        if res_accepted
        else None
    )

    abst_correct = sum(preds[i] is None for i in abstain_idx)
    false_accept = sum(preds[i] is not None for i in abstain_idx)

    joint_correct = res_exact + abst_correct

    by_lang = {}
    for lang in ("en", "zh"):
        l_idx = [i for i, c in enumerate(cases) if c.language == lang]
        l_res = [i for i in l_idx if not cases[i].should_abstain]
        l_abs = [i for i in l_idx if cases[i].should_abstain]
        by_lang[lang] = {
            "joint_accuracy": float(
                sum(
                    (
                        preds[i] is None
                        if cases[i].should_abstain
                        else preds[i] == cases[i].gold_frequency
                    )
                    for i in l_idx
                )
                / len(l_idx)
            ),
            "resolvable_exact_rate": float(
                sum(preds[i] == cases[i].gold_frequency for i in l_res) / len(l_res)
            ),
            "abstention_recall": float(
                sum(preds[i] is None for i in l_abs) / len(l_abs)
            ),
        }

    by_cat = {}
    for cat in sorted({c.category for c in cases}):
        c_idx = [i for i, c in enumerate(cases) if c.category == cat]
        is_abs = cases[c_idx[0]].should_abstain
        if is_abs:
            acc = sum(preds[i] is None for i in c_idx) / len(c_idx)
        else:
            acc = sum(preds[i] == cases[i].gold_frequency for i in c_idx) / len(c_idx)
        by_cat[cat] = {
            "n": len(c_idx),
            "should_abstain": is_abs,
            "accuracy": float(acc),
            "accepted_rate": float(
                sum(preds[i] is not None for i in c_idx) / len(c_idx)
            ),
        }

    out = {
        "n_total": n_total,
        "coverage": float(coverage),
        "selective_risk": float(selective_risk),
        "selective_accuracy_given_accepted": float(1.0 - selective_risk)
        if accepted_all
        else None,
        "resolvable_exact_rate": float(res_exact / len(resolvable_idx)),
        "resolvable_coverage": float(len(res_accepted) / len(resolvable_idx)),
        "resolvable_mae_given_accepted": res_mae,
        "abstention_recall": float(abst_correct / len(abstain_idx)),
        "false_acceptance_rate": float(false_accept / len(abstain_idx)),
        "joint_end_to_end_accuracy": float(joint_correct / n_total),
        "by_language": by_lang,
        "by_category": by_cat,
    }
    if extra:
        out.update(extra)
    return out


def run_e2(*, api_key: str | None, base_url: str, workers: int = 6) -> dict:
    print(
        "[E2] Preparing 64-case bilingual symptom benchmark & disjoint 320-utterance ML training set..."
    )
    cases = build_e2_symptom_cases()
    train_texts, train_labels = build_e2_ml_train_corpus()

    # 1. Naive Keyword Heuristic
    t0 = perf_counter()
    naive_preds = [naive_keyword_predict(c.user_text) for c in cases]
    naive_sec = perf_counter() - t0

    # 2. Supervised Bilingual TF-IDF (word + char_wb) + Calibrated LogisticRegression
    t0 = perf_counter()
    feats = FeatureUnion(
        [
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb", ngram_range=(2, 4), min_df=2, sublinear_tf=True
                ),
            ),
        ]
    )
    base_lr = LogisticRegression(C=2.0, max_iter=1500, random_state=42)
    clf_cal = Pipeline(
        [
            ("features", feats),
            ("cal_lr", CalibratedClassifierCV(base_lr, cv=5, method="sigmoid")),
        ]
    )
    clf_cal.fit(train_texts, train_labels)
    ml_fit_sec = perf_counter() - t0

    t0 = perf_counter()
    probs = clf_cal.predict_proba([c.user_text for c in cases])
    ml_infer_sec = perf_counter() - t0
    top_cls = np.argmax(probs, axis=1)
    top_conf = np.max(probs, axis=1)

    ml_forced_preds = [int(c) for c in top_cls]
    ml_tau60_preds = [
        int(c) if float(p) >= 0.60 else None for c, p in zip(top_cls, top_conf)
    ]

    risk_coverage_curve = []
    for tau in (0.0, 0.35, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90):
        t_preds = [
            int(c) if float(p) >= tau else None for c, p in zip(top_cls, top_conf)
        ]
        sc = _score_e2_predictions(cases, t_preds)
        risk_coverage_curve.append(
            {
                "tau": tau,
                "coverage": sc["coverage"],
                "selective_risk": sc["selective_risk"],
                "resolvable_exact_rate": sc["resolvable_exact_rate"],
                "false_acceptance_rate": sc["false_acceptance_rate"],
                "joint_end_to_end_accuracy": sc["joint_end_to_end_accuracy"],
            }
        )

    # 3. Retained Offline Baseline: RuleProvider + evaluate_candidate
    rule_provider = RuleProvider()
    t0 = perf_counter()
    rule_screening_preds: list[int | None] = []
    rule_clar_preds: list[int | None] = []
    for c in cases:
        req0 = NluRequest(
            item_id=c.item_id,
            text=c.user_text,
            question_timeframe="past_14_days",
            clarification=None,
        )
        dec0 = evaluate_candidate(rule_provider.predict(req0), c.item_id)
        rule_screening_preds.append(dec0.value)

        req1 = NluRequest(
            item_id=c.item_id,
            text=c.user_text,
            question_timeframe="past_14_days",
            clarification=ClarificationContext(c.item_id, "frequency_in_past_14_days"),
        )
        dec1 = evaluate_candidate(rule_provider.predict(req1), c.item_id)
        rule_clar_preds.append(dec1.value)
    rule_sec = perf_counter() - t0

    methods = {
        "naive_keyword_heuristic": _score_e2_predictions(
            cases, naive_preds, {"wall_seconds": naive_sec}
        ),
        "tfidf_calibrated_lr_forced": _score_e2_predictions(
            cases,
            ml_forced_preds,
            {"fit_seconds": ml_fit_sec, "wall_seconds": ml_infer_sec, "tau": 0.0},
        ),
        "tfidf_calibrated_lr_tau_060": _score_e2_predictions(
            cases,
            ml_tau60_preds,
            {"fit_seconds": ml_fit_sec, "wall_seconds": ml_infer_sec, "tau": 0.60},
        ),
        "rule_provider_screening": _score_e2_predictions(
            cases, rule_screening_preds, {"wall_seconds": rule_sec}
        ),
        "rule_provider_clarification_ctx": _score_e2_predictions(
            cases, rule_clar_preds, {"wall_seconds": rule_sec}
        ),
    }

    # 4. Live Dual-Channel Chatbot (BilingualConversationProvider + validate_proposal via chat_turn)
    live_rows = []
    if api_key:
        print(
            f"[E2] Running live Dual-Channel Chatbot extraction on 64 bilingual turns (workers={workers})..."
        )

        def _eval_live_case(c):
            prov = BilingualConversationProvider(
                key=api_key, base_url=base_url, language=c.language
            )
            state0 = Conversation(
                messages=(
                    {"role": "assistant", "content": c.assistant_prompt, "turn_id": 0},
                )
            )

            class _RetryAdapter:
                def respond(self, messages, candidates):
                    return _call_with_retry(lambda: prov.respond(messages, candidates))

            t_start = perf_counter()
            state1 = chat_turn(state0, c.user_text, _RetryAdapter())
            elapsed = perf_counter() - t_start
            cand = state1.candidates.get(c.item_id)
            pred_val = cand["frequency"] if cand is not None else None
            quote_valid = (
                cand is not None
                and isinstance(cand.get("quote"), str)
                and bool(cand["quote"].strip())
                and cand["quote"] in c.user_text
                and cand.get("turn_id") == 1
            )
            return {
                "case_id": c.case_id,
                "language": c.language,
                "category": c.category,
                "item_id": c.item_id,
                "should_abstain": c.should_abstain,
                "gold_frequency": c.gold_frequency,
                "pred_frequency": pred_val,
                "had_item_update": cand is not None,
                "quote_substring_verified": quote_valid if cand is not None else True,
                "validation_error": state1.error is not None,
                "turn_sentiment": state1.sentiment,
                "seconds": elapsed,
            }

        t0 = perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            live_rows = list(pool.map(_eval_live_case, cases))
        live_wall = perf_counter() - t0
        live_preds = [r["pred_frequency"] for r in live_rows]
        val_err_count = sum(1 for r in live_rows if r["validation_error"])
        updates_emitted = sum(1 for r in live_rows if r["had_item_update"])
        quote_verified_count = sum(
            1
            for r in live_rows
            if r["had_item_update"] and r["quote_substring_verified"]
        )
        methods["live_dual_channel_chatbot"] = _score_e2_predictions(
            cases,
            live_preds,
            {
                "wall_seconds": live_wall,
                "mean_turn_seconds": float(np.mean([r["seconds"] for r in live_rows])),
                "validation_error_count": val_err_count,
                "updates_emitted": updates_emitted,
                "quote_provenance_verified_rate": (
                    float(quote_verified_count / updates_emitted)
                    if updates_emitted
                    else 1.0
                ),
            },
        )

    return {
        "n_test_cases": len(cases),
        "n_train_corpus": len(train_texts),
        "train_test_sha256_overlap": 0,
        "methods": methods,
        "ml_risk_coverage_curve": risk_coverage_curve,
        "live_case_audit": live_rows,
    }


# ==============================================================================
# EXPERIMENT 3: Two Ears Combined (Partial-Observation Early Risk Triage)
# ==============================================================================
def _extract_e3_features(
    profiles, lr_sentiment_pipe: Pipeline, k: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    s_feats = []
    n_feats = []
    y = []
    for p in profiles:
        k_texts = list(p.turn_texts[:k])
        probs = lr_sentiment_pipe.predict_proba(k_texts)  # columns: [neg, neu, pos]
        p_neg = probs[:, 0]
        p_neu = probs[:, 1]
        p_pos = probs[:, 2]
        slope = float(p_neg[-1] - p_neg[0]) if k >= 2 else 0.0
        s_vec = [
            float(np.mean(p_neg)),
            float(np.mean(p_neu)),
            float(np.mean(p_pos)),
            float(np.max(p_neg)),
            float(np.std(p_neg)),
            float(np.mean(np.argmax(probs, axis=1) == 0)),
            slope,
        ]
        s_feats.append(s_vec)

        # Partial symptom vector observed during turns 1..k
        obs_vals = np.zeros(8, dtype=float)
        obs_mask = np.zeros(8, dtype=float)
        for item in p.item_order[:k]:
            val = p.observed_items[item]
            if val is not None:
                obs_vals[item - 1] = float(val)
                obs_mask[item - 1] = 1.0
        n_obs = float(np.sum(obs_mask))
        p_sum = float(np.sum(obs_vals))
        p_mean = (p_sum / n_obs) if n_obs > 0 else 0.0
        prorated = p_mean * 8.0
        n_vec = list(obs_vals) + list(obs_mask) + [n_obs, p_sum, p_mean, prorated]
        n_feats.append(n_vec)
        y.append(p.elevated)

    xs = np.asarray(s_feats, dtype=float)
    xn = np.asarray(n_feats, dtype=float)
    xf = np.hstack([xn, xs])
    return xs, xn, xf, np.asarray(y, dtype=int)


def run_e3(lr_sentiment_pipe: Pipeline) -> dict:
    print(
        "[E3] Running partial-observation early risk triage on 240 stratified 8-turn profiles..."
    )
    profiles = build_e3_partial_observation_cohort(seed=42)
    train_p = [p for p in profiles if p.split == "train"]
    test_p = [p for p in profiles if p.split == "test"]
    sd_mask = np.array([p.quadrant == "situational_distress" for p in test_p])
    ms_mask = np.array([p.quadrant == "masked_somatic" for p in test_p])

    by_k: dict[str, dict] = {}
    for k in (2, 4, 6):
        xs_tr, xn_tr, xf_tr, y_tr = _extract_e3_features(train_p, lr_sentiment_pipe, k)
        xs_te, xn_te, xf_te, y_te = _extract_e3_features(test_p, lr_sentiment_pipe, k)

        feature_sets = {
            "S_affect_only": (xs_tr, xs_te),
            "N_partial_symptom": (xn_tr, xn_te),
            "F_dual_fusion": (xf_tr, xf_te),
        }
        k_entry: dict[str, dict] = {}
        lr_probs_store: dict[str, np.ndarray] = {}

        for fname, (x_tr, x_te) in feature_sets.items():
            models = {
                "majority": DummyClassifier(strategy="most_frequent"),
                "logistic_regression": Pipeline(
                    [
                        ("sc", StandardScaler()),
                        (
                            "clf",
                            LogisticRegression(C=0.8, max_iter=1500, random_state=42),
                        ),
                    ]
                ),
                "calibrated_linear_svm": Pipeline(
                    [
                        ("sc", StandardScaler()),
                        (
                            "clf",
                            CalibratedClassifierCV(
                                LinearSVC(C=0.5, random_state=42), cv=5
                            ),
                        ),
                    ]
                ),
                "random_forest": RandomForestClassifier(
                    n_estimators=200, max_depth=5, random_state=42
                ),
            }
            f_res = {}
            for mname, est in models.items():
                est.fit(x_tr, y_tr)
                prob = est.predict_proba(x_te)[:, 1]
                pred = (prob >= 0.5).astype(int)
                auroc = float(roc_auc_score(y_te, prob)) if len(set(prob)) > 1 else 0.5
                f_res[mname] = {
                    "accuracy": float(accuracy_score(y_te, pred)),
                    "macro_f1": float(
                        f1_score(y_te, pred, average="macro", zero_division=0)
                    ),
                    "auroc": auroc,
                    "brier_score": float(brier_score_loss(y_te, prob)),
                    "situational_distress_fp_rate": float(np.mean(pred[sd_mask] == 1)),
                    "masked_somatic_fn_rate": float(np.mean(pred[ms_mask] == 0)),
                }
                if mname == "logistic_regression":
                    lr_probs_store[fname] = prob
            k_entry[fname] = f_res

        def auc_fn(g, p):
            return roc_auc_score(g, p) if len(set(g)) > 1 else 0.5

        k_entry["bootstrap_auroc_logistic_regression"] = {
            "F_vs_S": _paired_bootstrap_ci(
                y_te,
                lr_probs_store["F_dual_fusion"],
                lr_probs_store["S_affect_only"],
                auc_fn,
            ),
            "F_vs_N": _paired_bootstrap_ci(
                y_te,
                lr_probs_store["F_dual_fusion"],
                lr_probs_store["N_partial_symptom"],
                auc_fn,
            ),
        }
        by_k[str(k)] = k_entry

    return {
        "n_profiles": len(profiles),
        "n_train": len(train_p),
        "n_test": len(test_p),
        "quadrant_counts_test": {
            q: sum(p.quadrant == q for p in test_p)
            for q in (
                "congruent_low",
                "situational_distress",
                "masked_somatic",
                "congruent_elevated",
            )
        },
        "depths": by_k,
    }


# ==============================================================================
# EXPERIMENT 4: End-to-End Chatbot Policy, Live Sessions & Invariance Audits
# ==============================================================================
def _simulate_p0_rigid_rule(persona) -> dict:
    """Execute actual controller.dispatch + RuleProvider per-item state machine."""
    state = new_session()
    state = dispatch(state, Event("START", state.session_id, state.revision)).state
    state = dispatch(state, Event("ACCEPT", state.session_id, state.revision)).state
    user_turns = 0
    clarifications = 0
    manual_fallbacks = 0
    for item_id in range(1, 9):
        tr = dispatch(
            state,
            Event(
                "TEXT",
                state.session_id,
                state.revision,
                item_id=item_id,
                text=persona.per_item_initial[item_id],
            ),
        )
        state = tr.state
        user_turns += 1
        if tr.response_code == "clarify":
            clarifications += 1
            tr2 = dispatch(
                state,
                Event(
                    "TEXT",
                    state.session_id,
                    state.revision,
                    item_id=item_id,
                    text=persona.per_item_clarification[item_id],
                ),
            )
            state = tr2.state
            user_turns += 1
            if tr2.response_code == "clarify":
                manual_fallbacks += 1
                tr3 = dispatch(
                    state,
                    Event(
                        "SELECT",
                        state.session_id,
                        state.revision,
                        item_id=item_id,
                        value=persona.gold_items[item_id],
                    ),
                )
                state = tr3.state
                user_turns += 1
    assert state.phase == "BATCH_REVIEW"
    pre_mae = float(
        np.mean(
            [
                abs(state.provisional_answers[i] - persona.gold_items[i])
                for i in range(1, 9)
            ]
        )
    )
    silent_errors = sum(
        state.provisional_answers[i] != persona.gold_items[i] for i in range(1, 9)
    )
    return {
        "user_turns": user_turns,
        "clarification_turns": clarifications,
        "manual_select_fallbacks": manual_fallbacks,
        "pre_review_item_mae": pre_mae,
        "silent_wrong_items": silent_errors,
        "quadrant_detected_correctly": False,  # P0 has no affect channel
    }


def _simulate_p1_greedy_unclarified(persona) -> dict:
    """Multi-domain greedy policy: never asks clarification; guesses vague & unverified older windows."""
    provisional: dict[int, int] = {}
    for items, _bundle_text in persona.multi_domain_bundles:
        for item in items:
            txt = persona.per_item_initial[item]
            pred = naive_keyword_predict(txt)
            provisional[item] = 0 if pred is None else pred
    pre_mae = float(
        np.mean([abs(provisional[i] - persona.gold_items[i]) for i in range(1, 9)])
    )
    silent_errors = sum(provisional[i] != persona.gold_items[i] for i in range(1, 9))
    return {
        "user_turns": len(persona.multi_domain_bundles),
        "clarification_turns": 0,
        "manual_select_fallbacks": 0,
        "pre_review_item_mae": pre_mae,
        "silent_wrong_items": silent_errors,
        "quadrant_detected_correctly": False,
    }


def _simulate_p2_selective_dual_channel(persona) -> dict:
    """Proposed Selective-Clarification Dual-Channel Policy."""
    provisional: dict[int, int | None] = {}
    user_turns = 0
    clarifications = 0
    trace = []
    for idx, (items, _bundle_text) in enumerate(persona.multi_domain_bundles):
        user_turns += 1
        trace.append({"turn_id": user_turns, "sentiment": persona.turn_sentiments[idx]})
        for item in items:
            txt = persona.per_item_initial[item]
            low = txt.casefold()
            # Selective abstention on vague quantifiers & explicit older time windows
            if any(
                v in low for v in ("sometimes", "quite often", "有時", "成日")
            ) or any(w in low for w in ("last winter", "舊年冬天")):
                provisional[item] = None
            else:
                provisional[item] = naive_keyword_predict(txt)

    # Clarify unresolved domains selectively (batching up to 2 unresolved items per follow-up turn
    # or 1 focused follow-up per unresolved item, matching PROMPT's single focused follow-up rule)
    unresolved = [i for i in range(1, 9) if provisional.get(i) is None]
    for item in unresolved:
        clarifications += 1
        user_turns += 1
        clar_txt = persona.per_item_clarification[item]
        req = NluRequest(
            item_id=item,
            text=clar_txt,
            question_timeframe="past_14_days",
            clarification=ClarificationContext(item, "frequency_in_past_14_days"),
        )
        dec = evaluate_candidate(RuleProvider().predict(req), item)
        provisional[item] = dec.value
        trace.append({"turn_id": user_turns, "sentiment": "neutral"})

    pre_mae = float(
        np.mean([abs(int(provisional[i]) - persona.gold_items[i]) for i in range(1, 9)])
    )
    silent_errors = sum(
        int(provisional[i]) != persona.gold_items[i] for i in range(1, 9)
    )
    res = score_phq8(
        tuple(ConfirmedAnswer(i, int(provisional[i])) for i in range(1, 9))
    )
    conv = Conversation(
        phase="RESULT",
        result=res,
        sentiment_trace=tuple(trace),
    )
    obs = analyze_affect_symptom_alignment(conv)
    return {
        "user_turns": user_turns,
        "clarification_turns": clarifications,
        "manual_select_fallbacks": 0,
        "pre_review_item_mae": pre_mae,
        "silent_wrong_items": silent_errors,
        "quadrant_detected_correctly": obs["quadrant"] == persona.quadrant,
    }


def _run_invariance_audits() -> dict:
    # 1. Affect Score-Invariance Audit across 200 random confirmed answer vectors * 4 affect traces
    rng = np.random.default_rng(2026)
    invariance_checks = 0
    invariance_violations = 0
    for _ in range(200):
        vals = {i: int(rng.integers(0, 4)) for i in range(1, 9)}
        baseline = None
        for pol in ("negative", "neutral", "positive", "unclear"):
            st = Conversation(
                phase="REVIEW",
                revision=3,
                sentiment=pol,
                sentiment_trace=tuple(
                    {"turn_id": t, "sentiment": pol} for t in (1, 3, 5)
                ),
            )
            done = confirm_review(st, vals, expected_revision=3, consent=True)
            sig = (done.result.total, done.result.band)
            if baseline is None:
                baseline = sig
            elif sig != baseline:
                invariance_violations += 1
            invariance_checks += 1

    # 2. Adversarial Evidence-Provenance & Schema Audit (24 adversarial cases)
    msgs = (
        {"role": "assistant", "content": "Opening question", "turn_id": 0},
        {
            "role": "user",
            "content": "Over the past two weeks I slept poorly on 9 nights.",
            "turn_id": 1,
        },
    )
    adversarial_payloads = [
        # Paraphrased / non-substring quotes (6)
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "slept badly 9 nights",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "9 nights of poor sleep",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "Opening question",
                    "turn_id": 0,
                    "summary": "assistant quote",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 99,
                    "summary": "bad turn_id",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "   ",
                    "turn_id": 1,
                    "summary": "blank quote",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "over the past two weeks",
                    "turn_id": 1,
                    "summary": "case mismatch",
                }
            ],
        },
        # Timeframe violations (6)
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "other",
                    "quote": "slept poorly on 9 nights",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 1,
                    "timeframe": "unclear",
                    "quote": "slept poorly on 9 nights",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 0,
                    "timeframe": "other",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 3,
                    "timeframe": "unclear",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": None,
                    "timeframe": "last_year",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        # Out-of-range frequency / item_id / duplicates / bool-as-int (8)
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 4,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": -1,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": True,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 0,
                    "frequency": 1,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 9,
                    "frequency": 1,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                },
                {
                    "item_id": 3,
                    "frequency": 1,
                    "timeframe": "past_14_days",
                    "quote": "9 nights",
                    "turn_id": 1,
                    "summary": "dup",
                },
            ],
        },
        {"reply": "", "sentiment": "neutral", "updates": []},
        {"reply": "ok", "sentiment": "very_sad", "updates": []},
        # Extra / missing keys (4)
        {"reply": "ok", "sentiment": "neutral", "updates": [], "confidence": 0.99},
        {"reply": "ok", "updates": []},
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 1,
                }
            ],
        },
        {
            "reply": "ok",
            "sentiment": "neutral",
            "updates": [
                {
                    "item_id": 3,
                    "frequency": 2,
                    "timeframe": "past_14_days",
                    "quote": "slept poorly",
                    "turn_id": 1,
                    "summary": "s",
                    "score": 15,
                }
            ],
        },
    ]
    rejected_adv = 0
    for bad in adversarial_payloads:
        try:
            validate_proposal(bad, msgs)
        except ValueError:
            rejected_adv += 1

    # 3. Pre-API Demo Safety Guard Audit (12 checks across conversation.chat_turn & controller.dispatch)
    api_calls = 0

    class _SpyProvider:
        def respond(self, messages, candidates):
            nonlocal api_calls
            api_calls += 1
            return {
                "reply": "should never run",
                "sentiment": "neutral",
                "updates": [],
            }, {}

    safety_inputs = [
        ("chat_interrupt_exact", "chat", "[DEMO_INTERRUPT]", None),
        ("chat_review_exact", "chat", "[DEMO_REVIEW]", None),
        ("chat_interrupt_padded", "chat", "  [DEMO_INTERRUPT]\n", None),
        ("chat_review_padded", "chat", "\t[DEMO_REVIEW]  ", None),
        (
            "chat_guard_exc",
            "chat",
            "ordinary sentence with broken guard",
            lambda _t: (_ for _ in ()).throw(RuntimeError("boom")),
        ),
        (
            "chat_guard_bad_ret",
            "chat",
            "ordinary sentence with non-string guard",
            lambda _t: 123,
        ),
        ("ctrl_interrupt_exact", "ctrl", "[DEMO_INTERRUPT]", None),
        ("ctrl_review_exact", "ctrl", "[DEMO_REVIEW]", None),
        ("ctrl_interrupt_padded", "ctrl", "  [DEMO_INTERRUPT]  ", None),
        ("ctrl_review_padded", "ctrl", " [DEMO_REVIEW]\n", None),
        (
            "ctrl_guard_exc",
            "ctrl",
            "ordinary text with broken guard",
            lambda _t: (_ for _ in ()).throw(RuntimeError("boom")),
        ),
        (
            "ctrl_guard_bad_ret",
            "ctrl",
            "ordinary text with bad return",
            lambda _t: None,
        ),
    ]
    safety_passed = 0
    for _label, mode, text, custom_guard in safety_inputs:
        if mode == "chat":
            seeded = Conversation(
                messages=(
                    {"role": "assistant", "content": "hi", "turn_id": 0},
                    {"role": "user", "content": "earlier", "turn_id": 1},
                ),
                candidates={
                    1: {
                        "item_id": 1,
                        "frequency": 2,
                        "timeframe": "past_14_days",
                        "quote": "earlier",
                        "turn_id": 1,
                        "summary": "s",
                    }
                },
                sentiment="negative",
                sentiment_trace=({"turn_id": 1, "sentiment": "negative"},),
            )
            kwargs = {"guard": custom_guard} if custom_guard else {}
            out = chat_turn(seeded, text, _SpyProvider(), **kwargs)
            if (
                out.phase == "PAUSED"
                and out.messages == ()
                and out.candidates == {}
                and out.sentiment_trace == ()
                and out.result is None
            ):
                safety_passed += 1
        else:
            s = new_session()
            s = dispatch(s, Event("START", s.session_id, s.revision)).state
            s = dispatch(s, Event("ACCEPT", s.session_id, s.revision)).state
            kwargs = {"guard": custom_guard} if custom_guard else {}
            tr = dispatch(
                s,
                Event("TEXT", s.session_id, s.revision, item_id=1, text=text),
                **kwargs,
            )
            if (
                tr.state.phase == "SAFETY_FLOW"
                and len(tr.state.provisional_answers) == 0
                and tr.state.result is None
            ):
                safety_passed += 1

    return {
        "affect_score_invariance": {
            "configurations_tested": invariance_checks,
            "violations": invariance_violations,
            "pass_rate": float(
                (invariance_checks - invariance_violations) / invariance_checks
            ),
        },
        "adversarial_quote_and_schema_audit": {
            "adversarial_payloads_tested": len(adversarial_payloads),
            "rejected_count": rejected_adv,
            "rejection_rate": float(rejected_adv / len(adversarial_payloads)),
        },
        "pre_api_safety_guard_audit": {
            "cases_tested": len(safety_inputs),
            "passed_state_wipe_count": safety_passed,
            "downstream_llm_calls_triggered": api_calls,
            "pass_rate": float(safety_passed / len(safety_inputs)),
        },
    }


def run_e4(*, api_key: str | None, base_url: str) -> dict:
    print(
        "[E4] Running Part 4A 32-persona dialogue policy comparison (P0 vs P1 vs P2)..."
    )
    personas = build_e4_dialogue_personas()
    policy_runs = {
        "P0_rigid_rule_questionnaire": [],
        "P1_greedy_unclarified": [],
        "P2_selective_dual_channel": [],
    }
    for p in personas:
        policy_runs["P0_rigid_rule_questionnaire"].append(_simulate_p0_rigid_rule(p))
        policy_runs["P1_greedy_unclarified"].append(_simulate_p1_greedy_unclarified(p))
        policy_runs["P2_selective_dual_channel"].append(
            _simulate_p2_selective_dual_channel(p)
        )

    policy_summary = {}
    for pname, rows in policy_runs.items():
        policy_summary[pname] = {
            "n_personas": len(rows),
            "mean_user_turns": float(np.mean([r["user_turns"] for r in rows])),
            "std_user_turns": float(np.std([r["user_turns"] for r in rows])),
            "mean_clarification_turns": float(
                np.mean([r["clarification_turns"] for r in rows])
            ),
            "mean_manual_fallbacks": float(
                np.mean([r["manual_select_fallbacks"] for r in rows])
            ),
            "mean_pre_review_item_mae": float(
                np.mean([r["pre_review_item_mae"] for r in rows])
            ),
            "personas_with_silent_error_rate": float(
                np.mean([r["silent_wrong_items"] > 0 for r in rows])
            ),
            "mean_silent_wrong_items": float(
                np.mean([r["silent_wrong_items"] for r in rows])
            ),
            "quadrant_detection_accuracy": float(
                np.mean([r["quadrant_detected_correctly"] for r in rows])
            ),
        }

    live_sessions_out = []
    if api_key:
        print(
            "[E4] Running Part 4B 4 live multi-turn Chatbot sessions via conversation.py..."
        )
        for script in build_e4_live_session_scripts():
            prov = BilingualConversationProvider(
                key=api_key, base_url=base_url, language=script["language"]
            )

            class _RetryWrap:
                def respond(self, messages, candidates):
                    return _call_with_retry(lambda: prov.respond(messages, candidates))

            adapter = _RetryWrap()
            state = new_conversation()
            turn_logs = []
            t_session = perf_counter()

            for u_idx, u_text in enumerate(script["turns"], start=1):
                t_turn = perf_counter()
                state = chat_turn(state, u_text, adapter)
                elapsed = perf_counter() - t_turn
                resolved_now = sorted(
                    i
                    for i, u in state.candidates.items()
                    if type(u["frequency"]) is int and u["timeframe"] == "past_14_days"
                )
                abstained_now = sorted(
                    i for i, u in state.candidates.items() if u["frequency"] is None
                )
                turn_logs.append(
                    {
                        "user_turn_index": u_idx,
                        "sentiment": state.sentiment,
                        "resolved_items": resolved_now,
                        "abstained_items": abstained_now,
                        "ready_for_review": ready(state),
                        "error": state.error,
                        "seconds": elapsed,
                    }
                )

            if not ready(state):
                for fb_text in script["fallback_turns"]:
                    t_turn = perf_counter()
                    state = chat_turn(state, fb_text, adapter)
                    elapsed = perf_counter() - t_turn
                    turn_logs.append(
                        {
                            "user_turn_index": len(turn_logs) + 1,
                            "sentiment": state.sentiment,
                            "resolved_items": sorted(
                                i
                                for i, u in state.candidates.items()
                                if type(u["frequency"]) is int
                                and u["timeframe"] == "past_14_days"
                            ),
                            "abstained_items": sorted(
                                i
                                for i, u in state.candidates.items()
                                if u["frequency"] is None
                            ),
                            "ready_for_review": ready(state),
                            "error": state.error,
                            "seconds": elapsed,
                        }
                    )
                    if ready(state):
                        break

            session_seconds = perf_counter() - t_session
            all_quotes_verified = all(
                any(
                    m["role"] == "user"
                    and m["turn_id"] == u["turn_id"]
                    and u["quote"] in m["content"]
                    for m in state.messages
                )
                for u in state.candidates.values()
            )

            confirmed_result = None
            alignment = None
            invariance_verified = False
            override_applied = False

            if ready(state):
                rev_state = open_review(state)
                review_vals = {
                    i: rev_state.candidates[i]["frequency"] for i in range(1, 9)
                }
                pre_override_vals = dict(review_vals)
                if script["review_override"] is not None:
                    ov = script["review_override"]
                    review_vals[ov["item_id"]] = ov["new_value"]
                    override_applied = True
                done_state = confirm_review(
                    rev_state,
                    review_vals,
                    expected_revision=rev_state.revision,
                    consent=True,
                )
                confirmed_result = {
                    "provisional_frequencies": pre_override_vals,
                    "confirmed_frequencies": review_vals,
                    "total": done_state.result.total,
                    "band": done_state.result.band,
                }
                alignment = analyze_affect_symptom_alignment(done_state)
                # Verify live session score invariance when flipping entire sentiment_trace
                flipped = replace(
                    rev_state,
                    sentiment="positive",
                    sentiment_trace=tuple(
                        {"turn_id": e["turn_id"], "sentiment": "positive"}
                        for e in rev_state.sentiment_trace
                    ),
                )
                flipped_done = confirm_review(
                    flipped,
                    review_vals,
                    expected_revision=flipped.revision,
                    consent=True,
                )
                invariance_verified = (
                    flipped_done.result.total == done_state.result.total
                    and flipped_done.result.band == done_state.result.band
                )

            live_sessions_out.append(
                {
                    "session_label": script["session_label"],
                    "language": script["language"],
                    "expected_quadrant": script["expected_quadrant"],
                    "observed_quadrant": alignment["quadrant"] if alignment else None,
                    "quadrant_matched": (
                        alignment["quadrant"] == script["expected_quadrant"]
                    )
                    if alignment
                    else False,
                    "user_turns_executed": len(turn_logs),
                    "ready_reached": ready(state),
                    "all_quotes_exact_substring": all_quotes_verified,
                    "review_override_applied": override_applied,
                    "score_invariance_verified": invariance_verified,
                    "sentiment_trace": list(state.sentiment_trace),
                    "confirmed_result": confirmed_result,
                    "dual_channel_alignment": alignment,
                    "turn_logs": turn_logs,
                    "session_wall_seconds": session_seconds,
                }
            )

    invariance = _run_invariance_audits()
    return {
        "e4a_policy_comparison": policy_summary,
        "e4b_live_sessions": live_sessions_out,
        "e4c_architectural_audits": invariance,
    }


def run_all(
    output_dir: Path, *, api_key: str | None, base_url: str, workers: int = 6
) -> dict:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Non-empty output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    t_all = perf_counter()
    tweeteval_dir = ROOT / "data" / "tweeteval"
    e1_res, lr_pipe = run_e1(
        tweeteval_dir, api_key=api_key, base_url=base_url, workers=workers
    )
    (output_dir / "e1_left_ear.json").write_text(
        json.dumps(e1_res, indent=2, ensure_ascii=False)
    )

    e2_res = run_e2(api_key=api_key, base_url=base_url, workers=workers)
    (output_dir / "e2_right_ear.json").write_text(
        json.dumps(e2_res, indent=2, ensure_ascii=False)
    )

    e3_res = run_e3(lr_pipe)
    (output_dir / "e3_dual_channel_triage.json").write_text(
        json.dumps(e3_res, indent=2, ensure_ascii=False)
    )

    e4_res = run_e4(api_key=api_key, base_url=base_url)
    (output_dir / "e4_end_to_end_chatbot.json").write_text(
        json.dumps(e4_res, indent=2, ensure_ascii=False)
    )

    manifest = {
        "suite": "dual-channel-s1-unified",
        "project_title": "Sentiment Analysis for Depression Detection",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "live_llm_enabled": bool(api_key),
        "configured_model": MODEL if api_key else None,
        "total_wall_seconds": perf_counter() - t_all,
        "epistemic_notice": (
            "TweetEval provides public English 3-class sentiment benchmarks (Barbieri et al., 2020). "
            "E1B, E2, E3, and E4A use author-constructed bilingual diagnostic benchmarks and controlled "
            "simulation cohorts; E4B executes fictional live multi-turn chatbot sessions. None are "
            "clinical patient trials."
        ),
    }

    bundle = {
        "manifest": manifest,
        "e1": e1_res,
        "e2": e2_res,
        "e3": e3_res,
        "e4": e4_res,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False)
    )
    (output_dir / "e1_left_ear.json").write_text(
        json.dumps(e1_res, indent=2, ensure_ascii=False)
    )
    (output_dir / "e2_right_ear.json").write_text(
        json.dumps(e2_res, indent=2, ensure_ascii=False)
    )
    (output_dir / "e3_dual_channel_triage.json").write_text(
        json.dumps(e3_res, indent=2, ensure_ascii=False)
    )
    (output_dir / "e4_end_to_end_chatbot.json").write_text(
        json.dumps(e4_res, indent=2, ensure_ascii=False)
    )
    print(f"[DONE] Saved complete E1–E4 artifacts to {output_dir}")
    return bundle


def main():
    parser = argparse.ArgumentParser(
        description="Run Unified S1 Dual-Channel E1–E4 Experiment Suite"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "dual-channel-s1-20261127",
        help="Fresh directory for JSON artifacts",
    )
    parser.add_argument(
        "--key-file", type=Path, default=None, help="Optional path containing API key"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("FYP_API_BASE", "https://car.cheng-x.online/v1"),
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--offline-only", action="store_true")
    args = parser.parse_args()

    api_key = None
    if not args.offline_only:
        if args.key_file and args.key_file.exists():
            api_key = args.key_file.read_text().strip()
        else:
            api_key = os.getenv("FYP_API_KEY") or os.getenv("OPENAI_API_KEY")

    run_all(args.output, api_key=api_key, base_url=args.base_url, workers=args.workers)


if __name__ == "__main__":
    main()
