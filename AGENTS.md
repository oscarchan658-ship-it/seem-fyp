# Sentiment Analysis for Depression Detection

- 保留以上核准題目。以 Master Plan V3.1（本機原檔 `FYP_Research_and_Implementation_Master_Plan_V3_1.docx`）為歷史基線。先讀 [V3.2 交付現況](docs/verification/v32-delivery.md)、[架構與介面](architecture.md)及[需求與驗收](requirements.md)。新提案標記核定狀態，遇到來源衝突先記錄並澄清。
- Systems Engineering & Integration 負責 WP01、WP03、WP04、WP05 的規則／Mock、WP06 及相應驗收。進階 NLU、sentiment 訓練和資料集研究屬其他工作包。保持模型可替換，第一期以本地規則／Mock 驗收。
- 使用 Python、pytest、Streamlit。實作前先檢查 Git 根目錄、既有入口、測試、依賴與相關呼叫，沿用 repo 慣例。採 Ponytail full mode，寫最小完整改動，重要邏輯須有可執行測試。依實作計劃分批落實及驗收。
- 分數只來自用戶明確確認的八個唯一題目。只接受 0–3 嚴格整數。缺答、無法解析、未確認、重複題均無結果。Sentiment、NLU 信心及危機決策不得作為分值或補答來源。
- 所有活動狀態的自由文字都由獨立 Guard 先檢查。安全中斷必須阻止 NLU、一般轉移及計分。按照已確認的 Guard 契約處理 review、失效、會話清理與重設。使用有版本的審查文案。研究原型不得宣稱診斷能力或臨床安全。
- 只用虛構測試、資料與展示內容。避免記錄或持久化原始訊息，不把資料送往第三方服務。保護各 Streamlit 會話及表單輸入。
- 把修改連到需求與測試 ID。實作完成後實跑相關 pytest、全套及必要 Streamlit 操作。依 §V-B 記錄實際輸出、狀態、日期、環境及 commit。沒有實測證據的項目標記未執行。Mock 必須明確標識。
