"""AI-authored, unblinded diagnostic fixtures, NOT an independent clinical set."""

import csv
import hashlib
import json
from pathlib import Path

from evidence_manager import evaluate_candidate
from nlu_provider import ClarificationContext, NluRequest, RuleProvider

OPTIONS = ("完全沒有", "有幾天", "超過一半的日子", "幾乎每天")
SYMPTOMS = (
    "失去興趣",
    "心情低落",
    "睡不好",
    "疲倦",
    "食慾不振",
    "覺得自己失敗",
    "難以集中精神",
    "坐立不安",
)


def cases():
    rows = []
    for item, symptom in enumerate(SYMPTOMS, 1):
        value = (item - 1) % 4
        days = (0, 4, 9, 14)[value]
        specs = [
            ("canonical", OPTIONS[value], value),
            ("explicit_window", "過去兩週" + OPTIONS[value], value),
            (
                "natural_symptom",
                f"過去兩週，我{OPTIONS[value]}會{symptom}"
                if value
                else f"過去兩週，我完全沒有{symptom}",
                value,
            ),
            ("negation", f"過去兩週並不是幾乎每天{symptom}", None),
            ("ambiguous", f"最近有時會{symptom}", None),
            ("conflicting_time", f"上個月幾乎每天{symptom}，但這兩週不確定", None),
            (
                "contradiction",
                f"過去兩週完全沒有{symptom}，但又幾乎每天{symptom}",
                None,
            ),
            ("numeric_followup", f"{days} days", value),
        ]
        for category, text, gold in specs:
            rows.append(
                dict(
                    case_id=f"D{item}-{category}",
                    item_id=item,
                    category=category,
                    text=text,
                    expected=gold,
                    clarification=category == "numeric_followup",
                    source="AI-authored diagnostic; not blinded; frozen before this run",
                )
            )
    return rows


def naive(text):
    # Deliberately simple comparator: first recognized frequency wins.
    return next((i for i, option in enumerate(OPTIONS) if option in text), None)


def summarize(rows):
    accepted = [r for r in rows if r["predicted"] is not None]
    unresolved = [r for r in rows if r["expected"] is None]
    resolvable = [r for r in rows if r["expected"] is not None]
    correct = sum(r["predicted"] == r["expected"] for r in accepted)
    return dict(
        n=len(rows),
        accepted=len(accepted),
        accepted_correct=correct,
        coverage=len(accepted) / len(rows),
        accepted_accuracy=correct / len(accepted) if accepted else None,
        unresolved_n=len(unresolved),
        unresolved_false_accepts=sum(r["predicted"] is not None for r in unresolved),
        resolvable_n=len(resolvable),
        resolvable_abstentions=sum(r["predicted"] is None for r in resolvable),
    )


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    source = cases()
    encoded = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in source)
    (output / "cases.jsonl").write_text(encoded)
    rows = []
    provider = RuleProvider()
    for case in source:
        context = (
            ClarificationContext(case["item_id"], "frequency_in_past_14_days")
            if case["clarification"]
            else None
        )
        result = evaluate_candidate(
            provider.predict(
                NluRequest(case["item_id"], case["text"], clarification=context)
            ),
            case["item_id"],
        )
        for name, value in [
            ("naive_keyword", naive(case["text"])),
            ("context_rule", result.value),
        ]:
            rows.append({**case, "model": name, "predicted": value})
    summary = {
        name: summarize([r for r in rows if r["model"] == name])
        for name in ("naive_keyword", "context_rule")
    }
    (output / "summary.json").write_text(
        json.dumps(
            {
                "mode": "AI-AUTHORED DIAGNOSTIC, NOT BLINDED E2",
                "case_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                "results": summary,
            },
            indent=2,
        )
    )
    with (output / "predictions.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    import sys

    run(Path(sys.argv[1]))
