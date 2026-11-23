# WP01–WP06 合成原型驗收紀錄

- 日期 2026-11-23。實測程式 commit `b9b407046a93f2bc8d7b7685e337f73e418d9114`。
- Windows，Python 3.12.14，pytest 9.2.0，Streamlit 1.67.0，Chrome 157.0.8103.80。應用程式只綁定本機 loopback。
- `python -m pytest -q` 實際 **84 passed**。Streamlit 合併文字／按鈕觸發的回歸測試修正前重現計分呼叫，修正後通過。瀏覽器驗收使用兩個獨立會話，資料全為虛構。

| 案例 | 預期及實際結果 | 狀態 |
|---|---|---|
| T01–T04、T25 | 0、24、混合 12、分段端點符合預期。非法題號／分數／暫存值及布林值被拒絕。 | 通過 |
| T05–T08 | 七項、重複題拒絕。重送不重寫答案。新快照編輯後算 14，舊確認無效。取消清空。 | 通過 |
| T09–T16 | 明確兩週頻率產生正確候選。缺時間、上週、模糊、雙重否定、不確定、跨題訊息及矛盾均無候選。 | 通過 |
| T17–T20 | 無同意不能作答。修改可返回原畫面。八題暫存與重跑均無結果。明確確認只計一次。 | 通過 |
| T21–T22 | 「受審」規則尚無核定版本。替身標記走中斷／覆核，指定虛構慣用語與引用標記不觸發。 | 替身通過。受審規則未驗收 |
| T23 | 六種活動狀態均可中斷。舊版本及非當前題不阻礙守門。同批確認與中斷先走安全，scorer 未呼叫。瀏覽器顯示暫停、清除及可重新開始。 | 通過 |
| T24、T27 | NLU 異常及格式錯誤留原題。四級選項可恢復並完成 0 分。Schema 拒絕錯題及非法值，JSON 保持 0 與 null。 | 通過 |
| T26、T28–T29 | 非法、跨會話及舊事件不變更狀態。計分失效保留核對頁。守門覆核、非法回傳或例外均阻斷並使用固定回應。 | 通過 |
| T30 | 瀏覽器與 pytest 流程在無 sentiment adapter 及模型服務的環境完成。 | 通過 |
| T31 | 畫面核准題目一致，標明合成研究原型。安全文案清楚標明替身與版本。 | 顯示通過。正式譯稿及文案待審 |
| T32 | 兩個獨立會話狀態互不影響。虛構文字無畫面回顯、提交欄位清空，觀察的伺服器輸出和專案檔案未找到測試字串。 | 通過 |
| T33 | 實際啟動 Streamlit，完成同意、澄清、答題、修改、確認及 14 / 24。另跑模擬中斷與重設。 | 通過 |
| T34 | 已核對需求與案例對應，並在本文記錄環境、日期、commit 及各案例組的結果。 | 通過 |

[合成結果截圖](fyp-synthetic-result.png)　[模擬中斷截圖](fyp-synthetic-interruption.png)

守門覆蓋應用收到的文字事件。Streamlit 可能合併同一輸入元件的快速重複提交。這次只驗收本機合成原型行為。

---

## Task 1 審核與穩定化補充紀錄（2026-11-23 UTC；獨立審查分支）

**審查分支**：`task1/audit-stabilise`；**基線 main**：`51d4ce22e9b4f826bb459cbddb8024196c4058df`。本段補充審查結果，不覆蓋上方於 `b9b4070` 的既有 Windows 驗收歷史。

**審查範圍**：`AGENTS.md`、`app.py`、`controller.py`、`phq8_engine.py`、`rule_nlu.py`、`safety_guard.py`、`schemas.py`、五個 `tests/test_*.py`、`.streamlit/config.toml`、`requirements.txt`、`architecture.md`、`requirements.md`、`nlp_contract.md`。僅用合成數據。PHQ-8 題幹、選項、計分引擎及 Mock Safety Guard 均未改動。

### 缺陷／風險審核

