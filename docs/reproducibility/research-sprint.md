# 研究 Sprint 執行及交接

工程使用 Python 3.12。新環境先執行 `python -m pip install -r requirements-research.txt`。所有命令在 repo 根目錄執行。輸出目錄須為新名稱，避免覆蓋已凍結檔案。正式實驗須有人寫 Gold、版本固定嘅模型及輸入。合成工程 rehearsal 與 96 案 Pilot 各用獨立來源。

## Day 1 交付

`python -m research.pilot_package ../research-handoff-20261125`

標註員 A 只收到 `annotator_a.csv`，B 只收到 `annotator_b.csv`，並各附 `annotation_guide.md`。保管人保存 `private/`、manifest 同全部來源。矩陣的 12 類為 clear_frequency、natural_frequency、numeric_days、approximate_days、ambiguous、missing_timeframe、negation、contradiction、off_topic、refusal、affect_symptom_divergence、clarification_needed。每題每類一案，合共 96 案，初始無 Gold。矩陣同來源家族仍須人工檢查語義近似；修訂後要重新發表同封存雜湊。

R1 只在已詢問當題過去14日頻率嘅澄清回合啟用。0–1 日均可屬候選0。症狀事實按本地天數區間獨立驗證，1日係曾出現，0–1日則未知。外部 JSON 不能宣告本地證據。兩週初答數字維持澄清，E2a 同 E2b 因此分開量度。

## 雙人盲標及 Gold 凍結

收齊兩份表後執行以下命令，兩份原始表須保留。

```text
python -m research.blind_annotation ../research-handoff-20261125/private/blind_mapping.json ../research-handoff-20261125/annotator_a.csv ../research-handoff-20261125/annotator_b.csv ../returned-labels
python -m research.annotation compare ../research-handoff-20261125/private/development.jsonl ../returned-labels/development-a.csv ../returned-labels/development-b.csv ../review-dev
python -m research.annotation compare ../research-handoff-20261125/private/locked_evaluation.jsonl ../returned-labels/locked-a.csv ../returned-labels/locked-b.csv ../review-locked
```

裁決人填寫兩個 review 目錄內嘅 adjudicate.csv，保留 annotation_ref 及獨立裁決記錄。再執行凍結。

```text
python -m research.annotation freeze ../research-handoff-20261125/private/development.jsonl ../research-handoff-20261125/private/locked_evaluation.jsonl ../returned-labels/development-a.csv ../returned-labels/development-b.csv ../review-dev/adjudicate.csv ../returned-labels/locked-a.csv ../returned-labels/locked-b.csv ../review-locked/adjudicate.csv ../frozen-b --coverage-matrix ../research-handoff-20261125/private/coverage_matrix.csv --seed 42
```

新 Sprint 使用 coverage-matrix 選項。舊 validation-groups 介面保留供既有呼叫使用。新分割只讀 Development，整組分配，以覆蓋題號、Gold、案例類別優先，案例數目標25%。題號／Gold 出現於多組而仍缺覆蓋時拒絕凍結，保管人須檢查原因。類別缺口記入 manifest。讀者須同時查看 weighted κ 的配對數、完整列聯表及零分母情況。

## E2b 人寫跟進及配對

作者先填 `private/followup_author_template.csv` 中 followup_response、author_ref。兩位標註者收到嘅跟進表須由下列命令重新發布，模板中「待作者」字句不可當成作答。來源32案混合 Development16及Locked16。

```text
python -m research.handoff followups ../research-handoff-20261125 ../followup-issued
python -m research.annotation compare ../followup-issued/blind_sources.jsonl ../followup-issued/followup_a.csv ../followup-issued/followup_b.csv ../review-followup
python -m research.handoff freeze-followups ../research-handoff-20261125 ../frozen-followup --parent-dir ../frozen-b --a ../followup-issued/followup_a.csv --b ../followup-issued/followup_b.csv --adjudication ../review-followup/adjudicate.csv
```

跟進凍結保留原初答嘅 group_id 及實際 train／validation／locked 分配。配置 E2b 時加入 followup_manifest、parent_dir、split_role、initial_predictions、initial_manifest 路徑。runner 核對預選 ID、配對檔案及父資料雜湊、同一模型初答預測，輸出 e2b_pairs.csv、paired_summary.json。每條追問按自身 Gold 判正，both_resolvable 標出兩回合均可解嘅子集。

## E2、模型及閾值

```text
python -m research.experiment_runner ../frozen-b/locked_evaluation.jsonl research/configs/rule-pilot.json ../results-rule-e2a --turn initial
python -m research.experiment_runner ../frozen-followup/locked_evaluation.jsonl paired-rule-config.json ../results-rule-e2b --turn clarification
```

