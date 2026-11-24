# WP05 規則 NLU 合約

`NLUProvider.predict(NluRequest)` 回傳 [架構所列 NLU object](architecture.md)。預設 RuleProvider 沿用 `rule_nlu.extract`，只讓明確目前題目的頻率類別繼承兩週時間窗。Controller 在同一題需要追問時傳入 `ClarificationContext`，無需保存原始文字。守門在 provider 前執行，`evidence_manager.evaluate_candidate` 依 schema、題號和硬規則驗證候選並回原因碼。

獨立合成規則版本 `synthetic-rule-zh-hant-v2` 支援繁體中文的明確兩週時間前綴和四個標準頻率類別；V2 區分一般不確定和否定不明。文字帶不明症狀、模糊、時間缺失、否定不明或衝突時，回傳 null 候選；用戶可在同題選擇明確頻率。綁定當前題目，無跨題推斷。數值及信心訊號無法繞過硬性條件。NLU 回傳只供暫存，八題仍須明確核對確認。

互動 `context-rule-zh-hant-v1` 在同題澄清時可辨識「Around five days」等作答的天數。頻率候選保持 null，流程要求澄清或手選。R1 的區間與約略答案規則待另行核定。結構化外部模型目前以 MOCK 傳輸測試，模型或服務不可用時須回報失敗或棄答。 [規格與研究操作](research/README.md)
