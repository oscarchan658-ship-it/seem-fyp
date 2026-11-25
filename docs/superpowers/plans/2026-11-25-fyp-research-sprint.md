# SEEM FYP 五日研究 Sprint 實作計劃

**版本與狀態**　修訂版，納入七項方法修正。實作及實驗待執行。基線為 `main` 的 `502a86d`。延用 Python 3.12、pytest、Streamlit 及現有離線研究工具。按 Ponytail full 保持最小改動，按 Superpowers 逐步先驗證回歸測試的失敗原因，再實作及重跑。

**研究範圍**　Dataset B 為 96 條合成 Pilot，正式獨立鎖定集須另行收集。組員負責兩人獨立標註、裁決、Oracle 內容、模型選擇、Dataset A 授權及 FMEA 評級。

**依賴次序**　Day 1 同時啟動 Dataset A 授權核查、模型交接及 Oracle 編寫。Day 2 等兩份盲標及裁決先凍結。Day 3 開鎖前先凍結模型、評估程式、指標、子組及閾值。外部輸入未到位時，繼續可獨立完成嘅工程驗收，受影響實驗記 `NOT RUN` 並寫明所缺內容。

## 25 日｜R1、案例及盲標交接

1. **分開頻率類別與症狀事實。** 在 `research/day_mapping.py` 用純函式將 0–1、2–6、7–11、12–14 日映射為候選 0、1、2、3。只接受 0–14 嚴格整數。約略單值採 ±1 日，與 0–14 取交集。明示範圍使用所述端點。跨級、倒序或無效輸入維持澄清。`RuleProvider` 只在同題、過去 14 日嘅明確澄清回合辨識完整天數短句。英文及繁中各覆蓋精確、約略同明示範圍。初答、錯題、時間窗衝突及混合敘述繼續澄清。 [PHQ-8 Days 研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC3108293/)

   本地 Rule 候選附有已驗證嘅區間證據，驗證器重新計算映射並檢查語義。區間 `[0,0]` 對應 `symptom_present=False, negation=clear`，下限 ≥1 對應 `True, none`，區間含 0 同正數則用 `None, none`。所以 **1 日 → 候選 0、症狀曾出現**。`[0,1]` 亦可得候選 0，症狀是否曾出現仍未知。無本地天數證據嘅候選沿用原契約，外部 NLI／LLM 回傳本地證據欄位即拒絕。Guard 優先，候選只入暫存，八項唯一且明確確認後先計分。
2. **案例及盲標。** 產出八題 × 12 類共 96 條，Development 64 條、Locked Pilot 32 條，每題 8／4 並輪換類別。以 `group_id` 綁定來源家族及改寫，發放前檢查跨集合語義近似。私有 coverage matrix 保留題號、類別、語言和必要 context。延用現有標註 CLI，增加 Pilot 合併匯出模式。A／B 各收一份 **混合 96 案**嘅 CSV，使用共同不透明 ID，各自固定洗牌。可見欄位只有 ID、題目、作答文字、適用嘅題目 context 同三個空白標籤欄。表格、檔名及指南均無 split、group、source、類別提示或模型結果。保管人另存 ID ↔ 原案／split 對照，收齊兩份後先拆分，供原有比較及凍結流程使用。標註指南只用池外例子。
3. **追問準備。** 建立 E2b 固定追問模板。保管人從 Development 同 Locked Pilot 各預選 16 條初答案例，每題各兩條。優先選 clarification-needed，其次由數字／約略、時間窗缺漏、歧義、矛盾或拒答案中按私有案例 ID 選，再從該題其餘案例按 ID 補足。用同一編寫規格準備兩組追問回覆。A／B 各收到混合 32 案嘅獨立追問標註表，另用一套不透明 ID。E3 預備 24 個 Oracle 模板，每題三個主案例，含初答、追問、回覆、Gold、未解決／拒答分支、action ID、八題回放及確認快照清單，由組員填寫。
4. **Day 1 驗收。** 映射測 0／1／2／6／7／11／12／14、越界、非整數、`around 5 days`、兩個跨級範圍、0–1 區間語義、錯題及時間窗。候選回歸測一般文字候選偽造零分、外部 payload 偽造本地證據、Guard 中斷及確認前無結果。逐欄檢查盲標文件無 split 線索、ID 可逆、每案恰好出現一次、兩份排序可重現。以虛構表格走通匯出、填表、還原。交付 R1 規格、案例、矩陣、兩份盲標 CSV、指南、模板及含 Git SHA／版本／雜湊嘅 manifest。由獨立工作樹開一個待審 PR，原始鎖定案例及私有對照留在保管範圍內。跑全套 pytest、Ruff、格式、`pip check`、Streamlit 同題澄清及確認，記錄新 PR CI。