每個模型同一集合每案一列。F1固定四類，零類別分母用0；棄答計 FN，錯收 unresolved 計 FP。棄答率用全案數，Gold unresolved 錯收率用 unresolved Gold數，接受後 risk 用接受數。NA 保留空值，唔轉0。子組比較應連同 support 及每案輸出閱讀。

NLI config 用 provider=nli、model_path（已存在本機目錄）、version、templates、hypothesis_template。templates 為團隊核准嘅 hypothesis label → 完整 NluResult 欄位對照，item_id／model_version／confidence_signal 由 adapter 提供。使用本機 Transformers runtime，模型及 tokenizer 以 local_files_only=True、trust_remote_code=False 載入；先在獨立環境安裝與指定模型相容嘅 Transformers／PyTorch 版本並記錄。confidence 為最高 zero-shot score，須由團隊核定其研究用途。Structured LLM config 用 provider=structured_llm、version、command（argv陣列）及 timeout秒。Worker 從 stdin 收 item_id、text、question_timeframe、clarification，stdout 只回合法 NluResult JSON。外部資料服務受專案治理限制。載入失敗產出 NOT RUN manifest，逐案推論失敗保留該案並計棄答。

選 τ 時，config 須含 split_role=development_validation 及 dataset_manifest（frozen-b/manifest.json路徑），並執行 `--turn initial --validation-threshold`。runner 核對 manifest 嘅 Validation SHA256，拒絕追問資料同 Locked hash。threshold.json 保存 P1 baseline risk 分子／分母、候選網格、選定τ、Validation hash、模型設定簽章及版本。E3 重用同一模型設定並核對簽章。Rule 無 confidence，P2／P3 及 risk curve 記 NOT RUN，唔賦予人工信心值。

## E3 Oracle 及真正模型預測

oracle_template.csv 供逐題內容編寫及舊單題驗證用，`research.handoff oracle` 轉成單題 scenarios。完整政策實驗使用 questionnaire_template.json，每案須由作者填八題 initial_answer、gold_frequency、replies 及 batch。24–32 案嘅作者及內容由團隊核定。reply 分支明定 turn、action_id、outcome，追問動作為 clarify-frequency 並填 text；確認動作 confirm-item／confirm-batch 填 confirmed_value；拒答或未解決用 outcome=unresolved。替代分支用獨立 session_id 腳本表達，避免相同 turn/action 重複。batch 保存各可達八題 snapshot 及 confirmed 題號對值，全部確認內容由作者填。缺分支在結果單列。

```text
python -m research.oracle_predictions authored-questionnaires.json model-config.json frozen-questionnaires.json
python -m research.e3_runner frozen-questionnaires.json model-config.json validation-output/threshold.json e3-output
```

預測凍結步驟實際呼叫所選 provider。Rule 額外保存合成 request，JSON 重載時重算並比對，還原本地區間證據。NLI／LLM 使用已驗證輸出。E3 runner 輸出每題 trace、會話政策表、固定 Validation 網格嘅 Locked risk_coverage.csv、觀測範圍 AURC。零接受風險留空。P1／P2 批次確認一致，P2／P3 閾值及追問規則一致，每題最多追問兩次。

## E1、工程量度及重現

E1 config 參照 research/configs/e1.template.json。每行 features.jsonl 提供 case_id、participant_id、split（train／validation／test）、target（0／1）、sentiment_features（數值陣列）、context_features（數值陣列）、divergence（獨立取得布林標籤），以及可取得時嘅正規化 text_fingerprint。資料負責人先確認授權、標籤來源、分割、文字去重同特徵來源，抽取器嘅任何訓練／選擇只接觸 train／validation。

```text
python -m research.e1 features.jsonl e1-config.json e1-output
python -m research.engineering benchmark model-config.json benchmark-output --repetitions 30
python -m research.engineering plot e1-output/metrics.csv arm macro_f1 e1-output/comparison.png --mode empirical
python -m research.rehearsal results/engineering-self-check
```

S／N／F 共用 L2 logistic regression、五個C候選、seed42、同一validation選擇及0.5閾值，F只拼接同一S及N特徵。主比較為 F−N、配對 participant bootstrap 2000次。benchmark 將模型載入、首次推論及 warm p50／p95 分開，tracemalloc只量Python配置，RSS、tokens、cost未觀測則留空。Pareto 的五個指標須同一工作量及可比來源，缺指標組合由現有 pareto_front 排除。

rehearsal 使用獨立虛構 fixture 跑 E1實際擬合、E2a／E2b、E3回放、Rule量度及圖表，manifest 明列 Empirical E1／E2／E3 為 NOT RUN。重新執行時使用新目錄，核對所有非時間性輸出及來源雜湊；耗時同記憶體每次重新量度。

CI 安裝 requirements-research.txt，再執行 pip check、Ruff、格式及全套 pytest。Windows沙箱可能限制Streamlit建立本機socketpair，須用核准測試權限執行。故障測試及人工操作證據放 verification，受限來源同標註維持保管人存取範圍。
