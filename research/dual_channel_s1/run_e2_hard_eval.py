"""Run the 16 HK code-switched & boundary-trap stress cases and assemble the streamlined S1 v2 bundle.

Preserves ``results/dual-channel-s1-20261127/`` untouched and writes the focused 3-experiment
summary (E1 Sentiment & Divergence, E2 80-case Symptom Extraction + Error Analysis, E3 Live
Walkthroughs & Safety Checks) to ``results/dual-channel-s1-v2-20261127/``.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bilingual_provider import BilingualConversationProvider  # noqa: E402
from conversation import Conversation, chat_turn  # noqa: E402
from evidence_manager import evaluate_candidate  # noqa: E402
from nlu_provider import ClarificationContext, NluRequest, RuleProvider  # noqa: E402
from research.dual_channel_s1.benchmarks import (  # noqa: E402
    build_e2_hard_challenge_cases,
    build_e2_ml_train_corpus,
    build_e2_symptom_cases,
)
from research.dual_channel_s1.run_experiments import (  # noqa: E402
    _call_with_retry,
    _score_e2_predictions,
    naive_keyword_predict,
)


def run_v2_bundle(
    prev_summary_path: Path,
    out_dir: Path,
    *,
    api_key: str,
    base_url: str,
    workers: int = 6,
) -> dict:
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError(f"Non-empty output directory exists: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    prev = json.loads(prev_summary_path.read_text(encoding="utf-8"))
    core_cases = build_e2_symptom_cases()
    hard_cases = build_e2_hard_challenge_cases()
    all_cases = core_cases + hard_cases
    train_texts, train_labels = build_e2_ml_train_corpus()

    # 1. Fit classical ML pipeline on disjoint 320-utterance corpus
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
    clf_cal = Pipeline(
        [
            ("features", feats),
            (
                "cal_lr",
                CalibratedClassifierCV(
                    LogisticRegression(C=2.0, max_iter=1500, random_state=42),
                    cv=5,
                    method="sigmoid",
                ),
            ),
        ]
    )
    clf_cal.fit(train_texts, train_labels)
    ml_fit_sec = perf_counter() - t0

    probs_all = clf_cal.predict_proba([c.user_text for c in all_cases])
    top_cls = np.argmax(probs_all, axis=1)
    top_conf = np.max(probs_all, axis=1)

    naive_all = [naive_keyword_predict(c.user_text) for c in all_cases]
    ml_forced_all = [int(c) for c in top_cls]
    ml_tau60_all = [
        int(c) if float(p) >= 0.60 else None for c, p in zip(top_cls, top_conf)
    ]

    rule_prov = RuleProvider()
    rule_screen_all = []
    rule_clar_all = []
    for c in all_cases:
        d0 = evaluate_candidate(
            rule_prov.predict(NluRequest(c.item_id, c.user_text, "past_14_days", None)),
            c.item_id,
        )
        rule_screen_all.append(d0.value)
        d1 = evaluate_candidate(
            rule_prov.predict(
                NluRequest(
                    c.item_id,
                    c.user_text,
                    "past_14_days",
                    ClarificationContext(c.item_id, "frequency_in_past_14_days"),
                )
            ),
            c.item_id,
        )
        rule_clar_all.append(d1.value)

    risk_curve = []
    for tau in (0.0, 0.35, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90):
        t_preds = [
            int(c) if float(p) >= tau else None for c, p in zip(top_cls, top_conf)
        ]
        sc = _score_e2_predictions(all_cases, t_preds)
        risk_curve.append(
            {
                "tau": tau,
                "coverage": sc["coverage"],
                "selective_risk": sc["selective_risk"],
                "resolvable_exact_rate": sc["resolvable_exact_rate"],
                "false_acceptance_rate": sc["false_acceptance_rate"],
                "joint_end_to_end_accuracy": sc["joint_end_to_end_accuracy"],
            }
        )

    # 2. Query live gpt-6.1-terra on the 16 hard HK code-switched / trap cases
    print(
        f"[E2-Hard] Running 16 realistic HK/colloquial stress cases on live Chatbot (workers={workers})..."
    )

    def _eval_hard(c):
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
            "user_text": c.user_text,
            "should_abstain": c.should_abstain,
            "gold_frequency": c.gold_frequency,
            "pred_frequency": pred_val,
            "quote": cand.get("quote") if cand else None,
            "timeframe": cand.get("timeframe") if cand else None,
            "summary": cand.get("summary") if cand else None,
            "assistant_reply": state1.messages[-1]["content"]
            if state1.messages
            else "",
            "had_item_update": cand is not None,
            "quote_substring_verified": quote_valid if cand is not None else True,
            "validation_error": state1.error is not None,
            "turn_sentiment": state1.sentiment,
            "seconds": elapsed,
        }

    t0 = perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        hard_live_rows = list(pool.map(_eval_hard, hard_cases))
    hard_wall = perf_counter() - t0

    core_live_rows = prev["e2"]["live_case_audit"]
    assert len(core_live_rows) == 64
    all_live_rows = core_live_rows + hard_live_rows
    live_all_preds = [r["pred_frequency"] for r in all_live_rows]
    hard_live_preds = [r["pred_frequency"] for r in hard_live_rows]

    methods_80 = {
        "naive_keyword_heuristic": _score_e2_predictions(all_cases, naive_all),
        "tfidf_calibrated_lr_forced": _score_e2_predictions(
            all_cases, ml_forced_all, {"fit_seconds": ml_fit_sec, "tau": 0.0}
        ),
        "tfidf_calibrated_lr_tau_060": _score_e2_predictions(
            all_cases, ml_tau60_all, {"fit_seconds": ml_fit_sec, "tau": 0.60}
        ),
        "rule_provider_screening": _score_e2_predictions(all_cases, rule_screen_all),
        "rule_provider_clarification_ctx": _score_e2_predictions(
            all_cases, rule_clar_all
        ),
        "live_dual_channel_chatbot": _score_e2_predictions(
            all_cases,
            live_all_preds,
            {
                "core_64_joint_accuracy": prev["e2"]["methods"][
                    "live_dual_channel_chatbot"
                ]["joint_end_to_end_accuracy"],
                "hard_16_joint_accuracy": _score_e2_predictions(
                    hard_cases, hard_live_preds
                )["joint_end_to_end_accuracy"],
                "hard_16_metrics": _score_e2_predictions(hard_cases, hard_live_preds),
                "validation_error_count": sum(
                    1 for r in all_live_rows if r["validation_error"]
                ),
                "quote_provenance_verified_rate": float(
                    sum(
                        1
                        for r in all_live_rows
                        if r["had_item_update"] and r["quote_substring_verified"]
                    )
                    / max(1, sum(1 for r in all_live_rows if r["had_item_update"]))
                ),
                "hard_wall_seconds": hard_wall,
            },
        ),
    }

    live_errors = [
        r
        for r in hard_live_rows
        if (
            r["pred_frequency"] is not None
            if r["should_abstain"]
            else r["pred_frequency"] != r["gold_frequency"]
        )
    ]

    v2 = {
        "manifest": {
            "suite": "dual-channel-s1-streamlined-v2",
            "project_title": "Sentiment Analysis for Depression Detection",
            "n_experiments": 3,
            "e1_tweeteval_test_n": 12284,
            "e1b_bilingual_n": 48,
            "e2_total_test_n": 80,
            "e2_core_n": 64,
            "e2_hard_challenge_n": 16,
            "e2_train_n": 320,
            "e3_live_sessions_n": 4,
        },
        "e1": prev["e1"],
        "e2": {
            "n_test_cases": 80,
            "n_core_cases": 64,
            "n_hard_cases": 16,
            "n_train_corpus": 320,
            "train_test_sha256_overlap": 0,
            "methods": methods_80,
            "ml_risk_coverage_curve": risk_curve,
            "hard_16_live_audit": hard_live_rows,
            "live_error_cases": live_errors,
        },
        "e3_end_to_end": {
            "live_sessions": prev["e4"]["e4b_live_sessions"],
            "architectural_audits": prev["e4"]["e4c_architectural_audits"],
        },
    }
    (out_dir / "summary_v2.json").write_text(
        json.dumps(v2, indent=2, ensure_ascii=False)
    )
    print(f"[DONE] Saved streamlined v2 summary to {out_dir / 'summary_v2.json'}")
    print(
        f"[INFO] Live Chatbot on 80 total cases: joint_acc={methods_80['live_dual_channel_chatbot']['joint_end_to_end_accuracy']:.4f}, hard_16_acc={methods_80['live_dual_channel_chatbot']['hard_16_joint_accuracy']:.4f}, live_errors={len(live_errors)}"
    )
    return v2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prev",
        type=Path,
        default=ROOT / "results" / "dual-channel-s1-20261127" / "summary.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "dual-channel-s1-v2-20261127",
    )
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("FYP_API_BASE", "https://car.cheng-x.online/v1"),
    )
    args = parser.parse_args()
    key = args.key_file.read_text().strip()
    run_v2_bundle(args.prev, args.output, api_key=key, base_url=args.base_url)


if __name__ == "__main__":
    main()
