"""Create unlabelled synthetic Pilot drafts. Humans supply all final labels."""

import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path

from research.annotation import LABELS, _sources, _write_csv

SYMPTOMS = (
    "做事情缺乏興趣或樂趣",
    "感到低落或沒有希望",
    "入睡困難、睡不安穩或睡得太多",
    "感到疲倦或缺乏精力",
    "食慾不振或吃得太多",
    "覺得自己很差或令家人失望",
    "難以集中精神",
    "動作或說話異常緩慢，或坐立不安",
)
CATEGORIES = (
    "clear_frequency",
    "natural_frequency",
    "numeric_days",
    "approximate_days",
    "ambiguous",
    "missing_timeframe",
    "negation",
    "contradiction",
    "off_topic",
    "refusal",
    "affect_symptom_divergence",
    "clarification_needed",
)
QUESTIONS = {
    item: f"過去兩週，你有多常{symptom}？" for item, symptom in enumerate(SYMPTOMS, 1)
}
CLARIFICATION = "只考慮剛才那一題及過去14天，請說明出現了多少天，或選擇四級頻率。"


def _drafts(item, symptom):
    # Wording and intended categories are candidates for human review, never Gold.
    return (
        "過去兩週"
        + ("完全沒有", "有幾天", "超過一半的日子", "幾乎每天")[(item - 1) % 4],
        f"這兩星期，{symptom}這個狀況隔幾日就會發生一次，合共大概四日。",
        f"過去14天，有{(1, 2, 6, 7, 11, 12, 14, 0)[item - 1]}天出現剛才說的狀況。",
        f"過去兩週，{symptom}約有{(5, 6, 7, 11, 12, 2, 1, 13)[item - 1]}天。",
        f"關於{symptom}，這兩星期只能說有時如此，我說不準頻率。",
        f"{symptom}是上學期的事，最近的時間範圍我未說過。",
        f"這兩星期並不是完全沒有{symptom}，但我記不起有幾日。",
        f"過去兩週我完全沒有{symptom}，不過我又記得每天都有這個情況。",
        f"你問{symptom}，但我想問的是下一班巴士幾點開。",
        f"這一題關於{symptom}我選擇不回答。",
        f"我整體心情不錯，也很期待週末。不過過去兩週，{symptom}有九日。",
        f"說到{symptom}，我需要先問清楚你想知道時間長短，還是發生的日數？",
    )


def _jsonl(path, rows):
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def _sheets(root, name, entries, seed):
    keys = sorted(entries)
    rng = random.Random(seed)
    opaque = [f"Q{index:03d}" for index in range(1, len(keys) + 1)]
    rng.shuffle(opaque)
    mapping = dict(zip(opaque, (entries[key]["private"] for key in keys)))
    visible = [
        dict(case_id=blind, **entries[key]["visible"])
        for blind, key in zip(opaque, keys)
    ]
    fields = tuple(visible[0]) + LABELS
    for reviewer, offset in (("a", 1), ("b", 2)):
        order = list(visible)
        random.Random(seed + offset).shuffle(order)
        _write_csv(root / f"{name}_{reviewer}.csv", fields, order)
    return mapping


