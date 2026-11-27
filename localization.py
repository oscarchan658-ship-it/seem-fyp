"""UI copy shared by Chinese and English modes; original quotes stay unchanged."""

EN = {
    "心情對話": "Mood conversation",
    "Group T · PHQ-8 對話研究原型": "Group T · PHQ-8 conversation prototype",
    "清除對話並重新開始": "Clear conversation and start again",
    "聊聊近況，最後一起核對": "Talk first, review together at the end",
    "你可以一次說幾件事，也可以隨時更正。AI 整理症狀頻率，確認後才計分。": "Mention several things at once and correct them "
    "anytime. AI organizes symptom frequencies; scoring "
    "follows your confirmation.",
    "連線設定": "Connection settings",
    "API key（只保留於本次頁面）": "API key (this session only)",
    "模型：gpt-6.1-terra；身分由第三方服務回報。": "Model: gpt-6.1-terra; identity reported by the third-party "
    "gateway.",
    "清除頁面密鑰": "Clear session key",
    "連線設定已提供": "Connection settings provided",
    "尚未設定 API key，請展開連線設定。": "API key missing. Open Connection settings.",
    "研究限制：安全中斷仍是 mock；只測試虛構案例，不能提供診斷或危機評估。": "Research demo with fictional cases only. The "
    "safety guard is a mock, not a crisis detector. No "
    "diagnosis is provided.",
    "從最近的生活聊起": "Let's talk about recent life",
    "不用逐題填表。用自己的方式說，最後再確認我整理得對不對。": "Speak in your own words. We will review the summary "
    "together before scoring.",
    "這是研究展示，請使用虛構人物與情境。對話會暫存在本次頁面記憶體，並傳送至側欄所列的第三方 AI 端點作理解與回覆。": "Use fictional people and "
    "situations for this research "
    "demo. Conversation history "
    "stays in this session memory "
    "and is sent to the third-party "
    "AI endpoint shown in the "
    "sidebar for interpretation and "
    "replies.",
    "對話可清除；程式不把聊天內容寫入檔案。分數只是問卷摘要。": "You can clear the conversation. The app does not write "
    "chats to files. The score is a questionnaire summary.",
    "開始虛構對話": "Start fictional conversation",
    "需要先在側欄提供 API key，或用 scripts/serve_connected.py 啟動。": "Enter an API key in the sidebar or "
    "start with "
    "scripts/serve_connected.py.",
    "已按你核對的八項頻率完成加總。": "The eight frequencies you reviewed have been added together.",
    "PHQ-8 問卷總分": "PHQ-8 questionnaire total",
    "這不是診斷，也不代表已排除任何風險。如需修改，請清除並重新開始。": "This is not a diagnosis and does not rule out risk. To "
    "make changes, clear the conversation and start again.",
    "查看目前整理": "View current summary",
    "還需要了解": "Needs clarification",
    "正在理解你的回覆，通常需要約 10–25 秒…": "Interpreting your reply. This may take 10–25 seconds…",
    "未能建立連線，請檢查側欄的 API key 和 Base URL。": "Could not connect. Check the API key and Base URL in "
    "the sidebar.",
    "錯誤類型：": "Error type: ",
    "重試上一句": "Retry last message",
    "這是我從對話整理的內容": "Here is the summary of our conversation",
    "請核對過去兩星期的頻率；有誤可直接改選項，也可以繼續打字更正。": "Review the frequencies over the past two weeks. Change "
    "an option below, or continue chatting to correct the "
    "summary.",
    "我已核對八項內容，確認這些頻率符合這個虛構情境。": "I have reviewed all eight items and confirm these frequencies "
    "for this fictional situation.",
    "確認並查看分數": "Confirm and view score",
    "請先核對並勾選確認，才會計算分數。": "Review the items and check the confirmation box before scoring.",
    "核對整理內容": "Review summary",
    "可以繼續聊，也可以說「還需要了解什麼？」。資料不足時不會猜分數。": "Keep talking, or ask what else is needed. Missing "
    "information is not assigned a score.",
    "描述虛構人物的近況，或更正之前的內容…": "Describe a fictional situation, or correct an earlier detail…",
    "這段較長，請分成兩段傳送。": "This message is too long. Please split it into two parts.",
    "流程已暫停並清除本次對話。這是示範中斷，不是危機評估。": "The conversation has been paused and cleared. This is a "
    "demonstration interruption, not a crisis assessment.",
    "本次對話已到 40 回合上限。資料完整可核對計分；資料不足請重新開始。": "The 40-turn limit has been reached. Review and score a complete summary, or start again if information is missing.",
    "AI 暫時未能回覆，本次訊息尚未整理。請按「重試上一句」，或檢查側欄連線設定。": "AI could not reply. This message has not been "
    "processed. Retry it or check the connection "
    "settings.",
    "雙通道語氣與症狀對照觀察": "Dual-Channel Affect–Symptom Observation",
    "語氣極性與核對後兩週症狀頻率一致（低症狀負擔、非負面主導語氣）。": "Conversational affect aligns with low confirmed 14-day symptom frequencies.",
    "語氣與症狀出現落差（情境負向／短期壓力宣洩）：對話語氣偏負面，但核對後的兩週症狀總分較低。情緒極性不改變問卷計分。": "Affect–symptom divergence (situational negativity): negative conversational affect alongside low confirmed 14-day symptom frequencies. Sentiment never alters the PHQ-8 score.",
    "語氣與症狀出現落差（平淡／隱性生理表達）：對話語氣偏中性或正面，但核對後的兩週症狀頻率偏高。平淡語氣不等於低症狀負擔；總分完全依核對頻率計算。": "Affect–symptom divergence (masked/neutral presentation): predominantly neutral or positive wording alongside elevated confirmed 14-day symptom frequencies. Neutral tone does not imply low symptom burden; the score reflects confirmed frequencies only.",
    "語氣極性與核對後兩週症狀頻率一致（負向語氣與較高症狀頻率同時出現）。": "Conversational affect aligns with elevated confirmed 14-day symptom frequencies.",
    "對話語氣紀錄不足，僅顯示核對後的問卷總分。": "Insufficient unambiguous affect turns recorded; displaying confirmed questionnaire score only.",
    "雙通道觀察僅供研究對照，不屬於臨床診斷，亦絕不增減已確認的 0–24 分總和。": "Dual-channel observations are descriptive research summaries, not clinical diagnoses, and never modify the confirmed 0–24 score.",
}

ITEMS_EN = (
    "Reduced interest or pleasure",
    "Low mood or hopelessness",
    "Sleep difficulties",
    "Fatigue or low energy",
    "Appetite changes",
    "Low self-worth or guilt",
    "Difficulty concentrating",
    "Slowing down or restlessness",
)
OPTIONS_EN = (
    "Not at all",
    "Several days",
    "More than half the days",
    "Nearly every day",
)
OPENING_EN = "Hello. Thinking about the past two weeks, has anything been affecting your mood, sleep, or energy? Tell me in your own words; you do not need to answer a list of questions."


def translate(text, language):
    return EN.get(text, text) if language == "en" else text