## 26 日｜人工 Gold、覆蓋感知分割及模型接線

- 保管人收取 A／B 獨立 CSV，驗證 ID 集完全一致、標籤合法、每案一次。執行 `research.annotation compare` 產出各欄 Cohen’s κ、頻率 weighted κ（限雙方均為 0–3）、配對數、列聯及分歧表。裁決人填齊最終標籤、參考 ID 及理由。沿用 `freeze` 核實三份 JSONL 及 SHA256。Locked Pilot 保持封存。
- **Coverage-aware validation** 只讀已裁決嘅 Development。以 25% 案例數（目標 16 條）作目標，整組搬動，唔以 16 個群組為配額。覆蓋維度固定為八個 item、五個 Gold 類別（0–3、unresolved）及 12 個案例類別。優先讓 train、validation 同時保留出現於至少兩個獨立群組嘅每個維度值。其後比較 validation 人數偏差，再比較分布同 Development 比例嘅絕對誤差總和。用 seed 42 決定相同分數嘅群組順序。
- 實作使用確定性貪婪加組，再用單組搬動或兩組交換改善同一排序目標，直至無改善。兩邊必須非空。單組獨有嘅維度值優先留 train，同時輸出未覆蓋維度及原因。若可分配嘅題號或 Gold 類別仍缺覆蓋，標記 `SPLIT_REVIEW_REQUIRED`，保管人核查群組與來源後先凍結。類別覆蓋缺口須登記並限制對應子組結論。測試固定 seed、輸入列重排、大群組、稀有類別、缺覆蓋及跨 split 改寫。Manifest 記錄案例數、群組數、覆蓋及版本。
- 接入獲組員核定嘅本地 NLI、Structured LLM 及可用嘅 Sentiment。延用 provider 合約及 schema。至少 Rule 加一個真模型通過 Development smoke。驗收 timeout、壞 JSON、錯題及 Sentiment 失效。保存模型、模板、信心號定義、資料雜湊、依賴及 Git SHA。
- 以私有 `case_id → category` 對照餵入分割器。E2b 回覆繼承配對初答嘅 `group_id` 同實際 split，凍結資料及 manifest 時逐案核對。完成 Day 2 驗收前，保管人獨立重算各輸入及輸出嘅 SHA256，保留受限檔案及標註員身份嘅存取隔離。

## 27 日｜E2a、E2b 及 E3

| 實驗 | 固定輸入及交付 |
|---|---|
| **E2a 初答** | 同一份凍結 Locked Pilot 及相同初答題目 context，比較 Rule／NLI／LLM。每案呼叫一次，無追問 context。 |
| **E2b 追問回答** | 讀取 Day 1 預選、雙人盲標及裁決後凍結嘅 16 宗 Locked Pilot 追問。每案有固定同題、過去 14 日嘅澄清問題同一個人寫回覆。三模型讀同一輸入，模型最初有否接受均照跑。配對分析用同一批 16 案，分別以各回合 Gold 判正，另報兩回合 Gold 均可解嘅子集。 |
| **E3 政策** | 獨立凍結人寫 Oracle、同一 provider/version 嘅預測、確認分支及八題回放。每題最多兩次追問。P0 為無澄清離線基線。P1／P2 共用批次確認機制，P2／P3 共用硬條件及閾值。記錄追問、確認次數、錯誤暫存、未解決、缺分支、完成率及完整 Gold 案嘅最終絕對分數誤差。P0 嘅完成率同確認後分數標 `N/A`。 |

