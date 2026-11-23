# 需求追蹤矩陣與驗收測試

專案 **Sentiment Analysis for Depression Detection**。範圍 WP01／03／04／05／06。來源為 Master Plan V3.1（本機原檔 `FYP_Research_and_Implementation_Master_Plan_V3_1.docx`） 與本次使用者約束。模組與資料定義見 [architecture.md](architecture.md)，工作次序見 [實作計劃](docs/superpowers/plans/2026-11-23-fyp-systems-integration.md)。

T01–T24 沿用 V3.1 §V-B 類別及順序。T25 起為新增驗收。測試以虛構輸入、本地規則或明確標記的測試替身執行。實測及待驗收項目見[合成原型驗收紀錄](docs/verification/wp01-wp06-synthetic.md)。

## 需求追蹤矩陣

| ID | 需求 | WP／落點 | 來源 | 測試 | 狀態 | 證據 |
|---|---|---|---|---|---|---|
| FR-01 | 八項唯一、完整而明確確認的 0–3 整數才可加總及分類。 | WP03 `phq8_engine.py`、WP04 `controller.py` | §I-A、IV-B/C、WP03、使用者約束 | T01–T06、T19–T20、T25 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| FR-02 | 缺答、拒答或未確認維持無結果，缺答與合法 0 分可區分。 | `phq8_engine.py`、`controller.py`、`rule_nlu.py` | §IV-B/C、WP03/05、使用者約束 | T01、T05、T11–T12、T19、T24 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| FR-03 | 同意後逐題作答。只有合法事件可轉移，拒絕及取消清空。 | WP04 `controller.py` | §IV-C、WP04 | T08、T17、T18、T26 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| FR-04 | 每回合只寫入目標題，缺少過去兩週證據、模糊、矛盾或非法結構時澄清。 | WP01／04／05 `schemas.py`、`controller.py`、`rule_nlu.py` | §IV-B/C、WP01/05 | T09–T16、T24、T27、T35 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| FR-05 | 八題完整時批次核對。編輯、取消編輯、重跑或重送維持版本一致，只按最新已確認答案評分。 | `controller.py`、`app.py` | §IV-C/E、WP03/04/06，版本守衛為提案 | T06–T07、T18–T20、T28 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| FR-06 | Guard 獨立於 sentiment，所有活動狀態的自由文字先過 Guard。中斷優先於 NLU、分數與正常轉移。 | WP04／06 `safety_guard.py`、控制器及 UI | §IV-B/C/E、§XII D04、使用者約束 | T21–T23、T29、T36 | Partial | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| FR-07 | NLU 失效回到同題選項。Guard 失效或 `review` 阻斷，提供對應的固定畫面。 | `controller.py`、`app.py`、`safety_guard.py` | §IV-E、WP06，失效及 review 語意為提案 | T24、T29 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| FR-08 | Sentiment 缺席、與症狀不一致或輸出改變時，候選、確認及計分維持相同。 | `controller.py`、`app.py` | §I、IV-B/C、使用者約束 | T30 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| NFR-01 | 保留核准題目。畫面標示研究原型，分數呈現為篩查／症狀程度。使用已審核或標記的測試文案。 | `app.py` | §I-C、§IV-E、§X、使用者約束 | T31 | Partial | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| NFR-02 | 本地以 Python、pytest、Streamlit 重現。只用合成資料，不依賴 DB、外部模型或真實病患資料。 | `app.py`、`tests/test_app.py` | §IV-B/E、WP06、§XI、使用者約束 | T24、T31–T33 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| NFR-03 | 自由文字只在事件處理所需期間使用。會話隔離，取消／中斷／重設清除問卷資料，追蹤資料排除原始文字。 | `schemas.py`、`controller.py`、`app.py` | §IV-B/C/E，清除及隔離為提案 | T08、T23、T32 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |
| NFR-04 | 每項必備需求可追到驗收案例，僅以實際執行的證據填報結果。 | `tests/test_traceability.py` | §V-A/B、WP01、使用者約束 | T34 | Verified (synthetic) | [驗收紀錄](docs/verification/wp01-wp06-synthetic.md) |

## 驗收案例

路徑為建議。若 repo 有既定測試名稱，沿用其對應位置，在 pytest 參數 ID 或測試說明中保留 T 編號。

