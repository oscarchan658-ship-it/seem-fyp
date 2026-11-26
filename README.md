# Sentiment Analysis for Depression Detection

**目前預設為自然對話模式。** AI 會記住本次聊天、理解跨題回答並追問缺少的頻率；最後核對八項才計分。啟動方式及變更見 [自然對話指南](docs/CONVERSATION_UPGRADE.md)。舊問卷基線移至 `questionnaire_app.py`。下列實驗數字屬先前 baseline，不能當成新對話模型的準確率。


Group T 的第一學期研究原型。主線是「可獨立評估的 sentiment model + 保留確認及修改機制的 PHQ-8 對話流程」。新版模型產生對話、症狀候選及獨立情緒標籤；計分函式不讀取情緒標籤。僅輸入虛構案例；題幹是待審譯稿，安全 Guard 是 mock，並非診斷或危機偵測工具。

[專案檔案導覽](docs/PROJECT_MAP.md) · [英文整合報告](docs/report/Group_T_Semester_1_Final_Report.pdf)

## 最新成果（2026-11-26）

| 已執行工作 | 證據及限制 |
|---|---|
| TweetEval 三模型基線 | 固定 split；SVM test Macro-F1 0.5607，Macro Recall 0.5715，n = 12,284。英文一般情緒分類，不是抑鬱準確率。 |
| 64-case parser diagnostic | 規則接受 24/64，接受答案中 24/24 正確；另有 8 個可解答案例被拒絕。AI 編寫、未盲測。 |
| Terra 中英 pilot | 48 次請求，46 次有效且符合編寫的標籤，2 次連線失敗；有效回應延遲中位數 12 秒。第三方回報模型身分。 |
| 軟體驗證 | 223 tests passed；完成中英自然對話及確認計分的瀏覽器驗證。舊版 207 tests / 84% coverage 另存歷史證據。 |
| 文獻整理 | 9 篇研究來源，逐篇記錄閱讀範圍、證據、限制及設計影響。 |

正式 E1、人工標註 E2 和 E3 研究仍未執行；舊 synthetic rehearsal 不可當作這些正式研究的結果。新證據入口：[semester1](docs/evidence/semester1/)；詳解：[繁中指南](docs/SEMESTER1_GUIDE_ZH.md)；[文獻閱讀矩陣](docs/literature/reading_matrix.md)。

## 執行 prototype

使用 Python 3.12，在 repo 根目錄執行：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-research.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

打開 http://127.0.0.1:8501 。新對話模式需要 Terra API；舊問卷基線可用 `python -m streamlit run questionnaire_app.py`，預設不啟用情緒模型。本地 SVM 需交付包內的 `results/tweeteval-20261126/sentiment_model.joblib`；如只複製 Git repo，需要按下段重訓。本地模型不處理中文。

使用已授權的第三方 Terra 服務：

```bash
python scripts/serve_connected.py --base-url https://car.cheng-x.online/v1
```

它會隱藏輸入 API key，放在當前服務程序環境，不寫入程式或檔案。不要同時開兩個 8501 服務。新對話頁在開始後，每次請求會傳送本次虛構對話歷史。側欄 Language 可切換繁體中文／English；舊訊息與引句保留原文。端點自行回報模型名稱，並不等於獨立驗證實際底層模型。`store=false` 也不保證第三方的保留政策。新對話模式遇到 API 失敗會提供重試；不產生新候選或分數。舊問卷基線可離線用選項作答。

## 重現實驗

```bash
python scripts/download_tweeteval.py
python -m research.sentiment_benchmark data/tweeteval results/tweeteval-reproduction
python -m research.diagnostic_cases results/diagnostic-reproduction
python scripts/run_connected.py --base-url https://car.cheng-x.online/v1 --output results/terra-reproduction
python scripts/summarize_pilot.py --folder results/terra-reproduction
```

`run_connected.py` 會產生一次 smoke test 及 48 次實際 API 呼叫，可能產生供應商費用；它與不跑實驗的 `serve_connected.py` 不同。使用新 output 目錄保留原測量。原始 TweetEval text/labels 不放入交付 ZIP，下載腳本鎖定 upstream commit，manifest 保留 hashes。

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q --cov=. --cov-report=term-missing
```

## 架構與歷史文件

[架構](architecture.md)、[需求](requirements.md)、[NLU 合約](nlp_contract.md)及 `docs/verification` 保留原始規格與驗收歷史。當舊文件描述「無 sentiment 依賴」時，是 11 月 26 日整合前的狀態；本 README、semester1 evidence 和最終報告說明本次新增範圍。
