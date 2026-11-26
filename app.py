"""Natural conversation entry point; questionnaire_app.py retains the baseline UI."""

import os
from dataclasses import replace
from localization import translate, ITEMS_EN, OPTIONS_EN, OPENING_EN
from conversation import OPENING
from bilingual_provider import BilingualConversationProvider

import streamlit as st

from conversation import (
    ITEMS,
    OPTIONS,
    chat_turn,
    confirm_review,
    new_conversation,
    open_review,
    ready,
    retry_turn,
)

st.set_page_config(
    page_title="Mood conversation · Group T", page_icon="💬", layout="centered"
)
if "ui_language" not in st.session_state:
    st.session_state.ui_language = "zh"
with st.sidebar:
    st.selectbox(
        "Language",
        ("zh", "en"),
        format_func=lambda x: "繁體中文" if x == "zh" else "English",
        key="ui_language",
    )
lang = st.session_state.ui_language


def tr(text):
    return translate(text, lang)


items = ITEMS_EN if lang == "en" else ITEMS
options = OPTIONS_EN if lang == "en" else OPTIONS


def fresh():
    state = new_conversation()
    if lang == "en":
        state = replace(
            state,
            messages=({"role": "assistant", "content": OPENING_EN, "turn_id": 0},),
        )
    return state


if "conversation" not in st.session_state:
    st.session_state.conversation = fresh()
if "chat_consent" not in st.session_state:
    st.session_state.chat_consent = False


def clear_conversation():
    st.session_state.conversation = fresh()
    st.session_state.chat_consent = False
    for key in list(st.session_state):
        if key.startswith(("review-", "chat-message-")):
            del st.session_state[key]


