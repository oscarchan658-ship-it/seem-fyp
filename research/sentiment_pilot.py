"""Bilingual authored diagnostic examples, never a public benchmark replacement."""

PAIRS = {
    "positive": [
        ("I am happy with how today went.", "我對今天的經歷感到開心。"),
        ("That was wonderful news and I feel delighted.", "那是很棒的消息，我很高興。"),
        (
            "I really enjoyed spending time with my friends.",
            "我很享受和朋友相處的時間。",
        ),
        ("I feel hopeful about the coming week.", "我對下星期充滿希望。"),
        ("I am grateful for the support I received.", "我很感激收到的支持。"),
        (
            "Finishing the task made me proud and pleased.",
            "完成工作令我感到自豪和滿足。",
        ),
        (
            "The conversation was encouraging and reassuring.",
            "這次談話令人鼓舞，也讓我安心。",
        ),
        ("I loved the quiet walk this morning.", "我很喜歡今早那次寧靜的散步。"),
    ],
    "negative": [
        ("I feel miserable and upset today.", "我今天覺得很難受和不開心。"),
        ("The result was disappointing and frustrating.", "這個結果令人失望和沮喪。"),
        ("I hated the way that conversation ended.", "我很討厭那次談話的結局。"),
        ("I am worried and unhappy about tomorrow.", "我對明天感到擔心和不快樂。"),
        ("I feel lonely and sad tonight.", "今晚我覺得孤單和難過。"),
        ("That comment hurt me and made me angry.", "那句話傷害了我，也令我憤怒。"),
        ("I am not happy with what happened.", "我對發生的事情並不開心。"),
        (
            "I regret the decision and feel awful about it.",
            "我後悔這個決定，感覺很糟。",
        ),
    ],
    "neutral": [
        ("I slept for six hours last night.", "我昨晚睡了六小時。"),
        ("The appointment is scheduled for Thursday.", "預約安排在星期四。"),
        ("I recorded my answers on the form.", "我把答案記錄在表格上。"),
        (
            "During the past two weeks, this occurred on four days.",
            "在過去兩週，這情況出現了四天。",
        ),
        (
            "I ate lunch at twelve and returned to work.",
            "我十二時吃午餐，然後回去工作。",
        ),
        ("The questionnaire contains eight items.", "這份問卷有八題。"),
        ("I woke up twice during the night.", "我在夜裏醒了兩次。"),
        (
            "My energy level was recorded each evening.",
            "我每天晚上記錄自己的精力水平。",
        ),
    ],
}


def cases():
    return [
        dict(
            case_id=f"S-{label}-{i}-{lang}",
            pair_id=f"{label}-{i}",
            language=lang,
            text=pair[j],
            expected=label,
            source="AI-authored unblinded diagnostic; no independent human gold",
        )
        for label, pairs in PAIRS.items()
        for i, pair in enumerate(pairs, 1)
        for j, lang in enumerate(("en", "zh-Hant"))
    ]
