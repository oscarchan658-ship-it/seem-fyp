# WP05 規則 NLU 合約

`rule_nlu.extract(item_id, text)` 回傳 [架構所列 NLU object](architecture.md)。`schemas.validate_nlu(payload, expected_item)` 拒絕錯題、未知／缺失欄位和非法值。Controller 使用 `decide_candidate` 檢查時間窗、症狀語意、否定及歧義。後續模型替換可使用同一接口。守門在外部候選解析之前執行。

合成規則版本 `synthetic-rule-zh-hant-v1` 只支援繁體中文的明確兩週時間前綴和四個標準頻率類別。文字帶不明症狀、模糊、時間缺失、否定不明或衝突時，回傳 null 候選；用戶可在同題選擇明確頻率。綁定當前題目，無跨題推斷。數值及信心訊號無法繞過硬性條件。NLU 回傳只供暫存，八題仍須明確核對確認。