def build(output: Path, *, git_sha):
    if output.exists():
        raise ValueError("Use a new package directory.")
    output.mkdir(parents=True)
    private = output / "private"
    private.mkdir()
    (output / "oracle").mkdir()
    source, coverage, entries = [], [], {}
    for item, symptom in enumerate(SYMPTOMS, 1):
        for index, text in enumerate(_drafts(item, symptom)):
            case_id = f"B{(item - 1) * 12 + index + 1:03d}"
            # Three rotating strata give 4 locked cases per item and 2–3 per category.
            split = "locked" if index % 3 == (item - 1) % 3 else "development"
            row = dict(
                case_id=case_id,
                group_id=f"family-{case_id}",
                item_id=item,
                text=text,
                source_id="codex-synthetic-pilot-v1",
            )
            source.append(row)
            coverage.append(
                dict(
                    case_id=case_id,
                    item_id=item,
                    category=CATEGORIES[index],
                    split=split,
                    language="zh-Hant",
                    semantic_review="PENDING_HUMAN",
                )
            )
            entries[case_id] = dict(
                private=dict(case_id=case_id, split=split),
                visible=dict(item_id=item, question=QUESTIONS[item], text=text),
            )
    _jsonl(private / "source_cases.jsonl", source)
    splits = {row["case_id"]: row["split"] for row in coverage}
    for split in ("development", "locked"):
        _jsonl(
            private
            / (
                "development.jsonl"
                if split == "development"
                else "locked_evaluation.jsonl"
            ),
            [row for row in source if splits[row["case_id"]] == split],
        )
    _sources(private / "development.jsonl", private / "locked_evaluation.jsonl")
    _write_csv(private / "coverage_matrix.csv", tuple(coverage[0]), coverage)
    mapping = _sheets(output, "annotator", entries, 42)
    (private / "blind_mapping.json").write_text(
        json.dumps(mapping, indent=2), encoding="utf-8"
    )
    followups = {}
    priority = {
        value: rank
        for rank, value in enumerate(
            (
                "clarification_needed",
                "numeric_days",
                "approximate_days",
                "missing_timeframe",
                "ambiguous",
                "contradiction",
                "refusal",
            )
        )
    }
    for split in ("development", "locked"):
        for item in range(1, 9):
            pool = sorted(
                (
                    row
                    for row in coverage
                    if row["split"] == split and row["item_id"] == item
                ),
                key=lambda row: (priority.get(row["category"], 99), row["case_id"]),
            )
            for row in pool[:2]:
                parent = row["case_id"]
                followups[f"F-{parent}"] = dict(
                    private=dict(case_id=f"F-{parent}", parent_id=parent, split=split),
                    visible=dict(
                        item_id=item,
                        question=QUESTIONS[item] + " " + CLARIFICATION,
                        text="【待作者填寫跟進回答，再交兩位標註者獨立評分】",
                    ),
                )
    followup_mapping = _sheets(output, "followup", followups, 1042)
    (private / "followup_mapping.json").write_text(
        json.dumps(followup_mapping, indent=2), encoding="utf-8"
    )
    _write_csv(
        private / "followup_author_template.csv",
        (
            "case_id",
            "parent_id",
            "item_id",
            "question",
            "initial_answer",
            "clarification",
            "followup_response",
            "author_ref",
        ),
        (
            dict(
                case_id=key,
                parent_id=entry["private"]["parent_id"],
                item_id=entry["visible"]["item_id"],
                question=QUESTIONS[entry["visible"]["item_id"]],
                initial_answer=entries[entry["private"]["parent_id"]]["visible"][
                    "text"
                ],
                clarification=CLARIFICATION,
            )
            for key, entry in sorted(followups.items())
        ),
    )
    _write_csv(
        output / "oracle/oracle_template.csv",
        (
            "case_id",
            "item_id",
            "author_ref",
            "initial_answer",
            "clarification",
            "followup_response",
            "gold_frequency",
            "unresolved_alternative",
            "refusal_alternative",
            "confirmation_reply",
        ),
        (
            dict(
                case_id=f"O{item:02d}-{variant}",
                item_id=item,
                clarification=CLARIFICATION,
            )
            for item in range(1, 9)
            for variant in range(1, 4)
        ),
    )
    (output / "oracle/questionnaire_template.json").write_text(
        json.dumps(
            [
                dict(
                    session_id=f"O{item:02d}-{variant}",
                    author_ref="",
                    items=[
                        dict(
                            item_id=number,
                            case_id=f"O{item:02d}-{variant}-item-{number}",
                            gold_frequency="",
                            initial_answer="",
                            replies=[],
                        )
                        for number in range(1, 9)
                    ],
                    batch=[],
                )
                for item in range(1, 9)
                for variant in range(1, 4)
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (output / "annotation_guide.md").write_text(
        "# 合成 Pilot 雙人獨立標註指南\n\n"
        "每位標註者只讀自己的 CSV，獨立完成後交保管人。請勿互看答案或查模型預測。\n\n"
        "gold_frequency 填 0、1、2、3 或 unresolved。0–1 日為0，2–6為1，7–11為2，12–14為3。"
        "單一約略日數採±1日（限0–14）；所涵蓋區間跨類時標 unresolved。"
        "頻率0可以包含出現1日，並不等於症狀從未出現。初答文字不明確、拒答或矛盾時請按實際證據標 unresolved，唔好補0。\n\n"
        "ambiguity 填 none / ambiguous_frequency / uncertain / contradiction / off_topic。"
        "timeframe 填 past_14_days / missing / other / unclear。閱讀表內題目作語境，但其他明示時間不可當作過去兩週。"
        "Gold 描述人類能否從所給語境辨認頻率，不按 RuleProvider 能否辨認決定。\n\n"
        "池外例子：過去14日症狀出現8日 → 頻率2；只說『偶爾』 → unresolved；只說去年情況 → other。\n\n"
        "跟進表目前係作者交接模板，必須先填入人寫回答並重新發放，之後先可評分。"
        "表內待填字句不可當成正式作答。所有標籤同裁決由人填寫。\n",
        encoding="utf-8",
    )
    files = {
        str(path.relative_to(output)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    manifest = dict(
        dataset_version="dataset-b-synthetic-pilot-v1",
        status="DRAFT_UNLABELLED",
        count=96,
        development=64,
        locked=32,
        seed=42,
        git_sha=git_sha,
        mapping_version="r1-v1",
        protocol="two independent blind annotations plus human adjudication",
        split_rule="rotating category strata; parent groups kept together",
        semantic_review="PENDING_HUMAN",
        oracle_status="TEMPLATE_ONLY",
        files=files,
    )
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    print(json.dumps(build(args.output, git_sha=sha), indent=2))
