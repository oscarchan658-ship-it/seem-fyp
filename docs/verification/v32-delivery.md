# Sentiment Analysis for Depression Detection

## V3.2 驗收與交付清單

| 任務 | 可查證交付 | 剩餘門檻 |
|---|---|---|
| C01–C02 | [已合併的 PR #3](https://github.com/oscarchan658-ship-it/seem-fyp/pull/3)和[瀏覽器紀錄](wp01-wp06-synthetic.md) | 快速輸入的框架送達限制已記錄 |
| C03–C04 | [品質與追蹤 PR #4](https://github.com/oscarchan658-ship-it/seem-fyp/pull/4) | 人工審查及合併 |
| C05–C06、C08、C10 | [Controller 與驗證 PR #6](https://github.com/oscarchan658-ship-it/seem-fyp/pull/6)及離線確認回放 | PR 審查及天數映射核定 |
| C07、C16 | 離線情緒介面、研究錯配標記、失效處理和評分測試 | 組員模型版本及特徵輸出規格 |
| C09、C19 | 離線 P0–P3、八題回放、批次候選快照 Oracle、缺分支與未解決狀態 | 定稿正式案例、追問及確認分支 |
| C11–C12 | [Dataset B 驗證與 Rule runner](v32-research-readiness.md)；合成 CSV 已測 | 核定樣本量、主要分組、盲標裁決及鎖定集 |
| C13–C15 | C14 的 MOCK JSON 傳輸、結構拒絕、有限重試及用量驗證。C15 已測缺失信心、閾值及硬性衝突 | NLI 模型／模板、各模型信心定義、LLM 服務及成本核定 |
| C17–C18 | S／N／F Engineering Smoke Test 和 Rule 管線驗證 | Empirical E1 的 Dataset A 授權與標籤；正式 E2 的鎖定資料及全部模型輸出 |
| C20–C22 | 風險覆蓋、閾值、觀測範圍 AURC、配對群組 bootstrap 和 κ 均有測例；本機基準 manifest 有實際 SHA、時間和環境 | 正式資料與實驗設定後才可生成實證曲線及重現報告 |
| C23–C24、C27 | MOCK 失效與中斷[驗收及 FMEA 初稿](v32-research-readiness.md) | 人工審核失效分級及正式 Guard |
| C25–C26 | [本機 Rule 量測 manifest](v32-rule-benchmark/manifest.json)、[CSV](v32-rule-benchmark/timings.csv)和 Pareto 合成單元測試 | 多模型同條件量測，以及正式 Pareto 圖表 |
| C28–C30 | 本文件決策、證據和既有[架構圖](../../architecture.md) | 正式結果到齊後產生統計及比較圖 |
| C31–C34 | 下方報告整理、重現命令、demo 記錄及提交稽核 | 完整簡報、主報告、個人貢獻、Progress Form、Academic Honesty Declaration 及學系提交待團隊核定 |

## 決策與證據

- 先驗證會話，再依次執行 MOCK Guard、NLU、證據檢查及確認評分。控制器和 AppTest 驗證同會話中斷先於評分。 [既有瀏覽器與測試證據](wp01-wp06-synthetic.md)
- 離線政策使用一個 provider 和版本。P1／P2 固定資料、Oracle 與確認方式；P2／P3 固定閾值及硬性規則。同一八題合成案例驗得批次確認一次，逐題確認八次，總分均為 16。正式 E3 的人寫分支、資料快照及閾值待凍結。
- 在沒有接受案例時將風險記為空值。AURC 附觀測範圍。配對 CI 以群組抽樣，只有一個獨立群組便不報 CI。Pareto 排名須同時有 Accuracy、Risk、Latency、Cost 和 Turns。
- Rule 基準以 Windows 11、Python 3.12.14、Streamlit 1.67.0，使用一條合成輸入。首呼叫及 30 次暖機呼叫均成功。Warm p95 為 **0.0247 ms**，包含記憶體追蹤開銷。Token 與費用欄為空。 [原始量測](v32-rule-benchmark/manifest.json)

## 報告八章的證據索引

| 章節 | 可用材料 |
|---|---|
| I 緒論 | 核准題目、系統範圍、V3.1 研究問題 |
| II 文獻回顧 | 量表、情緒與症狀線索、澄清及風險管理。團隊核對引用 |
| III 問題與需求 | [FR／NFR](../../requirements.md)、資料邊界及 E1–E4 指標 |
| IV 設計 | [架構](../../architecture.md)、確認、守門及離線 Oracle |
| V 實作 | 各 PR、SHA、測試及 demo 證據 |
| VI 結果與討論 | 已驗證合成流程及本機量測。正式實證結果待實跑 |
| VII 工程分析與限制 | FMEA 初稿、瀏覽器限制、同條件 Pareto 設計 |
| VIII 結論及後續 | 以核驗結果回答研究問題，經團隊審查結論及 AI 使用披露 |

## 重現與最終稽核

Python 3.12 環境下由 repo 根目錄執行。

```text
python -m pip install -r requirements-dev.txt
python -m pip check
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m research.e1_smoke
python -m research.synthetic_benchmark ./synthetic-run
python -m streamlit run app.py
```

Dataset A 存取由持有人提供。Dataset B 鎖定集與 gold 留在指定資料管理人的存取範圍內。正式跑批記錄資料及 split 雜湊、模型和 prompt 版本、閾值、seed、套件和程式 SHA。

2026-11-24（JST），程式提交 `b30c824f76dd4a539081261e1eb235e0a3cb2878`。Windows 本機 **145 個 pytest 通過**。Chrome 157.0.8103.80 排練合成澄清、八題、修改、確認得 14/24、重設及 MOCK 中斷均通過。 [確認結果](v32-demo-result.png) · [MOCK 中斷](v32-demo-interruption.png)

提交前由團隊逐項核對最終 Head CI、資料許可、報告數值、個人貢獻、Progress Form 及 Academic Honesty Declaration。未通過或未執行項目保留實際狀態。
