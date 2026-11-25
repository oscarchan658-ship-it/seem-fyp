# Research Sprint 證據登記

## 已交付工程

| 項目 | 證據 | 狀態及範圍 |
|---|---|---|
| R1、候選契約、Guard及八題確認 | tests/test_day_mapping.py、tests/test_app.py、tests/test_b1_context.py | 本地映射及回歸已執行；1日可為候選0並保留症狀事實 |
| 96條未標註合成案例、64／32分配、盲標A／B、32案人寫跟進模板 | research.pilot_package、tests/test_pilot_package.py、tests/test_handoff.py | 已產生可交接CSV及私有對照；全部Gold留白；語義近似仍待人工覆核 |
| Group-aware及coverage-aware分割、κ、裁決、凍結與雜湊 | research.coverage_split、research.annotation、tests/test_annotation.py、tests/test_research_protocol.py | 工具及虛構案例驗收通過；正式Gold集合未凍結 |
| E2a／E2b及固定配對、指標分母 | research.experiment_runner、research.e2、tests/test_handoff.py | 初答／追問分開，父資料、來源、模型及發放版本可核對 |
| E3 Oracle人寫內容、實際模型預測凍結及回放 | research.oracle_predictions、research.e3_runner、tests/test_oracle_predictions.py | JSON重載、本地R1、模型簽章、Validation閾值及固定網格曲線有回歸 |
| E1同模型／預算、F−N及participant bootstrap | research.e1、tests/test_experiment_runners.py | 已用獨立虛構fixture實際擬合三臂；正式E1未執行 |
| Rule量度、CSV圖表及重現演練 | docs/verification/nov25-rehearsal、research.engineering、research.rehearsal | 一個合成回應，首次加30次warm推論；只量Python配置記憶體 |
| 故障注入及FMEA | tests/test_fault_injection.py、tests/test_research_providers.py、docs/fmea/research-sprint.csv | 故障路徑有測試，風險評級留待人核定 |
| 完整驗收 | docs/verification/nov25-tests.txt、docs/reproducibility/nov25-environment.txt | Python 3.12.14；實際完整測試輸出及依賴版本已保存 |

## 正式研究前置條件

| 實驗 | 狀態 | 所缺輸入 |
|---|---|---|
| E1 Depression-related S／N／F | NOT RUN | Dataset A授權、target來源、participant split、審查過嘅特徵及divergence標籤 |
| E2a／E2b 96案Pilot | NOT RUN | 兩人獨立標註、裁決、語義近似覆核、模型與模板版本及本地檔案 |
| E3正式Policy／Risk–Coverage | NOT RUN | 24–32個人寫完整Oracle、確認分支、可重現模型輸出及Validation閾值；Rule無confidence，P2／P3不可補人工信心 |
| 多模型benchmark與Pareto | NOT RUN | 指定模型、同一工作量、accuracy／risk／latency／cost／turns五項可比實測值 |
| FMEA最終評級及學術結論 | PENDING HUMAN | Severity／Occurrence／Detectability核定及團隊研究判斷 |

Rehearsal嘅16個虛構參與者、四條E2 fixture同一份八題腳本各自有來源標記，與96案候選池分開。圖表標題標明Synthetic engineering check。S／N／F的fixture分數只證明計算路徑，不能回答sentiment增量價值。正式結果未有實驗ID及完整輸入前維持NOT RUN。

## 重現及檔案位置

程式、測試及PR以 `research/nov25-sprint` 分支為準。交接包保存於工作區外層嘅 `research-handoff-20261125-final/`，只將對應A或B表及指南交畀標註員，private目錄由保管人保存。原始標註、鎖定案例及私有對照不提交Git。

[交接包實際核對](../verification/nov25-package-check.json) 記錄96案、兩表各96列、12類、8題、全空Gold及14個檔案雜湊核對。[完整工程演練manifest](../verification/nov25-rehearsal/rehearsal_manifest.json) 連到實際CSV、圖及逐案輸出。程式版本為 `e10f23d`。完整 pytest **197 passed**，Ruff、格式及 pip check 通過。獨立審查回歸12項通過，最終未發現剩餘Important問題。

PR推送曾被自動審批拒絕。審批理由為尚未明確授權將這批內容傳送到現有GitHub目的地；已向使用者提出具體目的地批准要求。批准到位前保持本地提交，正式遠端CI記為NOT RUN。

命令及配置見 [操作文件](../reproducibility/research-sprint.md)。圖表從逐案CSV重建，對應JSON記錄來源SHA256。每個輸出資料夾使用新名稱，量度每次重跑會產生新時間及記憶體值。
