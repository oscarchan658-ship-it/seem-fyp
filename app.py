import streamlit as st

from controller import dispatch, new_session
from safety_guard import MOCK_VERSION
from schemas import Event

TITLE = "Sentiment Analysis for Depression Detection"
QUESTIONS = (
    "做事提不起興趣或感到無趣",
    "感到心情低落、沮喪或絕望",
    "難以入睡、睡不安穩或睡得太多",
    "感到疲倦或沒有活力",
    "食慾不振或吃得太多",
    "對自己感覺不好，覺得自己是失敗者或令自己或家人失望",
    "難以集中精神，例如閱讀或看電視時",
    "行動或說話慢得讓人察覺，或比平常更坐立不安、動來動去",
)
OPTIONS = ("完全沒有", "有幾天", "超過一半的日子", "幾乎每天")
SAFETY_COPY = {
    "safety_interrupt": "模擬中斷。已清除本次問卷，接下來只可結束或重新開始。",
    "safety_review": "模擬覆核。已清除本次問卷，接下來只可結束或重新開始。",
    "safety_unavailable": "測試守門模組未能回應。已清除本次問卷並暫停流程。",
}


def send(event: Event):
    outcome = dispatch(st.session_state.dialogue, event)
    st.session_state.dialogue = outcome.state
    if outcome.response_code != "rejected":
        st.session_state.response_code = outcome.response_code


def submit_text(event: Event, text_key: str):
    text = st.session_state.pop(text_key, None)
    if isinstance(text, str):
        send(
            Event(
                event.kind,
                event.session_id,
                event.expected_revision,
                item_id=event.item_id,
                text=text,
            )
        )


def queue_action(event: Event):
    # Streamlit can batch callbacks in widget order. Guard text before applying a button.
    if "pending_action" not in st.session_state:
        st.session_state.pending_action = event


st.set_page_config(page_title=TITLE)
if "dialogue" not in st.session_state:
    st.session_state.dialogue = new_session()
    st.session_state.response_code = ""
pending = st.session_state.pop("pending_action", None)
if pending is not None:
    send(pending)

state = st.session_state.dialogue
phase = state.phase
scope = f"{state.session_id}-{state.revision}"


def action(label, kind, *, item_id=None, value=None, primary=False):
    event = Event(kind, state.session_id, state.revision, item_id=item_id, value=value)
    st.button(
        label,
        key=f"{scope}-{kind}-{item_id}-{value}",
        on_click=queue_action,
        args=(event,),
        type="primary" if primary else "secondary",
    )


st.title(TITLE)
st.caption("本機研究原型 · 僅供合成案例 · 題目為待審譯稿 · 不提供診斷或危機評估")

if phase == "START":
    st.write("用虛構答案試行八題問卷。完成後可逐題核對，再確認計分。")
    action("開始", "START", primary=True)
elif phase == "CONSENT":
    st.subheader("同意使用虛構資料")
    st.write("請勿輸入個人資料或真實經歷。可隨時取消及清除本次問卷。")
    action("同意並開始", "ACCEPT", primary=True)
    action("不同意", "DECLINE")
elif phase in ("SCREENING", "CLARIFICATION", "EDIT_ANSWER"):
    item = state.item_id
    label = "修改" if phase == "EDIT_ANSWER" else ""
    st.subheader(f"{label}第 {item} 題 / 8")
    st.write(f"過去兩週，以下情形出現的頻率是？\n\n**{QUESTIONS[item - 1]}**")
    code = st.session_state.response_code
    if code == "nlu_unavailable":
        st.info("暫時無法解讀文字。請用下方選項回答本題。")
    elif code == "clarify":
        st.info("請確認過去兩週的頻率，或直接選擇下方選項。")
    for value, option in enumerate(OPTIONS):
        action(option, "SELECT", item_id=item, value=value)
    if phase == "EDIT_ANSWER":
        st.caption(f"原答案：{OPTIONS[state.provisional_answers[item]]}")
        action("取消修改", "CANCEL_EDIT")
    elif phase == "SCREENING" and state.provisional_answers:
        with st.expander("修改先前答案"):
            for answered in state.provisional_answers:
                action(f"修改第 {answered} 題", "EDIT", item_id=answered)
elif phase == "BATCH_REVIEW":
    st.subheader("核對八題答案")
    if st.session_state.response_code == "scoring_unavailable":
        st.error("暫未能計分。請核對答案或取消問卷。")
    for item, value in sorted(state.provisional_answers.items()):
        with st.container(border=True):
            st.write(f"第 {item} 題　{QUESTIONS[item - 1]}")
            st.write(OPTIONS[value])
            action(f"修改第 {item} 題", "EDIT", item_id=item)
    action("確認八題答案並計分", "CONFIRM", primary=True)
elif phase == "RESULT":
    st.subheader("合成案例篩查結果")
    st.metric("PHQ-8 總分", f"{state.result.total} / 24")
    st.write(f"症狀程度分段：{state.result.band}")
    action("重新開始", "RESET", primary=True)
elif phase == "SAFETY_FLOW":
    st.subheader("流程已暫停")
    st.warning(SAFETY_COPY[state.safety_state])
    st.caption(f"測試替身 {MOCK_VERSION} · 支援文案待審")
    action("重新開始", "RESET")
elif phase == "END":
    st.write("已結束本次問卷。")
    action("重新開始", "RESET", primary=True)

if phase != "END":
    action("取消問卷", "CANCEL")
if phase not in ("END", "RESULT", "SAFETY_FLOW"):
    if state.item_id is not None:
        st.caption("合成文字範例：過去兩週有幾天。")
    text_key = f"{scope}-TEXT"
    text_event = Event("TEXT", state.session_id, state.revision, item_id=state.item_id)
    st.chat_input(
        "輸入虛構文字",
        key=text_key,
        max_chars=500,
        on_submit=submit_text,
        args=(text_event, text_key),
    )