with st.sidebar:
    st.header(tr("心情對話"))
    st.caption(tr("Group T · PHQ-8 對話研究原型"))
    st.caption("Sentiment Analysis for Depression Detection")
    if st.button(tr("清除對話並重新開始"), use_container_width=True):
        clear_conversation()
        st.rerun()
    st.divider()
    st.write(tr("聊聊近況，最後一起核對"))
    st.caption(
        tr("你可以一次說幾件事，也可以隨時更正。AI 整理症狀頻率，確認後才計分。")
    )
    with st.expander(tr("連線設定")):
        st.text_input(
            "API Base URL",
            value=os.getenv("FYP_API_BASE", "https://car.cheng-x.online/v1"),
            key="chat_api_base",
        )
        st.text_input(
            tr("API key（只保留於本次頁面）"), type="password", key="chat_api_key"
        )
        st.caption(tr("模型：gpt-6.1-terra；身分由第三方服務回報。"))
        st.button(
            tr("清除頁面密鑰"),
            on_click=lambda: st.session_state.update(chat_api_key=""),
        )
    configured = bool(
        st.session_state.get("chat_api_key")
        or os.getenv("FYP_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    st.caption(
        tr("連線設定已提供") if configured else tr("尚未設定 API key，請展開連線設定。")
    )
    st.caption(
        tr("研究限制：安全中斷仍是 mock；只測試虛構案例，不能提供診斷或危機評估。")
    )

st.title(tr("從最近的生活聊起"))
st.caption(tr("不用逐題填表。用自己的方式說，最後再確認我整理得對不對。"))

if not st.session_state.chat_consent:
    st.info(
        tr(
            "這是研究展示，請使用虛構人物與情境。對話會暫存在本次頁面記憶體，並傳送至側欄所列的第三方 AI 端點作理解與回覆。"
        )
    )
    st.caption(tr("對話可清除；程式不把聊天內容寫入檔案。分數只是問卷摘要。"))
    if st.button(tr("開始虛構對話"), type="primary", disabled=not configured):
        st.session_state.chat_consent = True
        st.rerun()
    if not configured:
        st.warning(
            tr("需要先在側欄提供 API key，或用 scripts/serve_connected.py 啟動。")
        )
    st.stop()

state = st.session_state.conversation
if len(state.messages) == 1:
    opening = OPENING_EN if lang == "en" else OPENING
    state = replace(
        state, messages=({"role": "assistant", "content": opening, "turn_id": 0},)
    )
    st.session_state.conversation = state
elif state.messages:
    st.caption(
        "Earlier messages and source quotes remain in their original language. New replies use your selected language."
        if lang == "en"
        else "舊訊息和來源引句保留原文；之後的回覆會使用你選擇的語言。"
    )
for message in state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if state.phase == "PAUSED":
    st.warning(tr(state.error))
    st.stop()
if state.phase == "RESULT":
    st.success(tr("已按你核對的八項頻率完成加總。"))
    st.metric(tr("PHQ-8 問卷總分"), f"{state.result.total} / 24")
    st.caption(tr("這不是診斷，也不代表已排除任何風險。如需修改，請清除並重新開始。"))
    st.stop()

count = sum(u["frequency"] is not None for u in state.candidates.values())
with st.sidebar:
    st.progress(
        count / 8,
        text=(
            f"{count} / 8 frequencies collected"
            if lang == "en"
            else f"已整理 {count} / 8 項頻率"
        ),
    )
    with st.expander(tr("查看目前整理")):
        for i, label in enumerate(items, 1):
            u = state.candidates.get(i)
            st.write(
                f"{label}: {options[u['frequency']] if u and u['frequency'] is not None else tr('還需要了解')}"
            )
    if state.sentiment != "unclear":
        st.caption(
            (
                f"Latest sentiment: {state.sentiment} (not used for scoring)"
                if lang == "en"
                else f"最近一句情緒：{state.sentiment}（不參與計分）"
            )
        )


def provider():
    return BilingualConversationProvider(
        language=lang,
        key=st.session_state.get("chat_api_key") or None,
        base_url=st.session_state.chat_api_base,
    )


def process(text=None, retry=False):
    with st.spinner(tr("正在理解你的回覆，通常需要約 10–25 秒…")):
        try:
            engine = provider()
            st.session_state.conversation = (
                retry_turn(state, engine) if retry else chat_turn(state, text, engine)
            )
        except Exception:
            st.error(tr("未能建立連線，請檢查側欄的 API key 和 Base URL。"))
            return
    st.rerun()


if state.error:
    st.warning(tr(state.error))
    st.caption(tr("錯誤類型：") + state.meta.get("failure_type", "unknown"))
    if st.button(tr("重試上一句")):
        process(retry=True)

if state.phase == "REVIEW":
    st.subheader(tr("這是我從對話整理的內容"))
    st.write(tr("請核對過去兩星期的頻率；有誤可直接改選項，也可以繼續打字更正。"))
    values = {}
    with st.form(f"review-{state.session_id}-{state.revision}"):
        for i, label in enumerate(items, 1):
            u = state.candidates[i]
            st.markdown(f"**{label}**")
            st.caption(u["summary"])
            st.caption(
                ("Source: “" if lang == "en" else "對話依據：「")
                + u["quote"]
                + ("”" if lang == "en" else "」")
            )
            values[i] = st.selectbox(
                (f"{label}: frequency" if lang == "en" else f"{label}的頻率"),
                range(4),
                format_func=lambda x: options[x],
                index=u["frequency"],
                key=f"review-{state.revision}-{i}",
            )
        consent = st.checkbox(tr("我已核對八項內容，確認這些頻率符合這個虛構情境。"))
        submit = st.form_submit_button(tr("確認並查看分數"), type="primary")
    if submit:
        if not consent:
            st.warning(tr("請先核對並勾選確認，才會計算分數。"))
        else:
            st.session_state.conversation = confirm_review(
                state, values, expected_revision=state.revision, consent=consent
            )
            st.rerun()
elif ready(state):
    if st.button(tr("核對整理內容"), type="primary"):
        st.session_state.conversation = open_review(state)
        st.rerun()
else:
    st.caption(tr("可以繼續聊，也可以說「還需要了解什麼？」。資料不足時不會猜分數。"))

text = st.chat_input(
    tr("描述虛構人物的近況，或更正之前的內容…"),
    max_chars=2000,
    key=f"chat-message-{state.session_id}-{state.revision}",
    disabled=bool(state.error),
)
if text:
    with st.chat_message("user"):
        st.write(text)
    process(text)