**固定 E2 分母，分開報 E2a 同 E2b。** 每臂每案一列。無效、失敗、缺候選、或未通過硬條件一律預測為棄答。Gold 只有 0–3 或 `unresolved`，後者表示人類裁定證據不足。歧義辨識以 Gold `ambiguity != none` 為正類，分母為該集合全案，另記輸出無效數。

| 指標 | 計法 |
|---|---|
| 頻率 Accuracy | 正確 0–3 數 ÷ Gold 為 0–3 嘅案件數。棄答仍在分母。 |
| 頻率 Macro F1 | 每個非空集合固定平均 0、1、2、3 四類。逐類算 `2TP/(2TP+FP+FN)`，該類分母為 0 時按 0 納入平均，並列明各類 Gold support。Gold 為該類而棄答或猜錯即 FN。接受該類而 Gold 為另一類或 unresolved 即 FP。全空子組記 NA。 |
| 棄答率／覆蓋率 | 棄答案數 ÷ 全案數，覆蓋率為已接受案數 ÷ 全案數。 |
| Gold unresolved 佔比 | Gold unresolved 案數 ÷ 全案數。 |
| Unresolved 錯誤接受率 | Gold unresolved 但接受案數 ÷ Gold unresolved 案數。 |
| 接受後風險／系統失敗率 | 接受後風險為接受案件中錯分或 Gold unresolved 嘅比例。系統失敗率為技術失敗案數 ÷ 全案數。所有比率分母為 0 時記 NA。 |

**固定 E3 baseline 及選閾值方法。** 每模型以 **P1 在 E2a Development Validation 嘅初答決策**作 baseline。套用 P1 硬條件，忽略 confidence，baseline risk = 錯誤接受數 ÷ 硬條件接受數，接受 unresolved 計入錯誤。用同一批案例、同一 Gold 同硬條件計候選 τ。搜尋 `{0, 1} ∪ validation 觀察到嘅合規 confidence`，接受條件為 confidence ≥ τ。選擇風險 ≤ baseline 且接受數 >0 嘅最高 coverage 點，同 coverage 選最大 τ。baseline 零接受、無合法 confidence 或無合格 τ，該模型 P2／P3 標 `NOT RUN`。先保存 baseline 數值、分子／分母、搜尋點同 τ 及設定雜湊，再開 Locked Pilot。鎖定曲線沿用預存網格，零接受時 risk 未定義。AURC 附觀測 coverage 範圍。測試 unresolved 錯收、同 coverage 決勝、零接受、缺信心同驗證／鎖定輸入隔離。

交付 E2a／E2b 逐案預測、摘要及錯誤 CSV，並保存分組分母、交叉模型錯誤、可解棄答、高信心錯誤同有獨立情緒資料時嘅 affect–symptom divergence。E3 交政策摘要、逐案 trace、risk–coverage CSV、圖及實驗 manifest。逐案輸出可重算所有彙總。缺模型、未凍結 Oracle 或缺驗證資料嘅實驗列標 `NOT RUN`。

驗收用小型人工算例覆核四類 F1（包括零 support）、棄答、錯收 unresolved、技術失敗、全空子組及接受數為零。另測 E2b 每模型收足同一批 16 案、無模型篩選，以及 E3 所有政策共用相同分支和追問上限。E3 完成率分母為固定全套八題腳本數，分數誤差分母只計完成且八題 Gold 齊備嘅腳本，兩者都須列分子／分母。

## 28 日｜正式 E1

