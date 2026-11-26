# Research experiments and evaluation tools

## Executed semester studies

| Command/module | Scope | Saved evidence |
|---|---|---|
| `research.sentiment_benchmark` | Official TweetEval splits; majority, logistic regression and SVM | `docs/evidence/semester1/sentiment_metrics.json` |
| `research.diagnostic_cases` | 64 authored rule-parser cases | `docs/evidence/semester1/parser_diagnostic.json` |
| `scripts/run_connected.py` | 48 authored bilingual sentiment requests plus a smoke request | `docs/evidence/semester1/terra_summary.json` |

Commands and installation are in the root [README](../README.md). These studies do not evaluate clinical diagnosis or independent multi-turn extraction accuracy.

## Future study tools

The modules below support E1/E2/E3 study preparation. Formal studies have not been completed. Existing synthetic rehearsals only verify the pipelines. See [reproduction and handoff](../docs/reproducibility/research-sprint.md) and the [dated evidence register](../docs/evidence/research-sprint-register.md).

## Dataset B 人工標註交接

準備兩份獨立來源 JSONL。每行包含 `case_id`、`group_id`、`item_id`、`text`、`source_id`。沿用現有 `source_id` 欄位記錄來源。將同一原句與改寫放入同一 `group_id`。

```text
python -m research.annotation prepare development.jsonl locked.jsonl sheets
python -m research.annotation compare development.jsonl sheets/development-a.csv sheets/development-b.csv development-review
python -m research.annotation compare locked.jsonl sheets/locked-a.csv sheets/locked-b.csv locked-review
python -m research.annotation freeze development.jsonl locked.jsonl sheets/development-a.csv sheets/development-b.csv development-review/adjudicate.csv sheets/locked-a.csv sheets/locked-b.csv locked-review/adjudicate.csv frozen --validation-groups 4 --seed 42
```

每位標註者只收到自己的空白評分欄。鎖定集評分表由資料管理人保管。填寫 `gold_frequency`（0–3 或 `unresolved`）、`ambiguity`（`none`、`ambiguous_frequency`、`uncertain`、`contradiction`、`off_topic`）及 `timeframe`（`past_14_days`、`missing`、`other`、`unclear`）。`compare` 產出 κ、頻率 weighted κ、有序標註配對數、列聯表及分歧列。兩位對任何欄位有分歧時，由裁決人填寫三項最終標籤及 `annotation_ref`；一致項沿用雙人標籤並保存來源表雜湊。上例的 validation group 數與 seed 是用法示例，以團隊核定值執行。

`freeze` 輸出 development train、validation、locked evaluation 三份 JSONL 及 SHA256 manifest。輸出資料夾須使用新名稱。以相同案例、裁決資料、seed 與群組數重現相同檔案；保存原始標註表，不把受限輸入或標註表提交至 repo。

## E3 人工 Oracle 交接

```text
python -m research.follow_up_oracle oracle.json --formal
```

JSON 頂層為案例陣列。每案提供 `case_id`、`author_ref`、`item_id`、`initial_answer`、`system_clarification`、`gold_frequency` 及 `branches`。每分支填 `turn`、`action_id`、`outcome`、`text`。同案以不同 action ID 區分分支，至少有一個 `reply` 和一個 `unresolved` 或 `refusal`。後兩者的 `text` 為 null。工具驗證 24–32 案及結構並產生檔案雜湊。正式跑批還須凍結同一模型的各分支預測及確認回應。

## Day-to-frequency mapping

The retained RuleProvider now uses the versioned R1 mapping in `research/day_mapping.py`: 0–1 days → 0, 2–6 → 1, 7–11 → 2, 12–14 → 3. Earlier notes saying day-count conversion was disabled are obsolete. The chat prompt uses the same intervals, but does not independently validate the model's semantic interpretation. Source and limitations are discussed in the report and literature matrix.

## C11 Dataset B

分兩個集合獨立收集。Development Set 可用於規則、模板及 validation。Locked Evaluation Set 的 gold 交資料管理人保管，先凍結再評估。公開／受限輸出依實際授權處理。本 repo 的測試 fixture 是合成工具驗證。

每條 JSONL 記錄包含 `case_id`、`group_id`、`item_id`、`text`、`gold_frequency`（0–3 或 `unresolved`）、`ambiguity`、`timeframe`、`source_id`、`annotation_ref`。以同一 `group_id` 標記原句及改寫。先由兩人獨立記錄 `case_id, annotator_id, frequency, ambiguity, timeframe`，比較分歧後由裁決人記錄決定及理由，再將裁決紀錄 ID 填入 `annotation_ref`。人工檢查語義近似及權限，驗證器檢查編號、型別、群組及正規化後的同題重複回答。

```text
python -m research.dataset_b development.jsonl locked-evaluation.jsonl
```

凍結前核定主要指標、分組和評估樣本量，保存指令產生的 manifest。用 `split_development` 由開發集作群組分割，保存 seed 與每列 split。正式樣本、標註及符合預定規格的凍結驗收目前待完成。

## C12 Rule baseline

使用通過 C11 驗證的開發資料執行 `python -m research.rule_baseline development.jsonl rule-predictions.csv`。指令匯出 case ID、gold、候選或空值、原因、版本及耗時。摘要分開顯示 coverage、棄答與有明確 gold 且已接受的正確率。正式 benchmark 仍待獨立凍結集。

## C19 Follow-up Oracle

以 `case_id + turn + action_id` 指定人工編寫的回應。若同一輪可由多種前序路徑到達，使用不同的 `action_id` 表達分支，不覆寫同一鍵。顯式空回應表示 unresolved；缺鍵是 missing_branch。模擬器應分開報告，並在已核定的追問額度耗盡時停止，避免自行補答。各政策使用同一組腳本。

目前單元測試有追問、確認時修訂、再確認、無法解答及缺分支案例。完整 P0–P3 比較仍依賴 C09 和已凍結的逐題及完整會話案例。

## C17 Engineering Smoke Test

`python -m research.e1_smoke` 用固定合成分數驗證 S／N／F 共用相同 case ID 和標籤，並檢查混淆矩陣、AUROC、Macro F1 和 Recall 的計算路徑。輸出只報管線檢查，沒有實證分數。Empirical E1 尚未執行，需先核對 Dataset A 的授權、使用條件、受訪者分組及目標標籤。
