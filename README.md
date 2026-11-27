# Sentiment Analysis for Depression Detection

**預設為中英自然對話模式。** AI 會記住本次聊天、理解跨題回答並追問缺少的頻率；最後核對八項才計分。啟動方式及變更見 [自然對話指南](docs/CONVERSATION_UPGRADE.md)。舊問卷基線移至 `questionnaire_app.py`。下列實驗分別評估公開資料情緒分類、規則解析和單句情緒；新版多輪對話的抽取準確率尚未獨立評估。

Group T 的第一學期研究原型。主線是「可獨立評估的 sentiment model + 保留確認及修改機制的 PHQ-8 對話流程」。新版模型產生對話、症狀候選及獨立情緒標籤；計分函式不讀取情緒標籤。僅輸入虛構案例；題幹是待審譯稿，安全 Guard 是 mock，並非診斷或危機偵測工具。

[專案檔案導覽](docs/PROJECT_MAP.md) · [英文整合報告](docs/report/Group_T_Semester_1_Final_Report.pdf)

## 最新成果（2026-11-26）

| 已執行工作 | 證據及限制 |
|---|---|
| TweetEval 三模型基線 | 固定 split；SVM test Macro-F1 0.5607，Macro Recall 0.5715，n = 12,284。英文一般情緒分類，不是抑鬱準確率。 |
| 64-case parser diagnostic | 規則接受 24/64，接受答案中 24/24 正確；另有 8 個可解答案例被拒絕。AI 編寫、未盲測。 |
| Terra 中英 pilot | 48 次請求，46 次有效且符合編寫的標籤，2 次連線失敗；有效回應延遲中位數 12 秒。第三方回報模型身分。 |
| 軟體驗證 | 報告截點為 223 tests passed；完成中英自然對話及確認計分的瀏覽器驗證。舊版 207 tests / 84% coverage 另存歷史證據。 |
| 文獻整理 | 9 篇研究來源，逐篇記錄閱讀範圍、證據、限制及設計影響。 |

正式 E1、人工標註 E2 和 E3 研究仍未執行；舊 synthetic rehearsal 不可當作這些正式研究的結果。新證據入口：[semester1](docs/evidence/semester1/)；詳解：[繁中指南](docs/SEMESTER1_GUIDE_ZH.md)；[文獻閱讀矩陣](docs/literature/reading_matrix.md)。

## 雙通道語氣對照與計分不變性

- **回合級語氣紀錄（`sentiment_trace`）**：`conversation.py` 在每次通過結構與原文子字串驗證的回合後，將使用者回合的情緒標籤（`negative`、`neutral`、`positive`、`unclear`）追加至 `state.sentiment_trace`；若觸發重置或 `safety_guard.py` 示範標記中斷，紀錄會與對話及候選一併清空。
- **確認後非計分對照（`analyze_affect_symptom_alignment(state)`）**：完成八項明確核對並進入 `RESULT` 後，`conversation.py` 的 `analyze_affect_symptom_alignment(state)` 會對照對話負向語氣比例與已確認總分（是否 `>= 10`），歸類為四個研究觀察象限：`congruent_low`、`situational_distress`、`masked_somatic`、`congruent_elevated`。`app.py` 於側欄顯示累計語氣統計（標明不參與計分），並於結果頁呈現雙通道觀察說明。
- **計分嚴格不變性與安全邊界**：`phq8_engine.py` 的 `score_phq8` 只接受八個已確認題號及其嚴格整數頻率 `0–3`，對情緒極性（`sentiment` 與 `sentiment_trace`）保持嚴格不變（strictly invariant）。`safety_guard.py` 僅為檢查示範標記（demonstration marker guard）的前置攔截模組，並非危機偵測器（not a crisis detector）；所有軟體測試與雙通道指標均不構成臨床效度證明。

## 執行 prototype