| ID | 測試位置 | 操作與預期結果 |
|---|---|---|
| T01 | `tests/test_phq8.py` | 題號 1–8 均確認為 0，總分 0，屬 0–4。 |
| T02 | 同上 | 八題均確認為 3，總分 24，屬 20–24。 |
| T03 | 同上 | 確認分值 `[0,1,2,3,0,1,2,3]` → 12，屬 10–14。 |
| T04 | 同上 | 逐一在完整確認集合中代入 `-1, 4, 1.0, "1", true, null` 或題號 9，拒絕且無結果。 |
| T05 | 同上 | 只提交七個確認值，即使第八題有暫存 0，仍拒絕。 |
| T06 | 引擎＋控制器 | 八列含重複題號及一個缺題，引擎拒絕。重送已接受的答題事件，不覆寫下一題或增加題數。 |
| T07 | 控制器 | 以 T03 暫存，編輯第一題 0→2。舊核對版本的確認被拒絕。確認最新版本只計一次，結果 14。 |
| T08 | 控制器＋UI | 中途取消進入 END，清空暫存、確認、結果與輸入內容。舊事件無法產生結果。 |
| T09 | `tests/test_rule_nlu.py`＋控制器 | 對當前題以合成句表示「過去兩週有幾天出現此症狀」，候選 1，只進暫存。參數化驗證超過一半的日子為 2、幾乎每天為 3。 |
| T10 | 同上 | 只有上週，或無可靠時間證據時澄清。V3.2 互動 Provider 的明確頻率類別可繼承當前題目已指定的兩週時間窗。獨立 Rule baseline 的無時間輸入仍棄答。 |
| T11 | 同上 | 「過去兩週有時」頻率模糊，暫存不變，要求選頻率。 |
| T12 | 同上 | 「我不確定」拒答且留在原題，不補 0。 |
| T13 | 同上 | 明確表示「過去兩週完全沒有此症狀」，可暫存 0。刪除回答的時間窗後，只有當前問句已提供兩週時間窗的明確類別可暫存；兩者均無時間窗時澄清。 |
| T14 | 同上 | 雙重否定語義不明時留原題且產生澄清，無候選寫入。 |
| T15 | 同上 | 只描述其他題的症狀，任何題均不新增分值。 |
| T16 | 同上 | 同一答案同時宣稱「過去兩週完全沒有」與「幾乎每天」，即使 mock 信心高仍澄清。 |
| T17 | `tests/test_controller.py` | 未同意先送結構化答案，拒絕且無暫存。拒絕 consent → END。 |
| T18 | 同上 | 分別從 SCREENING 與 BATCH_REVIEW 進入編輯。合法修訂或取消編輯後回原狀態與題目。無效編輯保留原值，取消不提交修訂。 |
| T19 | 控制器＋UI | 完整八項暫存停在核對，無確認集合、分數或結果。核對渲染及重跑不等於確認。 |
| T20 | 控制器＋UI | 八項逐題呈現後，明確確認最新快照才顯示 T03 結果。第二次送同一事件時 scorer spy 呼叫數仍為 1。 |
| T21 | `tests/test_safety_guard.py` | 以受審的虛構規則案例檢查明確危機分到 interrupt。 |
| T22 | 同上 | 以同一規則集的虛構非危機慣用語檢查 normal。 |
| T23 | 控制器＋UI | 參數化六個活動狀態。送 Guard 判為 interrupt 的文字，包括非當前題及過期事件，均進 SAFETY_FLOW。NLU 和 scorer spy 呼叫數為 0，確定結果、問卷與原文字不出現在中斷畫面。嘗試繼續或確認均被拒絕，重設以新 ID 返回 START。 |
| T24 | 規則＋控制器＋UI | 注入 NLU 例外／格式錯誤，保留原題和既有暫存。結構化選項可恢復答題並完成，不連接真實模型。 |
| T25 | 引擎 | 合法確認集合覆蓋分段端點 0、4、5、9、10、14、15、19、20、24。傳入八個暫存值也拒絕。 |
| T26 | 控制器 | START 跳 RESULT、錯題提交、跨會話結構化事件、結果後嘗試編輯，均拒絕且不變更快照。 |
| T27 | Schema＋控制器 | 合法 JSON 往返保留 0 與 null。逐一測錯題、額外或缺失欄位、非整數分值及非有限 confidence，無暫存寫入。 |
| T28 | 控制器＋UI | 模擬 Streamlit 重跑與過期 widget 的答題及確認。合法事件只消費一次，讀取和重跑維持題號與答案。注入計分錯誤時留在核對，無部分結果。 |
| T29 | Guard＋控制器＋UI | 注入 review、非法回傳及例外。三者均阻斷，顯示對應固定回應。NLU／scorer 未呼叫，普通確認或重跑不解除中斷。 |
| T30 | 整合 | 同一合成腳本在沒有 sentiment、以及注入不同或故障的 sentiment 替身下，比對暫存、確認集與總分相同。若採無 adapter 設計，改驗證 app 不匯入或呼叫 sentiment，且在無模型環境執行相同流程。 |
| T31 | UI＋人工核對 | 核准題目逐字一致。Consent、結果、中斷畫面可辨識研究用途，無臨床安全或診斷宣稱。核對安全文案版本及審查狀態。 |
| T32 | UI＋人工核對 | 用兩個獨立會話及無個資的虛構字串驗證隔離。重設不帶入舊資料。掃描觀察到的應用日誌、輸出、截圖及專案資料目錄，查無該字串的留存或輸出。 |
| T33 | UI＋人工 demo | 乾淨環境執行 `python -m pytest -q` 和 `streamlit run app.py`。啟動後以合成資料從 consent 走到 result，能編輯並確認。記錄啟動方式、已使用的替身及實際截圖。 |
| T34 | 驗收紀錄審查 | 每項 FR/NFR 有至少一個案例。執行後逐案留存測試 ID、預期／實際、PASS／FAIL、日期、Git commit、Python／pytest／Streamlit 版本和環境。未跑標未執行。 |

| T35 | `tests/test_rule_nlu.py` | 句尾標點前空白不應令清楚頻率變成模糊；相同標點正規化亦不得接受模糊、缺時間窗及矛盾回覆。 |
| T36 | `tests/test_controller.py` | 跨會話 TEXT 在 Guard 前拒絕；同會話舊版本 TEXT 先過 Guard 再驗版本；結構化 SELECT 不呼叫文字 Guard。 |

Controller、Schema 和 Guard 案例可隨 WP04／05 分批完成。UI 測試建議以 Streamlit `AppTest` 驗證支援的操作，瀏覽器實際操作補足 widget 重跑、跨會話及截圖證據。若現有 Streamlit 版本或元件不支援該 API，在 repo baseline 確認後再定替代方式。[Streamlit AppTest 官方文件](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
