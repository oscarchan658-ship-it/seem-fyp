"""Fast, deterministic offline unit tests for the Unified S1 Dual-Channel suite."""

from collections import Counter

import numpy as np

from research.dual_channel_s1.benchmarks import (
    _norm_sha256,
    build_e1b_screening_cases,
    build_e2_hard_challenge_cases,
    build_e2_ml_train_corpus,
    build_e2_symptom_cases,
    build_e3_partial_observation_cohort,
    build_e4_dialogue_personas,
)
from research.dual_channel_s1.run_experiments import (
    _run_invariance_audits,
    _simulate_p0_rigid_rule,
    _simulate_p1_greedy_unclarified,
    _simulate_p2_selective_dual_channel,
)

QUADRANTS = (
    "congruent_low",
    "situational_distress",
    "masked_somatic",
    "congruent_elevated",
)


def test_e1b_screening_cases_structure_and_naive_proxy_divergence():
    cases = build_e1b_screening_cases()
    assert len(cases) == 48
    assert len({c.case_id for c in cases}) == 48
    assert len({_norm_sha256(c.text) for c in cases}) == 48

    lang_counts = Counter(c.language for c in cases)
    assert lang_counts == {"en": 24, "zh": 24}

    quad_counts = Counter(c.quadrant for c in cases)
    assert quad_counts == {q: 12 for q in QUADRANTS}

    for c in cases:
        assert c.elevated_phq8 is (c.profile_phq8_total >= 10)

    # Naive proxy: predicting elevated PHQ-8 (>= 10) iff gold_polarity == "negative"
    sit_cases = [c for c in cases if c.quadrant == "situational_distress"]
    masked_cases = [c for c in cases if c.quadrant == "masked_somatic"]
    assert len(sit_cases) == 12
    assert len(masked_cases) == 12

    sit_fp_rate = np.mean(
        [(c.gold_polarity == "negative") and (not c.elevated_phq8) for c in sit_cases]
    )
    masked_fn_rate = np.mean(
        [(c.gold_polarity != "negative") and c.elevated_phq8 for c in masked_cases]
    )
    assert sit_fp_rate == 1.0
    assert masked_fn_rate == 1.0


def test_e2_symptom_cases_and_disjoint_ml_train_corpus():
    cases = build_e2_symptom_cases()
    assert len(cases) == 64
    assert len({c.case_id for c in cases}) == 64

    lang_counts = Counter(c.language for c in cases)
    assert lang_counts == {"en": 32, "zh": 32}

    resolvable = [c for c in cases if not c.should_abstain]
    must_abstain = [c for c in cases if c.should_abstain]
    assert len(resolvable) == 32
    assert len(must_abstain) == 32

    r_prefixes = {c.category.split("_", 1)[0] for c in resolvable}
    a_prefixes = {c.category.split("_", 1)[0] for c in must_abstain}
    assert r_prefixes == {"R1", "R2", "R3", "R4"}
    assert a_prefixes == {"A1", "A2", "A3", "A4"}
    assert Counter(c.category.split("_", 1)[0] for c in resolvable) == {
        "R1": 8,
        "R2": 8,
        "R3": 8,
        "R4": 8,
    }
    assert Counter(c.category.split("_", 1)[0] for c in must_abstain) == {
        "A1": 8,
        "A2": 8,
        "A3": 8,
        "A4": 8,
    }
    assert all(c.gold_frequency in {0, 1, 2, 3} for c in resolvable)
    assert all(c.gold_frequency is None for c in must_abstain)

    train_texts, train_labels = build_e2_ml_train_corpus()
    assert len(train_texts) == 320
    assert len(train_labels) == 320
    assert Counter(train_labels) == {0: 80, 1: 80, 2: 80, 3: 80}

    test_hashes = {_norm_sha256(c.user_text) for c in cases}
    train_hashes = {_norm_sha256(t) for t in train_texts}
    assert len(test_hashes) == 64
    assert len(train_hashes) == 320
    assert len(train_hashes & test_hashes) == 0


def test_e3_partial_observation_cohort_stratification_and_distinct_utterances():
    profiles = build_e3_partial_observation_cohort(seed=42)
    assert len(profiles) == 240
    assert Counter(p.split for p in profiles) == {"train": 160, "test": 80}
    assert Counter(p.quadrant for p in profiles) == {q: 60 for q in QUADRANTS}

    all_utterances = [utt for p in profiles for utt in p.turn_texts]
    assert len(all_utterances) == 240 * 8 == 1920
    assert len(set(all_utterances)) == 1920
    assert len({_norm_sha256(u) for u in all_utterances}) == 1920

    # Deterministic under fixed seed
    repeat = build_e3_partial_observation_cohort(seed=42)
    assert [p.turn_texts for p in profiles] == [p.turn_texts for p in repeat]


def test_e4_dialogue_personas_and_policy_simulators():
    personas = build_e4_dialogue_personas()
    assert len(personas) == 32
    assert Counter(p.language for p in personas) == {"en": 16, "zh": 16}
    assert Counter(p.quadrant for p in personas) == {q: 8 for q in QUADRANTS}

    p0_runs = [_simulate_p0_rigid_rule(p) for p in personas]
    p1_runs = [_simulate_p1_greedy_unclarified(p) for p in personas]
    p2_runs = [_simulate_p2_selective_dual_channel(p) for p in personas]

    mean_turns_p0 = float(np.mean([r["user_turns"] for r in p0_runs]))
    mean_turns_p2 = float(np.mean([r["user_turns"] for r in p2_runs]))
    assert mean_turns_p2 < mean_turns_p0
    assert all(r2["user_turns"] < r0["user_turns"] for r0, r2 in zip(p0_runs, p2_runs))

    mean_mae_p1 = float(np.mean([r["pre_review_item_mae"] for r in p1_runs]))
    mean_mae_p2 = float(np.mean([r["pre_review_item_mae"] for r in p2_runs]))
    assert mean_mae_p2 == 0.0
    assert mean_mae_p2 < mean_mae_p1

    quad_acc_p2 = float(np.mean([r["quadrant_detected_correctly"] for r in p2_runs]))
    assert quad_acc_p2 == 1.0


def test_architectural_invariance_audits():
    audits = _run_invariance_audits()

    assert audits["affect_score_invariance"]["pass_rate"] == 1.0
    assert audits["affect_score_invariance"]["violations"] == 0

    assert audits["adversarial_quote_and_schema_audit"]["rejection_rate"] == 1.0

    assert audits["pre_api_safety_guard_audit"]["pass_rate"] == 1.0
    assert audits["pre_api_safety_guard_audit"]["downstream_llm_calls_triggered"] == 0


def test_e2_hard_challenge_cases_disjoint_and_balanced():
    hard = build_e2_hard_challenge_cases()
    core = build_e2_symptom_cases()
    train_texts, _ = build_e2_ml_train_corpus()

    assert len(hard) == 16
    assert Counter(c.language for c in hard) == {"en": 8, "zh": 8}
    assert sum(not c.should_abstain for c in hard) == 8
    assert sum(c.should_abstain for c in hard) == 8

    hard_h = {_norm_sha256(c.user_text) for c in hard}
    core_h = {_norm_sha256(c.user_text) for c in core}
    train_h = {_norm_sha256(t) for t in train_texts}
    assert len(hard_h) == 16
    assert not (hard_h & core_h)
    assert not (hard_h & train_h)
