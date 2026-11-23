# Sentiment Analysis for Depression Detection

本機合成資料研究原型，涵蓋 WP01、WP03、WP04、WP05 的規則版本及 WP06。量表題幹是繁體中文待審譯稿，守門規則與中斷文案只用於測試流程。請只輸入虛構資料。

## 執行

在 repo 根目錄以 Python 3.12 執行。建議先建立及啟用虛擬環境。

```text
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Streamlit 預設只監聽本機。問卷狀態留在當前會話的記憶體。原型沒有 DB、模型服務或 sentiment 依賴。

## 合成展示

1. 開始並同意。第一題輸入「有時」，確認程式留在同題並請求澄清。選「完全沒有」。
2. 依序選其餘七題，組成 `0, 1, 2, 3, 0, 1, 2, 3`。核對頁只有暫存答案。
3. 修改第一題為「超過一半的日子」。確認八題後應顯示 `14 / 24`。
4. 重新開始，於活動狀態提交 `[DEMO_INTERRUPT]`（模擬中斷）或 `[DEMO_REVIEW]`（模擬覆核）。畫面轉入暫停並清除問卷。兩個標記只用於展示安全中斷的接線。

## 規格

- [架構與模組介面](architecture.md)
- [需求與驗收矩陣](requirements.md)
- [規則 NLU 合約](nlp_contract.md)
- [合成原型驗收與截圖](docs/verification/wp01-wp06-synthetic.md)

正式題幹、目標語言、Guard 規則及支援文案須由團隊與相關審閱者核定。原型結果只支持合成情境中的軟體行為驗證。