- 確認 Dataset A 授權、target／標籤來源、參與者分組及重複文本。同一 participant split、共用預處理及相同訓練資料下，比較 S（sentiment）、N（context／symptom）、F（同一 N 特徵加同一 S 特徵）。
- **固定同一 downstream model family 及 tuning budget。** 正式二元分類三臂統一用 L2 logistic regression，採 `liblinear`、seed 42、`class_weight=None`、`tol=1e-4`、`max_iter=1000`。各跑相同五個 `C` 候選 `[0.01, 0.1, 1, 10, 100]`，以相同 Validation Macro F1 選模型，同分取較小 C。分類閾值固定 0.5。Train 或 Validation 缺任一 target 類時暫停凍結，保留參與者分組，由資料負責人審核分割。共同特徵處理參數只在 train 擬合。開鎖前封存三臂設定，Test 只做最終比較。
- **主比較為 F − N 嘅 Test Macro F1 差及配對 95% participant bootstrap CI**，同一重抽 ID 用於兩臂，2,000 次、seed 42。三臂另報 AUROC、Precision、Recall、Macro F1、混淆矩陣及 divergence 分組。交 `results/e1/` 嘅 manifest、S／N／F 預測、指標、CI、分組表及圖。Dataset A 或可用 target 未到位，正式 E1 標 `NOT RUN`。
- 以資料供應者批准嘅 participant split 優先；若無指定分割，按 participant target 分層，以 seed 42 分 60%／20%／20%，凍結實際 ID，再逐組檢查 participant 及正規化文本洩漏。目標定義由資料負責人確認。主 CI 用兩臂差值嘅 bootstrap 2.5／97.5 百分位，若少於兩個獨立參與者就報 NA。驗收三臂 Test ID、target、設定空間相同，並從逐案預測重算主比較。

## 29 日｜工程分析與證據交付

- 重跑已有故障注入，涵蓋 NLI／Sentiment 不可用、LLM timeout／壞 JSON、信心缺失、過期事件、重複確認、澄清期間重設及 Oracle 缺分支。更新 FMEA，由組員核定三項評級。相同負載量度可用模型冷／熱延遲、p50／p95、失敗率、記憶體、tokens 及成本。Pareto 使用覆蓋一致嘅比較組合，按 accuracy、risk、latency、cost、turns 判定，記錄缺指標或不可比嘅組合。
- Final Evidence Register 串起實驗 ID、資料與設定雜湊、樣本分母、模型版本、Git SHA、CSV、表圖同證據狀態。乾淨安裝後重跑 pytest、Ruff、依賴及可重現實驗，核對表圖數字、機密、受限原始資料及研究原型措辭。團隊據此定稿學術判斷。

## 交付核對

| 日程 | 可驗收檔案及證據 |
|---|---|
| Day 1 | `research/day_mapping.py`、私有 `source_cases.jsonl`／`development.jsonl`／`locked_evaluation.jsonl`／coverage matrix、A／B 盲標 CSV、標註指南、E2b 模板及 `oracle_template.csv`、候選 manifest、待審 PR 及 CI。 |
| Day 2 | `development_train.jsonl`、`development_validation.jsonl`、`locked_evaluation.jsonl`、已凍結 manifest、`agreement.json`、分歧與裁決 CSV、`model_manifest.json`。 |
| Day 3 | `e2a_*`／`e2b_*` 預測、摘要及錯誤 CSV，`e3_policy_results.csv`、`e3_case_traces.jsonl`、`risk_coverage.csv`、`experiment_manifest.json`、E2／E3 圖表。 |
| Day 4 | `results/e1/` 嘅 `dataset_manifest.json`、`predictions_s.csv`／`predictions_n.csv`／`predictions_f.csv`、`metrics.csv`、`bootstrap_ci.csv`、`divergence_analysis.csv`，以及可重建圖表或 `NOT RUN` 紀錄。 |
| Day 5 | `results/final/`、`docs/evidence/`、`docs/figures/`、`docs/tables/`、`docs/fmea/`、`docs/reproducibility/`、Final Evidence Register。用 `python -m pip install -r requirements-dev.txt`、`python -m pip check`、`python -m ruff check .`、`python -m ruff format --check .`、`python -m pytest -q --cov=. --cov-report=term-missing`，並用 manifest 重跑有授權及齊備輸入嘅實驗。 |
