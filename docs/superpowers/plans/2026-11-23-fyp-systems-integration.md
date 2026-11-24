# Systems Engineering & Integration 實作計劃

這份文件記錄 2026-11-23 制訂的 V3.1 基線。V3.2 的合併、實測結果及待核定事項以 [交付與驗收現況](../../verification/v32-delivery.md) 為準。下列實作前問題與預期屬制訂計劃時的紀錄。

**目標**　以合成情境重現 consent → 作答／澄清 → 批次核對／修改 → 確認 → 結果，以及任何活動狀態的安全中斷。

**架構**　採用本地規則、單一控制器和純評分函式。先完成可獨立驗證的核心介面，再接 Streamlit。UI 透過事件提交，未來模型僅經驗證後以候選輸出接入。

**技術**　Python、pytest、Streamlit。第一期使用本地記憶體與合成 fixtures。

**規格**　Master Plan V3.1（本機原檔 `FYP_Research_and_Implementation_Master_Plan_V3_1.docx`） §IV–V、§VIII、§X–XII、[架構與介面](../../../architecture.md)、[需求追蹤與驗收](../../../requirements.md)。

## 決策與前置依賴

| 待確認事項 | 建議與影響 |
|---|---|
| 現有 repo 在哪個路徑或網址？需指定分支／commit 嗎？ | 先定位 checkout、讀取最近的 `AGENTS.md`、依賴與 CI 設定，檢查實際入口並記錄基線。未確認前，本文路徑是提案。 |
| 是否採九狀態與終止行為？ | 建議明列 END、安全中斷後不恢復舊會話、結果後重做建新會話。確認後同步修正圖 2 和「七大狀態」條文。 |
| Guard 的 `review`、故障行為、規則與文案由誰核准？ | 建議均暫停但用不同回應碼。由導師及適當審閱者確認用途、適用語言／地區、固定文案與虛構案例。合成測試可用替身驗證流程。 |
| 第一階段支援何種語言、量表題幹、頻率措辭和合成語料？ | WP03 可先做。WP05 建議鎖定一套經團隊確認的題目／四級選項與雙方都能重現的有限詞彙。測試標明覆蓋的語言。結果分段標籤一併確認。 |
| G0 demo 使用哪個環境？11 月 27 日是 sprint 目標或正式截止？ | 預設本機合成 demo。V3.1 §VIII-D 把日期當作 sprint 計劃，§X 把正式截止列為待確認。待 repo 基線確認 Python／pytest／Streamlit 版本。 |

全期保留 **Sentiment Analysis for Depression Detection**。不得使用真實病患資料、補零、從 sentiment 推分、繞過安全中斷或聲稱臨床安全。所有軟體及測試步驟目前未執行。真實模型與資料集授權不影響這一階段，臨床用途未納入。

## 建議實作與測試次序

未來每批先新增對應的最小 pytest 案例，核對實際失敗原因，再補最小程式、重跑目標測試與完整回歸。提交或填報時引用真實執行證據。

| 次序 | 交付內容與依賴 | 驗收與執行方式 |
|---|---|---|
| 0．WP01 repo 基線及契約 | 取得 checkout，執行 `git rev-parse --show-toplevel`、`git status --short`、`git rev-parse HEAD`，核對源碼、依賴、測試及已存在的介面。若有既有環境，執行 `python -m pytest -q`。然後鎖定型別、必備欄位及已決事項。`schemas.py` 隨消費端逐步建立。 | 根據實際 repo 修訂本文件路徑。記錄基線狀態。審核 T34 的可追溯性，未有程式或測試直接如實記錄。 |
| 1．WP03 評分 | 落實 `ConfirmedAnswer`、`Phq8Result` 和 `score_phq8`。依賴 WP01 評分合約。 | `python -m pytest -q tests/test_phq8.py`，T01–T06 的評分部分、T25。純函式可獨立交付。 |
| 2．WP04 控制器及 Safety Guard 接口 | 建立型別化事件、`new_session`、`dispatch`。以結構化選項、Guard／NLU 替身驗證狀態、批次確認及安全優先順序。納入可審查的本地規則與固定決策碼。依賴 WP01 和 WP03。 | `python -m pytest -q tests/test_controller.py tests/test_safety_guard.py`。T06–T08、T17–T23、T26、T28–T29 的核心斷言。T21／T22 的實際規則用例依賴審查。 |
| 3．WP05 規則與 Schema 整合 | 落實 `validate_nlu`、`extract` 及 `decide_candidate`。把本地規則接入控制器，保留 injection 作回退測試。把給組員的資料介面沿用本規格，按 WP05 需要整理成 `nlp_contract.md`。依賴 WP01 語言及欄位決策、WP04 入口。 | `python -m pytest -q tests/test_rule_nlu.py tests/test_controller.py`。T09–T16、T24、T27，至少通過清楚、缺時間、頻率模糊三類，再核對否定及衝突。 |
| 4．WP06 Streamlit 與整合 | 建立 `app.py` 的事件繫結、畫面渲染、批次編輯、重跑／重設與安全轉移。依賴 WP03–05。 | `python -m pytest -q` 加 `streamlit run app.py`，覆蓋 T08、T19–T20、T23–T24、T28–T33 的整合斷言。保存實際截圖、demo 紀錄及限制。 |
| 5．WP01／06 驗收 | 對照每條 FR／NFR 和 V3.1 G0。記錄未執行、失敗與已驗證項目，保留執行日期、版本、環境與 commit。 | 以 T34 核對測試證據，並完成可重現的合成展示紀錄。 |

### 下一個 coding task

取得和核對 repo 後，先做 **WP03 純 PHQ-8 評分引擎與單元測試**。以同一任務加入或重用 `ConfirmedAnswer`、`Phq8Result`，保留既有呼叫慣例。驗收涵蓋全零、全三、混合值、分段邊界、七項、暫存混入、重複／額外題號及非法型別。通過後以確認集合的契約接 WP04。