| ID / 優先 | 位置與重現 | 預期 vs 實際 | 決定與測試證據 |
|---|---|---|---|
| A01 / P1 | `app.py:33–52` 文字提交 callback 與待處理按鈕，`tests/test_app.py` 同批輸入。 | 同一輪若收到危機文字及確認按鈕，必須先走 Guard；現有 AppTest 可驗證，惟 Streamlit 快速同元件連續輸入可能合併（框架層限制，並非已證明會由程式保留每一筆）。 | **保留既有實作**；現有 `test_t23_coalesced_confirm_cannot_precede_safety_text` 經 CI 執行。仍需獨立真實瀏覽器／快速連續提交驗收。此項只證明 MOCK 事件優先序，不證明真正危機辨識。 |
| A02 / P2（已修復） | `rule_nlu.py:12`：輸入 `過去兩週有幾天 。` 會留下標點前空白，`decide_candidate` 回傳 null。 | 預期候選 1；修正前候選 null，落入澄清。 | 先提交 T35（`58954ef`）；GitHub CI `92c68c5` **4 failed, 87 passed**；再增加第二次 `.rstrip()`（`5f1f60f`）。測試亦鎖定模糊、缺兩週時間及衝突文字仍拒絕自動候選。 |
| A03 / P2（已修復） | 根目錄欠缺 `.github/workflows/ci.yml`；先前只能依賴獨立 Windows 紀錄。 | PR / main push 應自動在 Python 3.12 安裝依賴、執行 `pip check` 及全套 pytest。 | 新增 GitHub Actions 單一 `ubuntu-24.04` Job，`permissions: contents: read`；更新至 `checkout@v5`、`setup-python@v6`，避免 Node 20 deprecation。 |
| A04 / P3（已修正文件及新增測試） | `architecture.md:9,45` 的 Guard 敘述與 `controller.py:52–65` 真實次序不一致。 | 跨會話 `session_id` 應先拒絕；同會話舊版本 TEXT 即使題號不符，仍先經 Guard，再驗證版本。 | 更新 `architecture.md`；新增 T36：跨會話不觸發 Guard / NLU、同會話 stale TEXT 的 normal/review/interrupt，以及 SELECT 不進自由文字 Guard。保留既有 Controller 實作。 |
| A05 / 既有限制 | `safety_guard.py:7–13` 只識別 `[DEMO_INTERRUPT]`、`[DEMO_REVIEW]`。 | 正式危機訊號分類需另行審核，不在本次驗收範圍。 | **刻意維持 MOCK**。T21/T22 的受審規則及真實場景的 sensitivity / false-negative 仍 **未驗收**；不得宣稱危機檢測有效。 |
| A06 / 既有限制 | `rule_nlu.py` 只處理明確兩週前綴和四級繁體中文固定措辭；`app.py` 題幹為待審譯稿。 | 本階段應安全拒答無法解釋之文字，不推測 PHQ-8 分數。 | 保留狹義 Baseline；進階 NLU、正式題幹與額外語言覆蓋留待第二階段。 |

### 實際執行紀錄（區分測試層級）