使用 Python 3.12，在 repo 根目錄執行：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/serve_connected.py --base-url https://car.cheng-x.online/v1
```

啟動器會隱藏輸入 API key，再啟動本機網頁。打開 http://127.0.0.1:8501 ，選擇繁體中文或 English，按「開始虛構對話」。先聊天、補充或更正，再核對八項頻率並確認計分。不要同時啟動兩個 8501 服務。

也可執行 `python -m streamlit run app.py --server.address 127.0.0.1`，在側欄輸入端點和密鑰。需要可用的相容 Responses API；端點必須支援本專案使用的模型名稱和 structured output。

| 設定 | 用途 |
|---|---|
| `FYP_API_KEY` | 啟動器或環境提供的 API key；側欄輸入可覆蓋。 |
| `FYP_API_BASE` | API Base URL；啟動器由 `--base-url` 設定。 |
| `OPENAI_API_KEY` | API client 的備用 key 來源；使用第三方端點時請確認密鑰屬於該服務。 |

密鑰保留於程序環境或頁面 session；程式不寫入檔案。每次請求會傳送本次虛構對話歷史及候選證據。服務端自行回報 `gpt-6.1-terra` 身分；`store=false` 不保證第三方的保留政策。API 失敗會提供重試且不產生新候選或分數。40 回合後停止聊天；資料完整仍可核對與計分，資料不足則重新開始。

離線比較基線：`python -m streamlit run questionnaire_app.py --server.address 127.0.0.1`。它保留逐題規則流程，預設不啟用情緒模型。選配本地 SVM 可從交付包取得或按下節重訓；雙語聊天不需要該模型檔案。

## 重現實驗

先安裝實驗及開發依賴：

```bash
python -m pip install -r requirements-research.txt
python scripts/download_tweeteval.py
python -m research.sentiment_benchmark data/tweeteval results/tweeteval-reproduction
python -m research.diagnostic_cases results/diagnostic-reproduction
python scripts/run_connected.py --base-url https://car.cheng-x.online/v1 --output results/terra-reproduction
python scripts/summarize_pilot.py --folder results/terra-reproduction
```

`run_connected.py` 會產生一次 smoke test 及 48 次實際 API 呼叫，可能產生供應商費用；它與不跑實驗的 `serve_connected.py` 不同。使用新 output 目錄保留原測量。原始 TweetEval text/labels 不放入交付 ZIP，下載腳本鎖定 upstream commit，manifest 保留 hashes。

統一第一學期雙通道評估套件位於 `research/dual_channel_s1/`：

- `research/dual_channel_s1/benchmarks.py`：建立中英四象限語氣與症狀落差案例（E1B，48 案）、症狀頻率抽取與選擇性棄答測試集及零 SHA-256 重疊的 320 句訓練語料（E2）、240 組八回合部分觀察隊列（E3），以及 32 組對話策略人物設定與虛構多輪腳本（E4）。除公開 TweetEval 資料集外，其餘均為作者設計之診斷基準與受控模擬，並非臨床病患資料或臨床效度驗證。
- `research/dual_channel_s1/run_experiments.py`：整合執行 E1–E4 實驗（含 `score_phq8` 情緒極性不變性、引句出處與 schema 驗證，以及 `safety_guard.py` 示範標記前置攔截審計；支援 `--offline-only` 離線重現或連接 API 輸出至全新目錄）。
- `research/dual_channel_s1/plot_figures.py`：讀取實驗輸出的 JSON 結果檔，產出對應的圖表檔案。

```bash
python -m research.dual_channel_s1.run_experiments --offline-only --output results/dual-channel-offline-repro
```

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q --cov=. --cov-report=term-missing
```

## 文件與驗證

- [目前架構](architecture.md)：聊天、來源驗證、重試、核對和計分。
- [需求及測試對照](requirements.md)：目前 chat mapping，以及保留基線的歷史矩陣。
- [English demo guide](docs/CONVERSATION_GUIDE_EN.md)／[繁中成果指南](docs/SEMESTER1_GUIDE_ZH.md)。
- [研究工具](research/README.md)：已執行實驗及尚未完成的 E1/E2/E3 工具。
- [基線 NLU 合約](nlp_contract.md)：只適用 `questionnaire_app.py`。

`docs/verification/` 和舊 research-sprint register 是有日期的歷史證據。過時的執行計劃已移除，原稿可從 Git 歷史找回。報告與測量紀錄保留實驗當時的數字；目前軟體檢查以 GitHub Actions 及 [清理驗證紀錄](docs/evidence/repository-cleanup.md) 為準。