| 檢查 | 執行環境與提交 | 實際結果 |
|---|---|---|
| 第一輪 Red 測試 | GitHub Actions Ubuntu 24.04、Python 3.12；commit `92c68c5`；[run 45210026439](https://github.com/oscarchan658-ship-it/seem-fyp/actions/runs/45210026439) | `pip check` 通過；`python -m pytest -q`: **87 passed、4 failed**，四個失敗均屬 T35 句尾空白回歸。 |
| 修正後 CI | GitHub Actions Ubuntu 24.04、Python 3.12.16、pytest 9.2.0、Streamlit 1.67.0；commit `4bae7d889eac161b32f64a07d9aa223cffb8a805`；[run 45211538593](https://github.com/oscarchan658-ship-it/seem-fyp/actions/runs/45211538593) | `pip check`: **No broken requirements found**；`python -m pytest -q`: **96 passed in 2.67 s**。該測試集包含 Streamlit AppTest，並非真實瀏覽器測試。 |
| 本機 Windows（歷史） | 2026-11-23，commit `b9b4070`；Python 3.12.14、pytest 9.2.0、Streamlit 1.67.0 | 原有紀錄報告 **84 passed** 並完成 Chrome 手動操作；不可沿用作目前 PR 最新 commit 的瀏覽器證據。 |
| 今次最新分支本機 Windows 跑測試 | 未執行 | **NOT RUN**：GitHub 連接提供遠端檔案／CI，當前執行環境未具有所述 Windows checkout。 |
| 今次最新分支真實瀏覽器驗收及雙會話操作 | 未執行 | **NOT RUN**：CI AppTest 及歷史截圖不取代最新分支的實際 Chrome 操作。需由本機環境執行並補上記錄。 |
| CI `main` push after merge | 未執行 | **NOT RUN**：PR 保留開啟，尚未合併。 |

### 設計決定與剩餘工作

1. **安全優先順序**：先檢查 Session ID（避免跨會話影響），對同一會話收到的活動狀態文字先過 Guard，之後才檢查 Revision、題號與 NLU。維持 guard fail-closed。現有安全測試只證明 Mock 接線。
2. **評分原子性**：不修改 `phq8_engine.py`；八個 0–3 唯一題號、明確 Batch Confirmation、缺答不可補零、Sentiment 不參與評分，均由既有單元與整合測試涵蓋。
3. **最小修正**：A02 只移除句尾標點前空白，拒答／澄清策略保持不變，未拓寬自然語言推論範圍。
4. **CI 及環境界線**：CI 使用 ubuntu-24.04／Python 3.12；Windows 實測必須另外記錄。過去截圖與 84 passed 係歷史證據。
5. **交付前仍需**：以最新 PR Head 執行真實 Chrome 同兩會話測試、核對 `main` 之後的可能變化、再核實當前 CI 成功狀態。PR 保持開啟，不自動合併。

### V3.2 C01／C02｜PR #3 瀏覽器補驗

實測日期 2026-11-24（JST）。測試提交 `89fa3207ae33b958ef0306f18a93fe9b74e35d75`。Windows、Python 3.12.14、pytest 9.2.0、Streamlit 1.67.0、Chrome 157.0.8103.80，以 Playwright 操作本機 loopback。依賴檢查通過；本機完整 pytest **96 passed**。本段接續上方的歷史 `NOT RUN` 紀錄。

| 案例 | 合成輸入／預期 | 實際結果 | 狀態 |
|---|---|---|---|
| 澄清 | 輸入「過去兩週有時」，留第 1 題 | 留在第 1 題並顯示澄清及選項 | PASS |
| 八題核對 | `0,1,2,3,0,1,2,3`，核對頁無分數 | 八題進入核對，未顯示總分 | PASS |
| 修改與重複確認 | 第 1 題改為 2，快速雙按確認，最終 14/24 | 顯示 14/24；是否只呼叫 scorer 一次由控制器測試另外驗證 | PASS |
| 雙會話及 MOCK 中斷 | 第二會話於核對頁輸入 `[DEMO_INTERRUPT]`，停止並清除；第一會話不受影響 | 第二會話顯示模擬暫停，無答案核對或分數；第一會話保持 14/24 | PASS |
| 同文字欄快速重送 | 鍵入明確合成回答後連按 Enter，不能跳兩題或提前計分 | 首次留第 1 題；重跑前進一次，該次 WebSocket 檢查捕捉到一個非空文字觸發。兩次均無分數或多跳；兩次送出各自送達的假設未獲證明 | PASS（無多跳／提前計分） |
| 取消、重設 | 取消後結束，重設可回到開始 | 顯示結束，重設後顯示開始 | PASS |
| 同 rerun 的中斷文字與確認 | 精確控制兩種 widget 觸發合併 | 瀏覽器操作未強制伺服器合併順序；由現有 AppTest 驗證先中斷，scorer 零呼叫 | NOT RUN（瀏覽器精確排程）；AppTest PASS |

[C01 合成結果](c01-result.png) · [C01 模擬中斷](c01-interruption.png)

C02 仍待人工審查及批准。T21／T22 正式規則驗收仍待核定；本紀錄只驗證 MOCK 接線。
