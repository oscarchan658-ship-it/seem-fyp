"""Benchmark suites and disjoint ML training corpora for the Unified S1 Dual-Channel study.

Provenance notice:
- TweetEval splits live under ``data/tweeteval/`` (public benchmark; Barbieri et al., 2020).
- All cases constructed in this module are author-designed bilingual diagnostic benchmarks
  and controlled simulation cohorts for evaluating affect-symptom divergence, selective
  abstention, partial-observation triage, and chatbot state-machine invariants. They are NOT
  clinical patient records and must never be described as clinical validation data.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
import numpy as np


def _norm_sha256(text: str) -> str:
    return hashlib.sha256(
        " ".join(text.strip().casefold().split()).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class E1BScreeningCase:
    case_id: str
    language: str
    quadrant: str
    text: str
    gold_polarity: str
    profile_phq8_total: int

    @property
    def elevated_phq8(self) -> bool:
        return self.profile_phq8_total >= 10


def build_e1b_screening_cases() -> list[E1BScreeningCase]:
    """Return 48 bilingual screening turns (24 EN + 24 ZH; 12 per quadrant)."""
    raw: list[tuple[str, str, str, str, int]] = [
        # --- Quadrant 1: congruent_low (6 EN, 6 ZH; positive/neutral affect, PHQ-8 < 10) ---
        (
            "en",
            "congruent_low",
            "Past two weeks have been pretty steady overall; I've slept well and enjoyed cooking dinner with roommates.",
            "positive",
            1,
        ),
        (
            "en",
            "congruent_low",
            "Nothing unusual lately—my appetite is normal, energy is fine, and focus in lectures has been solid.",
            "neutral",
            2,
        ),
        (
            "en",
            "congruent_low",
            "I felt genuinely refreshed after hiking last weekend, and my mood and sleep over the fortnight were great.",
            "positive",
            0,
        ),
        (
            "en",
            "congruent_low",
            "Over the last 14 days I had maybe two tired evenings after lab, otherwise routine schedule and calm mood.",
            "neutral",
            3,
        ),
        (
            "en",
            "congruent_low",
            "I'm grateful my project rhythm is back on track; reading, eating, and sleeping have all felt comfortable.",
            "positive",
            1,
        ),
        (
            "en",
            "congruent_low",
            "Standard two weeks for me: zero trouble concentrating, regular meals, and normal pace at work.",
            "neutral",
            0,
        ),
        (
            "zh",
            "congruent_low",
            "過去兩星期生活幾規律，夜晚一覺瞓到天光，放假仲好開心約咗朋友去行山。",
            "positive",
            1,
        ),
        (
            "zh",
            "congruent_low",
            "呢十四日冇咩特別狀況，胃口同平時一樣，返學聽書精神都好正常。",
            "neutral",
            1,
        ),
        (
            "zh",
            "congruent_low",
            "最近心情幾輕鬆愉快，做運動同睇書都好有興趣，身體狀態好理想。",
            "positive",
            0,
        ),
        (
            "zh",
            "congruent_low",
            "呢兩個禮拜只係有兩日開會比較攰少少，其餘時間睡眠、食慾同專注力都完全冇問題。",
            "neutral",
            2,
        ),
        (
            "zh",
            "congruent_low",
            "好滿意最近嘅作息節奏，每日食得落瞓得著，同屋企人傾偈都好開心。",
            "positive",
            0,
        ),
        (
            "zh",
            "congruent_low",
            "過去兩週整體平穩，冇自責或者低落，做嘢節奏同往常差不多。",
            "neutral",
            2,
        ),
        # --- Quadrant 2: situational_distress (6 EN, 6 ZH; negative affect, PHQ-8 < 10) ---
        (
            "en",
            "situational_distress",
            "I am furious that the bus soaked me in pouring rain this morning! Aside from today's annoyance, my past two weeks of sleep and mood were fine.",
            "negative",
            2,
        ),
        (
            "en",
            "situational_distress",
            "Honestly super annoyed because my laptop charger died right before printing slides, though over the two-week window my energy and appetite stayed normal.",
            "negative",
            3,
        ),
        (
            "en",
            "situational_distress",
            "Today's group meeting was frustrating and chaotic, yet looking across the past 14 days I've still enjoyed hobbies and slept well except two nights.",
            "negative",
            4,
        ),
        (
            "en",
            "situational_distress",
            "I hate how noisy the construction upstairs was this afternoon—so irritating! My actual two-week focus, eating, and mood have been totally okay though.",
            "negative",
            3,
        ),
        (
            "en",
            "situational_distress",
            "Really upset about losing my umbrella on the train tonight, even though the last two weeks were otherwise calm with good sleep and steady motivation.",
            "negative",
            2,
        ),
        (
            "en",
            "situational_distress",
            "That surprise quiz grading rubric felt unfair and pissed me off today, but I haven't had persistent low mood or fatigue over these two weeks.",
            "negative",
            5,
        ),
        (
            "zh",
            "situational_distress",
            "今日搭巴士塞車塞咗成個鐘真係激死我好忟憎！不過講返過去兩星期，我睡眠、胃口同平時心情其實都好正常。",
            "negative",
            2,
        ),
        (
            "zh",
            "situational_distress",
            "頭先唔小心倒瀉杯咖啡整污糟份筆記，超煩躁！但呢十四日整體精神同做嘢興趣都冇受影響。",
            "negative",
            3,
        ),
        (
            "zh",
            "situational_distress",
            "組員臨時改時間令我覺得好無奈同唔開心，不過計返成個兩星期我只係兩晚夜瞓，其他身心狀況都好穩定。",
            "negative",
            4,
        ),
        (
            "zh",
            "situational_distress",
            "今日落大雨仲要漏低八達通真係好倒楣好煩！但過去兩個禮拜我食得瞓得，專注力亦冇問題。",
            "negative",
            1,
        ),
        (
            "zh",
            "situational_distress",
            "隔離屋裝修嘈到我頭先好火滾，不過呢兩星期以嚟心情大致平穩，放假去打波都好投入。",
            "negative",
            3,
        ),
        (
            "zh",
            "situational_distress",
            "今朝電腦突然更新搞到我要重寫一頁表，好討厭，但過去十四日並冇持續低落或者疲倦。",
            "negative",
            4,
        ),
        # --- Quadrant 3: masked_somatic (6 EN, 6 ZH; neutral/matter-of-fact tone, PHQ-8 >= 10) ---
        (
            "en",
            "masked_somatic",
            "Logging the past 14 days factually: sleep averaged four hours on 12 nights, meal intake dropped on 10 days, and reading focus lapsed on 9 days.",
            "neutral",
            14,
        ),
        (
            "en",
            "masked_somatic",
            "For the two-week record, physical energy remained low on 13 days, tasks took roughly twice my usual pace on 8 days, and hobbies occurred on 1 day.",
            "neutral",
            15,
        ),
        (
            "en",
            "masked_somatic",
            "To answer by count: waking before 4 a.m. happened 11 times, daytime fatigue 12 days, reduced appetite 9 days, and concentration drift 8 days.",
            "neutral",
            13,
        ),
        (
            "en",
            "masked_somatic",
            "Across these 14 days I skipped breakfast and lunch on 11 days, needed afternoon rest on 12 days, and stopped usual weekend activities on 10 days.",
            "neutral",
            12,
        ),
        (
            "en",
            "masked_somatic",
            "Schedule summary for the fortnight: fragmented sleep on 13 nights, low stamina on 11 days, slow speech noted on 7 days, concentration loss on 9 days.",
            "neutral",
            14,
        ),
        (
            "en",
            "masked_somatic",
            "Reporting the numbers plainly: 10 days with minimal interest in usual routines, 12 days of low energy, 9 nights of early awakening, 8 days of poor focus.",
            "neutral",
            13,
        ),
        (
            "zh",
            "masked_somatic",
            "按過去十四日紀錄回答：有十二晚凌晨三點醒咗再瞓唔返，十一日體力偏低，九日食量比平時少一半，八日睇文件難以集中。",
            "neutral",
            14,
        ),
        (
            "zh",
            "masked_somatic",
            "客觀計返呢兩星期日數：十三日下晝都冇乜精神，十日對平時活動提唔起興趣，八日做嘢動作明顯比以往慢。",
            "neutral",
            13,
        ),
        (
            "zh",
            "masked_somatic",
            "照實報返過去兩週情況：十一晚入睡超過一個鐘，十日無胃口食正餐，九日溫書集中唔到，十二日覺得身體疲倦。",
            "neutral",
            15,
        ),
        (
            "zh",
            "masked_somatic",
            "呢十四日嘅作息數字係：十二晚睡眠斷斷續續，十日全日缺乏活力，八日完全冇掂過平時嘅興趣，七日坐唔定。",
            "neutral",
            12,
        ),
        (
            "zh",
            "masked_somatic",
            "單純講返過去兩星期頻率：十一日食慾減少，十二日早醒兼日頭無力，九日開會跟唔上內容，整體只係如實記錄。",
            "neutral",
            13,
        ),
        (
            "zh",
            "masked_somatic",
            "過去兩星期統計：十日對日常事務少咗興趣，十三日體力消耗得好快，九晚睡眠不足四小時，八日難以專心閱讀。",
            "neutral",
            14,
        ),
        # --- Quadrant 4: congruent_elevated (6 EN, 6 ZH; negative affect + PHQ-8 >= 10) ---
        (
            "en",
            "congruent_elevated",
            "These past two weeks have felt exhausting and bleak—nearly every day I feel hopeless, can barely sleep, and blame myself for letting everyone down.",
            "negative",
            19,
        ),
        (
            "en",
            "congruent_elevated",
            "I feel drained and miserable almost every single day over the fortnight; nothing brings joy anymore and my focus has completely fallen apart.",
            "negative",
            18,
        ),
        (
            "en",
            "congruent_elevated",
            "It has been an awful two weeks: crying and feeling down on 12 days, tossing awake almost every night, and feeling like a total failure.",
            "negative",
            17,
        ),
        (
            "en",
            "congruent_elevated",
            "Over the past 14 days I've felt dreadful and empty on 11 days, lost my appetite most days, and feel guilty that I can barely get through simple work.",
            "negative",
            16,
        ),
        (
            "en",
            "congruent_elevated",
            "Everything over these two weeks feels heavy and discouraging; I'm worn out nearly every day, restless in my seat, and uninterested in seeing anyone.",
            "negative",
            15,
        ),
        (
            "en",
            "congruent_elevated",
            "I hate how awful these two weeks have been—13 days of gloomy mood, constant fatigue, terrible sleep, and feeling disappointed in myself.",
            "negative",
            18,
        ),
        (
            "zh",
            "congruent_elevated",
            "過去兩星期真係好難捱好絕望，幾乎日日都心情低落、夜晚眼光光瞓唔著，仲成日怪責自己做得唔夠好。",
            "negative",
            19,
        ),
        (
            "zh",
            "congruent_elevated",
            "呢十四日覺得好痛苦好無力，差不多每日都提唔起勁做任何嘢，食唔落飯，連睇幾行字都集中唔到精神。",
            "negative",
            18,
        ),
        (
            "zh",
            "congruent_elevated",
            "最近兩個禮拜心情差到極點，有十二日都好沮喪想喊，日頭攰到郁唔到，覺得自己好失敗連累屋企人。",
            "negative",
            17,
        ),
        (
            "zh",
            "congruent_elevated",
            "過去兩週真係好煎熬，十一日都食慾不振同埋失眠，心入面好壓抑好難過，做乜都完全冇晒樂趣。",
            "negative",
            16,
        ),
        (
            "zh",
            "congruent_elevated",
            "呢兩個星期過得好灰暗好辛苦，幾乎每日都坐立不安、精神散渙，覺得自己好似乜都做唔掂咁。",
            "negative",
            15,
        ),
        (
            "zh",
            "congruent_elevated",
            "呢十四日日日都好攰好頹喪，超過十日瞓得極差又冇胃口，成個人好消沉好討厭而家嘅狀態。",
            "negative",
            18,
        ),
    ]
    cases = [
        E1BScreeningCase(
            case_id=f"E1B_{idx:02d}",
            language=lang,
            quadrant=quad,
            text=text,
            gold_polarity=pol,
            profile_phq8_total=tot,
        )
        for idx, (lang, quad, text, pol, tot) in enumerate(raw, start=1)
    ]
    assert len(cases) == 48
    assert len({_norm_sha256(c.text) for c in cases}) == 48
    return cases


@dataclass(frozen=True)
class E2SymptomCase:
    case_id: str
    language: str
    category: str
    item_id: int
    assistant_prompt: str
    user_text: str
    should_abstain: bool
    gold_frequency: int | None


_ITEM_PROMPTS_EN = {
    1: "Over the past two weeks, how often have you had little interest or pleasure in doing things?",
    2: "Over the past two weeks, how often have you felt down, depressed, or hopeless?",
    3: "Over the past two weeks, how often have you had trouble falling or staying asleep, or sleeping too much?",
    4: "Over the past two weeks, how often have you felt tired or had little energy?",
    5: "Over the past two weeks, how often have you had poor appetite or overeating?",
    6: "Over the past two weeks, how often have you felt bad about yourself or that you are a failure?",
    7: "Over the past two weeks, how often have you had trouble concentrating on things such as reading or work?",
    8: "Over the past two weeks, how often have you moved or spoken noticeably slowly, or felt fidgety and restless?",
}

_ITEM_PROMPTS_ZH = {
    1: "以過去兩星期來說，你有幾常覺得做事情提不起興趣或沒有樂趣？",
    2: "以過去兩星期來說，你有幾常覺得心情低落、沮喪或絕望？",
    3: "以過去兩星期來說，你有幾常出現入睡困難、易醒或睡得太多等睡眠困擾？",
    4: "以過去兩星期來說，你有幾常覺得疲倦或缺乏活力？",
    5: "以過去兩星期來說，你有幾常覺得食慾不振或暴飲暴食？",
    6: "以過去兩星期來說，你有幾常覺得自己不好、自責或覺得自己失敗？",
    7: "以過去兩星期來說，你有幾常在閱讀或做事時難以集中精神？",
    8: "以過去兩星期來說，你有幾常覺得動作或說話變慢，或者坐立不安？",
}


def build_e2_symptom_cases() -> list[E2SymptomCase]:
    """Return 64 bilingual conversational turns (32 resolvable + 32 must-abstain)."""
    rows: list[tuple[str, str, int, str, bool, int | None]] = [
        # === R1_canonical (4 EN + 4 ZH, resolvable) ===
        (
            "en",
            "R1_canonical",
            1,
            "In the past two weeks, not at all—I've still enjoyed my usual music and cooking.",
            False,
            0,
        ),
        (
            "en",
            "R1_canonical",
            2,
            "Over the past two weeks I felt down on several days when deadlines piled up.",
            False,
            1,
        ),
        (
            "en",
            "R1_canonical",
            3,
            "More than half the days in the past two weeks I kept waking up in the middle of the night.",
            False,
            2,
        ),
        (
            "en",
            "R1_canonical",
            4,
            "Nearly every day during the past two weeks I felt drained of energy by noon.",
            False,
            3,
        ),
        (
            "zh",
            "R1_canonical",
            5,
            "過去兩星期完全沒有食慾改變，三餐食量都好正常。",
            False,
            0,
        ),
        (
            "zh",
            "R1_canonical",
            6,
            "過去兩星期有幾天會自責覺得自己做得唔夠好。",
            False,
            1,
        ),
        (
            "zh",
            "R1_canonical",
            7,
            "過去兩星期超過一半的日子睇書都難以集中精神。",
            False,
            2,
        ),
        (
            "zh",
            "R1_canonical",
            8,
            "過去兩星期幾乎每天都覺得坐立不安、靜唔落嚟。",
            False,
            3,
        ),
        # === R2_exact_days (4 EN + 4 ZH, natural embedded day counts -> R1 mapping) ===
        (
            "en",
            "R2_exact_days",
            1,
            "Counting across these past two weeks, there was only 1 day when I didn't feel like doing hobbies.",
            False,
            0,
        ),
        (
            "en",
            "R2_exact_days",
            3,
            "Over this two-week window I woke up at 3 a.m. and couldn't sleep again on 9 nights.",
            False,
            2,
        ),
        (
            "en",
            "R2_exact_days",
            5,
            "During the past 14 days I skipped dinner from low appetite on 4 days.",
            False,
            1,
        ),
        (
            "en",
            "R2_exact_days",
            7,
            "Across the last two weeks my focus drifted badly during reading on 13 days.",
            False,
            3,
        ),
        (
            "zh",
            "R2_exact_days",
            2,
            "計返過去十四日入面，我只係有零日覺得沮喪，心情一直幾穩陣。",
            False,
            0,
        ),
        (
            "zh",
            "R2_exact_days",
            4,
            "呢兩個星期裏面大概有五日下晝覺得特別疲倦冇力。",
            False,
            1,
        ),
        (
            "zh",
            "R2_exact_days",
            6,
            "過去兩星期我有九日都忍唔住怪責自己拖慢進度。",
            False,
            2,
        ),
        (
            "zh",
            "R2_exact_days",
            8,
            "呢十四日入面足足有十二日我都行得好慢、講嘢冇氣力。",
            False,
            3,
        ),
        # === R3_colloquial_contextual (4 EN + 4 ZH, colloquial reply to item prompt) ===
        (
            "en",
            "R3_colloquial_contextual",
            2,
            "Zero days over these two weeks, honestly my mood has stayed upbeat.",
            False,
            0,
        ),
        (
            "en",
            "R3_colloquial_contextual",
            6,
            "Just 3 days over the fortnight when I beat myself up after a presentation.",
            False,
            1,
        ),
        (
            "en",
            "R3_colloquial_contextual",
            8,
            "About 8 days out of the last 14 where I couldn't stop pacing around my room.",
            False,
            2,
        ),
        (
            "en",
            "R3_colloquial_contextual",
            4,
            "Every single day for the full 14 days—I wake up already exhausted.",
            False,
            3,
        ),
        (
            "zh",
            "R3_colloquial_contextual",
            1,
            "呢兩星期一日都冇喎，放工去彈結他不知幾投入。",
            False,
            0,
        ),
        (
            "zh",
            "R3_colloquial_contextual",
            3,
            "呢兩個禮拜有四晚眼光光輾轉反側比較難入睡。",
            False,
            1,
        ),
        (
            "zh",
            "R3_colloquial_contextual",
            5,
            "過去十四日有八日都冇乜胃口，食兩啖就飽。",
            False,
            2,
        ),
        (
            "zh",
            "R3_colloquial_contextual",
            7,
            "呢兩星期日日如是，十四日都完全集中唔到精神寫報告。",
            False,
            3,
        ),
        # === R4_window_contrast_resolved (4 EN + 4 ZH, older period contrasted with explicit past-14-day count) ===
        (
            "en",
            "R4_window_contrast_resolved",
            3,
            "Back in January I had awful insomnia almost nightly, whereas in the past two weeks it happened on 0 nights.",
            False,
            0,
        ),
        (
            "en",
            "R4_window_contrast_resolved",
            4,
            "Last semester I felt tired constantly, though over the past 14 days I only felt fatigued on 3 days.",
            False,
            1,
        ),
        (
            "en",
            "R4_window_contrast_resolved",
            1,
            "Last summer I enjoyed everything, yet in the past two weeks I lost interest in hobbies on 9 days.",
            False,
            2,
        ),
        (
            "en",
            "R4_window_contrast_resolved",
            2,
            "Two months ago I felt fine, while across the past two weeks I've felt hopeless on 13 days.",
            False,
            3,
        ),
        (
            "zh",
            "R4_window_contrast_resolved",
            5,
            "舊年考試嗰陣成日暴飲暴食，不過最近呢兩星期零日有呢個問題，食慾好正常。",
            False,
            0,
        ),
        (
            "zh",
            "R4_window_contrast_resolved",
            7,
            "上個月日日都分心，但過去十四日好返好多，只係有三日比較難集中。",
            False,
            1,
        ),
        (
            "zh",
            "R4_window_contrast_resolved",
            6,
            "以前好少咁樣，但喺過去兩星期入面有十日都覺得自己好失敗。",
            False,
            2,
        ),
        (
            "zh",
            "R4_window_contrast_resolved",
            8,
            "半年前完全冇事，反而最近呢兩星期有十三日都坐唔定、手腳好煩躁。",
            False,
            3,
        ),
        # === A1_vague_quantifier (4 EN + 4 ZH, must abstain) ===
        (
            "en",
            "A1_vague_quantifier",
            1,
            "Sometimes lately I just don't feel super into my usual weekend plans.",
            True,
            None,
        ),
        (
            "en",
            "A1_vague_quantifier",
            3,
            "It happens quite often when I try to sleep after checking messages.",
            True,
            None,
        ),
        (
            "en",
            "A1_vague_quantifier",
            5,
            "Occasionally my appetite is a bit off depending on the canteen menu.",
            True,
            None,
        ),
        (
            "en",
            "A1_vague_quantifier",
            7,
            "Yeah, a fair bit recently whenever lectures get really dense.",
            True,
            None,
        ),
        (
            "zh",
            "A1_vague_quantifier",
            2,
            "有時都會覺得心情麻麻哋、有少少悶咁啦。",
            True,
            None,
        ),
        (
            "zh",
            "A1_vague_quantifier",
            4,
            "間唔中都會覺得個人幾攰吓，睇吓嗰日忙唔忙。",
            True,
            None,
        ),
        (
            "zh",
            "A1_vague_quantifier",
            6,
            "成日都會諗多咗少少嘅，不過又未算好實數。",
            True,
            None,
        ),
        (
            "zh",
            "A1_vague_quantifier",
            8,
            "偶爾開會嗰陣會覺得有啲坐唔定咁囉。",
            True,
            None,
        ),
        # === A2_wrong_timeframe (4 EN + 4 ZH, explicit older timeframe only -> must abstain) ===
        (
            "en",
            "A2_wrong_timeframe",
            2,
            "During my final exams last December I felt hopeless nearly every day.",
            True,
            None,
        ),
        (
            "en",
            "A2_wrong_timeframe",
            3,
            "Three months ago when I moved apartments I couldn't sleep on 10 nights.",
            True,
            None,
        ),
        (
            "en",
            "A2_wrong_timeframe",
            4,
            "Back in secondary school I was exhausted almost every afternoon.",
            True,
            None,
        ),
        (
            "en",
            "A2_wrong_timeframe",
            6,
            "Last summer after that internship rejection I blamed myself for two straight weeks.",
            True,
            None,
        ),
        (
            "zh",
            "A2_wrong_timeframe",
            1,
            "舊年冬天嗰陣幾乎日日都對所有嘢失去興趣。",
            True,
            None,
        ),
        (
            "zh",
            "A2_wrong_timeframe",
            5,
            "三個月前轉工嗰排有成十日都完全食唔落嘢。",
            True,
            None,
        ),
        (
            "zh",
            "A2_wrong_timeframe",
            7,
            "上學期寫論文嗰陣超過一半日子都集中唔到精神。",
            True,
            None,
        ),
        (
            "zh",
            "A2_wrong_timeframe",
            8,
            "兩年前有一段時間幾乎每日講嘢同動作都慢晒落嚟。",
            True,
            None,
        ),
        # === A3_cross_boundary_range (4 EN + 4 ZH, straddles R1 thresholds 1-2, 6-7, 11-12 -> must abstain) ===
        (
            "en",
            "A3_cross_boundary_range",
            1,
            "Over the past two weeks it was maybe 1 or 2 days, I didn't count closely.",
            True,
            None,
        ),
        (
            "en",
            "A3_cross_boundary_range",
            2,
            "In the last 14 days probably somewhere around 6 to 7 days of feeling low.",
            True,
            None,
        ),
        (
            "en",
            "A3_cross_boundary_range",
            4,
            "Over these two weeks I'd estimate 11 or 12 days of low stamina.",
            True,
            None,
        ),
        (
            "en",
            "A3_cross_boundary_range",
            7,
            "Roughly 6 or 7 days during the past fortnight where my concentration slipped.",
            True,
            None,
        ),
        (
            "zh",
            "A3_cross_boundary_range",
            3,
            "過去兩星期大約一至兩晚左右瞓得唔係幾好，唔太肯定。",
            True,
            None,
        ),
        (
            "zh",
            "A3_cross_boundary_range",
            5,
            "呢十四日入面大概六至七日胃口差啲，介乎中間咁上下。",
            True,
            None,
        ),
        (
            "zh",
            "A3_cross_boundary_range",
            6,
            "過去兩週大約十一或者十二日會覺得自責，記唔清實數。",
            True,
            None,
        ),
        (
            "zh",
            "A3_cross_boundary_range",
            8,
            "呢兩個禮拜可能六到七日有少少坐立不安，未計得好準。",
            True,
            None,
        ),
        # === A4_affect_only_no_frequency (4 EN + 4 ZH, emotional expression without frequency -> must abstain) ===
        (
            "en",
            "A4_affect_only_no_frequency",
            2,
            "Everything about my career uncertainty feels scary and overwhelming when I think about it.",
            True,
            None,
        ),
        (
            "en",
            "A4_affect_only_no_frequency",
            3,
            "Waking up groggy before an early seminar is honestly the worst feeling.",
            True,
            None,
        ),
        (
            "en",
            "A4_affect_only_no_frequency",
            6,
            "I really hate making silly mistakes in front of my supervisor, it stings.",
            True,
            None,
        ),
        (
            "en",
            "A4_affect_only_no_frequency",
            8,
            "Feeling jittery after drinking strong coffee is super unpleasant.",
            True,
            None,
        ),
        (
            "zh",
            "A4_affect_only_no_frequency",
            1,
            "見到出面落雨濕立立真係令人覺得好無癮好煩悶。",
            True,
            None,
        ),
        (
            "zh",
            "A4_affect_only_no_frequency",
            4,
            "每次趕完大報告嗰種虛脫感真係好難受好討厭。",
            True,
            None,
        ),
        (
            "zh",
            "A4_affect_only_no_frequency",
            5,
            "食飯時間見到飯堂排長龍真係好令人倒胃口。",
            True,
            None,
        ),
        (
            "zh",
            "A4_affect_only_no_frequency",
            7,
            "對住密密麻麻嘅試算表真係睇到個人頭都大埋好煩。",
            True,
            None,
        ),
    ]
    cases: list[E2SymptomCase] = []
    for idx, (lang, cat, item_id, text, abstain, freq) in enumerate(rows, start=1):
        prompt = (
            _ITEM_PROMPTS_EN[item_id] if lang == "en" else _ITEM_PROMPTS_ZH[item_id]
        )
        cases.append(
            E2SymptomCase(
                case_id=f"E2_{idx:02d}",
                language=lang,
                category=cat,
                item_id=item_id,
                assistant_prompt=prompt,
                user_text=text,
                should_abstain=abstain,
                gold_frequency=freq,
            )
        )
    assert len(cases) == 64
    assert sum(not c.should_abstain for c in cases) == 32
    assert sum(c.should_abstain for c in cases) == 32
    assert len({_norm_sha256(c.user_text) for c in cases}) == 64
    return cases


def build_e2_ml_train_corpus() -> tuple[list[str], list[int]]:
    """Build a 320-utterance bilingual training set (160 EN + 160 ZH) SHA-256 disjoint from E2 test."""
    en_domains = [
        "interest in daily activities",
        "feeling sad or discouraged",
        "difficulty staying asleep",
        "feeling low on energy",
        "changes in meal appetite",
        "feeling bad about myself",
        "trouble keeping focus",
        "moving slowly or restlessness",
    ]
    zh_domains = [
        "對日常活動提唔起興趣",
        "覺得心情低落沮喪",
        "夜晚入睡困難或者易醒",
        "日頭覺得疲倦冇力",
        "食慾減少或者食得太多",
        "覺得自責或者自己做得差",
        "做嘢睇書難以專心",
        "動作變慢或者坐唔定",
    ]
    en_templates = {
        0: [
            "For {dom}, not at all over the past two weeks (0 days).",
            "During these 14 days I experienced {dom} on zero days.",
            "No {dom} for me in the last two weeks; maybe 1 brief day at most.",
            "Over the fortnight, {dom} did not happen at all.",
            "Past 14 days record for {dom}: none, completely absent.",
        ],
        1: [
            "Over the past two weeks I noticed {dom} on several days, around 3 days.",
            "In these 14 days {dom} came up on 4 days after busy shifts.",
            "For {dom}, it happened a few times—specifically 2 days in the fortnight.",
            "During the last two weeks I had {dom} on 5 days total.",
            "Past two weeks: {dom} occurred on several days (about 6 days).",
        ],
        2: [
            "More than half the days in the past two weeks I dealt with {dom} (8 days).",
            "Over these 14 days {dom} happened on 9 days.",
            "For {dom}, I counted 10 days during the past two-week window.",
            "In the last fortnight {dom} was present more than half the time, 7 days.",
            "Past two weeks summary: {dom} persisted on 11 days.",
        ],
        3: [
            "Nearly every day in the past two weeks I struggled with {dom} (12 days).",
            "Over all 14 days {dom} happened almost daily without a break.",
            "For {dom}, it was 13 days out of the past two weeks.",
            "Every day across the fortnight (14 days) I had severe {dom}.",
            "In the last two weeks {dom} showed up nearly every single day.",
        ],
    }
    zh_templates = {
        0: [
            "過去兩星期關於{dom}係完全沒有，零日出現。",
            "呢十四日入面我完全冇{dom}嘅情況。",
            "以過去兩週計，{dom}最多只有一日甚至完全冇。",
            "最近兩個禮拜{dom}係零次，狀態好正常。",
            "過去兩星期統計：{dom}完全沒有發生過。",
        ],
        1: [
            "過去兩星期有幾天出現{dom}，大約三日左右。",
            "呢十四日裏面我有四日覺得{dom}。",
            "以過去兩週嚟講，{dom}出現咗兩日，算係有幾天。",
            "最近兩個星期總共有五日遇到{dom}嘅情況。",
            "過去兩星期有幾天（實數六日）有{dom}。",
        ],
        2: [
            "過去兩星期超過一半的日子都有{dom}，數返有八日。",
            "呢十四日入面有九日都出現{dom}。",
            "以過去兩週計算，{dom}持續咗十日，超過一半時間。",
            "最近兩個禮拜有七日覺得{dom}，過咗一半日子。",
            "過去兩星期有十一日都受{dom}影響。",
        ],
        3: [
            "過去兩星期幾乎每天都有{dom}，足足十二日。",
            "呢十四日入面有十三日都持續出現{dom}。",
            "以過去兩週嚟講，{dom}幾乎日日都有，成十四日。",
            "最近兩個星期幾乎每天都因為{dom}而困擾。",
            "過去兩星期差唔多日日（十二日以上）都有{dom}。",
        ],
    }
    texts: list[str] = []
    labels: list[int] = []
    for y in range(4):
        for dom in en_domains:
            for tmpl in en_templates[y]:
                texts.append(tmpl.format(dom=dom))
                labels.append(y)
        for dom in zh_domains:
            for tmpl in zh_templates[y]:
                texts.append(tmpl.format(dom=dom))
                labels.append(y)
    test_hashes = {
        _norm_sha256(c.user_text)
        for c in (build_e2_symptom_cases() + build_e2_hard_challenge_cases())
    }
    train_hashes = {_norm_sha256(t) for t in texts}
    assert len(texts) == 320
    assert len(train_hashes) == 320
    assert not (train_hashes & test_hashes), "Train/Test leakage detected in E2!"
    return texts, labels


def build_e2_hard_challenge_cases() -> list[E2SymptomCase]:
    """Return 16 realistic HK code-switched, ironic, and boundary-trap conversational cases."""
    rows: list[tuple[str, str, int, str, bool, int | None]] = [
        # --- 8 Resolvable Challenge Cases (4 ZH code-switched + 4 EN colloquial) ---
        (
            "zh",
            "H1_irony_resolved",
            3,
            "係呀我不知幾好瞓，呢 two weeks 有十二晚凌晨四點仲眼仔碌碌望住天花板到天光囉。",
            False,
            3,
        ),
        (
            "en",
            "H1_irony_resolved",
            3,
            "Oh yeah sleeping like a dream—if your dream is waking up soaked in sweat 10 nights out of the last 14.",
            False,
            2,
        ),
        (
            "zh",
            "H2_calendar_math",
            4,
            "呢 two weeks 逢禮拜一至五返 intern 都 tired 到死，係兩個 weekend 共四日先精神返完全唔攰。",
            False,
            2,
        ),
        (
            "en",
            "H2_calendar_math",
            4,
            "Over these past two weeks it only hit me on Mondays and Thursdays after 3-hour labs, totally energetic the other ten days.",
            False,
            1,
        ),
        (
            "zh",
            "H3_boundary_exact",
            6,
            "呢十四日頭一個 week 完全 ok 冇嘢，係第二個禮拜連續七日都覺得自己做 project 好廢好失敗。",
            False,
            2,
        ),
        (
            "en",
            "H3_boundary_exact",
            5,
            "First week of the fortnight my eating was normal, then all 7 days of this second week I barely touched meals.",
            False,
            2,
        ),
        (
            "zh",
            "H4_self_correction_resolved",
            1,
            "原本想講呢兩星期日日都冇 mood 玩，但諗真啲上禮拜去 camp 嗰陣好 happy，其實只係返嚟呢三日提唔起勁啫。",
            False,
            1,
        ),
        (
            "en",
            "H4_self_correction_resolved",
            2,
            "I almost said several days, wait—actually there was just that single Tuesday night last week when I felt hopeless, only 1 day out of 14.",
            False,
            0,
        ),
        # --- 8 Must-Abstain Challenge Cases (4 ZH code-switched + 4 EN colloquial) ---
        (
            "zh",
            "H5_weekly_rate_cross_boundary",
            3,
            "呢 two weeks 大概一個禮拜有三至四晚瞓唔著啦，兩個禮拜加埋冇認真數實。",
            True,
            None,
        ),
        (
            "en",
            "H5_weekly_rate_cross_boundary",
            7,
            "Across the last fortnight my focus zoned out roughly three to four days a week during study sessions.",
            True,
            None,
        ),
        (
            "zh",
            "H6_past_fortnight_trap",
            5,
            "上次 mid-term 嗰 two weeks 我直頭有十日完全食唔落 lunch，而家諗返起嗰兩個禮拜都仲覺得胃痛。",
            True,
            None,
        ),
        (
            "en",
            "H6_past_fortnight_trap",
            8,
            "During that two-week quarantine period I paced around my room restless for 12 days straight; talking about it now still stresses me out.",
            True,
            None,
        ),
        (
            "zh",
            "H7_code_switch_litotes_vague",
            7,
            "呢兩個禮拜你話完全冇分心就假嘅，溫書嗰陣 on and off 都會 drift 走吓咁囉。",
            True,
            None,
        ),
        (
            "en",
            "H7_code_switch_litotes_vague",
            6,
            "Saying I never felt like a failure over these two weeks would be a lie—it crept in every now and then.",
            True,
            None,
        ),
        (
            "zh",
            "H8_retracted_or_sarcastic_vague",
            2,
            "頭先講錯咗話日日都 down，其實嗰陣係講緊上個月啫，至於呢 two weeks 有幾多日我就真係唔記得喇。",
            True,
            None,
        ),
        (
            "en",
            "H8_retracted_or_sarcastic_vague",
            1,
            "Haha yeah totally loving group projects right now, staring at messy slides at midnight is peak joy.",
            True,
            None,
        ),
    ]
    cases: list[E2SymptomCase] = []
    for idx, (lang, cat, item_id, text, abstain, freq) in enumerate(rows, start=1):
        prompt = (
            _ITEM_PROMPTS_EN[item_id] if lang == "en" else _ITEM_PROMPTS_ZH[item_id]
        )
        cases.append(
            E2SymptomCase(
                case_id=f"E2H_{idx:02d}",
                language=lang,
                category=cat,
                item_id=item_id,
                assistant_prompt=prompt,
                user_text=text,
                should_abstain=abstain,
                gold_frequency=freq,
            )
        )
    core_hashes = {_norm_sha256(c.user_text) for c in build_e2_symptom_cases()}
    hard_hashes = {_norm_sha256(c.user_text) for c in cases}
    assert len(cases) == 16
    assert len(hard_hashes) == 16
    assert not (core_hashes & hard_hashes)
    return cases


@dataclass(frozen=True)
class E3SessionProfile:
    profile_id: str
    split: str
    quadrant: str
    item_order: tuple[int, ...]
    true_items: dict[int, int]
    observed_items: dict[int, int | None]
    turn_texts: tuple[str, ...]
    phq8_total: int
    elevated: int


def build_e3_partial_observation_cohort(seed: int = 42) -> list[E3SessionProfile]:
    """Generate 240 stratified 8-turn English screening profiles (160 train / 80 test).

    Turn utterances are natural English sentences so that the TweetEval-trained classical ML
    sentiment classifier from E1A produces real turn-level polarity probabilities P(neg, neu, pos)
    on every turn without cross-script confound, isolating the partial-observation information
    geometry between Affect (S_k), Partial Symptoms (N_k), and Dual-Channel Fusion (F_k).
    """
    rng = np.random.default_rng(seed)
    quadrants = (
        "congruent_low",
        "situational_distress",
        "masked_somatic",
        "congruent_elevated",
    )
    domain_nouns = {
        1: ("hobbies", "weekend plans", "music practice", "cooking"),
        2: ("overall mood", "outlook", "emotional steadiness", "daily spirits"),
        3: ("nighttime sleep", "staying asleep", "sleep schedule", "bedtime rest"),
        4: ("daytime energy", "physical stamina", "afternoon alertness", "vitality"),
        5: ("meal appetite", "regular eating", "lunch and dinner intake", "hunger"),
        6: (
            "self-regard",
            "confidence at work",
            "sense of self-worth",
            "self-evaluation",
        ),
        7: ("reading concentration", "task focus", "lecture attention", "mental focus"),
        8: (
            "walking and speaking pace",
            "physical restlessness",
            "sitting still",
            "movement pace",
        ),
    }
    stressor_tags = (
        "after noisy construction next door",
        "because the commuter train was delayed again",
        "when my printer jammed right before class",
        "after getting splashed by a passing taxi",
        "because group scheduling got messy today",
        "when the campus Wi-Fi dropped mid-upload",
    )
    calm_tags = (
        "during a steady fortnight",
        "across my usual routine",
        "over this two-week stretch",
        "throughout the past 14 days",
        "on my regular weekly schedule",
        "over the last couple of weeks",
    )
    bleak_tags = (
        "and everything feels heavy and exhausting",
        "which leaves me feeling drained and discouraged",
        "and honestly it has felt bleak and overwhelming",
        "making the whole fortnight feel miserable",
        "and I feel worn down and disappointed in myself",
        "which has been really painful to get through",
    )
    clinical_tags = (
        "logged purely by calendar count",
        "noted as a plain routine observation",
        "recorded factually from my planner",
        "counted across the 14-day window",
        "tracked without dramatizing it",
        "summarized from my daily schedule",
    )

    profiles: list[E3SessionProfile] = []
    seen_utterances: set[str] = set()

    for q_idx, quad in enumerate(quadrants):
        for i in range(60):
            split = "train" if i < 40 else "test"
            pid = f"E3_{q_idx * 60 + i + 1:03d}"
            # Sample realistic item scores matching quadrant definition
            while True:
                if quad == "congruent_low":
                    probs = [0.62, 0.30, 0.07, 0.01]
                    vals = {item: int(rng.choice(4, p=probs)) for item in range(1, 9)}
                    if sum(vals.values()) <= 7:
                        break
                elif quad == "situational_distress":
                    probs = [0.48, 0.38, 0.12, 0.02]
                    vals = {item: int(rng.choice(4, p=probs)) for item in range(1, 9)}
                    if 2 <= sum(vals.values()) <= 9:
                        break
                elif quad == "masked_somatic":
                    vals = {}
                    for item in range(1, 9):
                        if item in (3, 4, 5, 7):
                            vals[item] = int(rng.choice(4, p=[0.05, 0.20, 0.45, 0.30]))
                        else:
                            vals[item] = int(rng.choice(4, p=[0.30, 0.40, 0.22, 0.08]))
                    if 10 <= sum(vals.values()) <= 18:
                        break
                else:  # congruent_elevated
                    probs = [0.06, 0.22, 0.40, 0.32]
                    vals = {item: int(rng.choice(4, p=probs)) for item in range(1, 9)}
                    if sum(vals.values()) >= 11:
                        break

            order = tuple(int(x) for x in rng.permutation(np.arange(1, 9)))
            # Simulate realistic partial conversational ambiguity before review:
            # 1 or 2 early turns may initially use a vague quantifier (observed=None until later review)
            n_unclarified = int(rng.choice([1, 2, 3], p=[0.35, 0.45, 0.20]))
            unclarified_positions = set(
                int(x) for x in rng.choice(6, size=n_unclarified, replace=False)
            )

            observed: dict[int, int | None] = {}
            texts: list[str] = []
            for pos, item in enumerate(order):
                v = vals[item]
                noun = domain_nouns[item][(i + pos) % len(domain_nouns[item])]
                freq_phrase = {
                    0: f"0 days of issues with {noun}",
                    1: f"about {int(rng.integers(2, 6))} days of mild {noun} changes",
                    2: f"{int(rng.integers(7, 11))} days of noticeable {noun} difficulty",
                    3: f"{int(rng.integers(12, 15))} days of persistent {noun} trouble",
                }[v]
                if pos in unclarified_positions:
                    observed[item] = None
                    freq_phrase = (
                        f"some occasional shifts in {noun} without counting exact days"
                    )
                else:
                    observed[item] = v

                if quad == "congruent_low":
                    tag = calm_tags[(i + pos) % len(calm_tags)]
                    tone = (
                        "I felt good and comfortable"
                        if (pos + i) % 2 == 0
                        else "Things stayed steady and normal"
                    )
                    utt = f"[{pid}-T{pos + 1}] {tone} {tag}, with {freq_phrase}."
                elif quad == "situational_distress":
                    if pos % 3 != 2:
                        tag = stressor_tags[(i + pos) % len(stressor_tags)]
                        utt = f"[{pid}-T{pos + 1}] Honestly annoyed and frustrated today {tag}, though overall I had {freq_phrase}."
                    else:
                        tag = calm_tags[(i + pos) % len(calm_tags)]
                        utt = f"[{pid}-T{pos + 1}] Setting today's hassle aside, {tag} I only had {freq_phrase}."
                elif quad == "masked_somatic":
                    tag = clinical_tags[(i + pos) % len(clinical_tags)]
                    if v >= 2 and pos % 3 == 0:
                        utt = f"[{pid}-T{pos + 1}] Reporting {tag}: {freq_phrase}, feeling somewhat worn down physically."
                    else:
                        utt = (
                            f"[{pid}-T{pos + 1}] Standard update {tag}: {freq_phrase}."
                        )
                else:
                    tag = bleak_tags[(i + pos) % len(bleak_tags)]
                    utt = f"[{pid}-T{pos + 1}] Over these two weeks I had {freq_phrase}, {tag}."

                # Strip ID prefix from model input while guaranteeing uniqueness via varied phrasing
                clean_utt = utt.split("] ", 1)[1] + f" (note {i + 1}-{pos + 1})"
                assert clean_utt not in seen_utterances
                seen_utterances.add(clean_utt)
                texts.append(clean_utt)

            total = sum(vals.values())
            profiles.append(
                E3SessionProfile(
                    profile_id=pid,
                    split=split,
                    quadrant=quad,
                    item_order=order,
                    true_items=vals,
                    observed_items=observed,
                    turn_texts=tuple(texts),
                    phq8_total=total,
                    elevated=int(total >= 10),
                )
            )
    assert len(profiles) == 240
    assert sum(p.split == "train" for p in profiles) == 160
    assert sum(p.split == "test" for p in profiles) == 80
    return profiles


@dataclass(frozen=True)
class E4Persona:
    persona_id: str
    language: str
    quadrant: str
    gold_items: dict[int, int]
    per_item_initial: dict[int, str]
    per_item_clarification: dict[int, str]
    multi_domain_bundles: tuple[tuple[tuple[int, ...], str], ...]
    turn_sentiments: tuple[str, ...]

    @property
    def gold_total(self) -> int:
        return sum(self.gold_items.values())


def build_e4_dialogue_personas() -> list[E4Persona]:
    """Construct 32 8-domain bilingual personas (16 EN + 16 ZH; 8 per quadrant) for Policy Comparison."""
    rng = np.random.default_rng(20261127)
    quadrants = (
        "congruent_low",
        "situational_distress",
        "masked_somatic",
        "congruent_elevated",
    )
    personas: list[E4Persona] = []
    idx = 0
    for quad in quadrants:
        for lang in ("en", "zh"):
            for rep in range(4):
                idx += 1
                pid = f"E4P_{idx:02d}"
                if quad == "congruent_low":
                    base = [0, 0, 1, 1, 0, 0, 0, 0]
                    rng.shuffle(base)
                    sents = ("positive", "neutral", "positive", "neutral")
                elif quad == "situational_distress":
                    base = [0, 1, 1, 1, 0, 1, 0, 0]
                    rng.shuffle(base)
                    sents = ("negative", "negative", "negative", "neutral")
                elif quad == "masked_somatic":
                    base = [1, 0, 3, 3, 2, 0, 2, 1]
                    sents = ("neutral", "neutral", "neutral", "neutral")
                else:
                    base = [2, 3, 3, 3, 2, 2, 2, 1]
                    sents = ("negative", "negative", "negative", "negative")

                gold = {i + 1: int(base[i]) for i in range(8)}
                # Introduce realistic conversational phenomena on fixed slots:
                # - slot A (item 3): vague quantifier initially ("sometimes" / "有時"), needing clarification
                # - slot B (item 4): embedded exact day count in natural prose
                # - slot C (item 6): older-window mention ("last winter" / "舊年冬天") before clarifying past 14 days
                vague_item = 3
                exact_day_item = 4
                old_window_item = 6
                day_for_val = {0: 0, 1: 4, 2: 9, 3: 13}

                per_init: dict[int, str] = {}
                per_clar: dict[int, str] = {}
                for item, val in gold.items():
                    d = day_for_val[val]
                    if lang == "en":
                        per_clar[item] = f"{d} days"
                        if item == vague_item:
                            per_init[item] = (
                                "Sometimes my sleep gets disrupted depending on noise."
                                if val <= 1
                                else "Quite often lately I struggle to stay asleep through the night."
                            )
                        elif item == exact_day_item:
                            per_init[item] = (
                                f"Looking at the past two weeks, I felt low on energy on {d} days."
                            )
                        elif item == old_window_item:
                            per_init[item] = (
                                "Last winter during finals I blamed myself almost every day."
                            )
                        else:
                            canon = {
                                0: "Not at all in the past two weeks.",
                                1: "Several days over the past two weeks.",
                                2: "More than half the days in the past two weeks.",
                                3: "Nearly every day in the past two weeks.",
                            }[val]
                            per_init[item] = canon
                    else:
                        zh_d = {0: "零日", 4: "四日", 9: "九日", 13: "十三日"}[d]
                        per_clar[item] = zh_d
                        if item == vague_item:
                            per_init[item] = (
                                "有時夜晚都會瞓得麻麻哋咁啦。"
                                if val <= 1
                                else "成日都會半夜醒咗覺得難瞓返。"
                            )
                        elif item == exact_day_item:
                            per_init[item] = (
                                f"計返過去兩星期入面，我有{zh_d}覺得疲倦冇力。"
                            )
                        elif item == old_window_item:
                            per_init[item] = "舊年冬天趕大項目嗰陣幾乎日日都覺得自責。"
                        else:
                            canon_zh = {
                                0: "過去兩星期完全沒有。",
                                1: "過去兩星期有幾天。",
                                2: "過去兩星期超過一半的日子。",
                                3: "過去兩星期幾乎每天。",
                            }[val]
                            per_init[item] = canon_zh

                bundles = (
                    ((1, 2), f"{per_init[1]} {per_init[2]}"),
                    ((3, 4), f"{per_init[3]} {per_init[4]}"),
                    ((5, 6), f"{per_init[5]} {per_init[6]}"),
                    ((7, 8), f"{per_init[7]} {per_init[8]}"),
                )
                personas.append(
                    E4Persona(
                        persona_id=pid,
                        language=lang,
                        quadrant=quad,
                        gold_items=gold,
                        per_item_initial=per_init,
                        per_item_clarification=per_clar,
                        multi_domain_bundles=bundles,
                        turn_sentiments=sents,
                    )
                )
    assert len(personas) == 32
    return personas


def build_e4_live_session_scripts() -> list[dict]:
    """Return 4 live multi-turn Chatbot scripts testing E4B end-to-end properties."""
    return [
        {
            "session_label": "S1_zh_situational_distress",
            "language": "zh",
            "expected_quadrant": "situational_distress",
            "description": "Cantonese/Traditional Chinese user venting acute transit/work frustration across turns while reporting low 14-day PHQ-8 frequencies.",
            "turns": [
                "今日落大雨搭巴士塞咗成個鐘，仲俾上司挑剔份簡報排版，真係激死我好煩躁！不過講返過去兩星期，做平時鍾意嘅運動完全沒有減少興趣，心情低落都只係有幾天（大約兩日）。",
                "唉頭先仲發現漏低咗把遮喺車上面好討厭！計返過去兩星期嘅睡眠同體力：入睡困難有幾天（三晚左右），疲倦冇力都係有幾天（三日），食慾改變就完全沒有。",
                "雖然今日單嘢令我好忟憎，但過去兩星期完全沒有自責或覺得自己失敗，睇書做嘢難以集中精神都係完全沒有，動作變慢或者坐立不安亦完全沒有。",
            ],
            "fallback_turns": [
                "補充返以過去兩星期計：興趣減少係完全沒有（0日），心情低落係有幾天（2日），睡眠困擾係有幾天（3日），疲倦係有幾天（3日），食慾改變、自責、難以集中同動作變慢坐立不安呢四項全部都係完全沒有（0日）。",
            ],
            "review_override": None,
        },
        {
            "session_label": "S2_en_masked_somatic_clarification",
            "language": "en",
            "expected_quadrant": "masked_somatic",
            "description": "English user reporting elevated somatic/cognitive frequencies in calm factual prose, initially giving a vague quantifier on item 8 before clarifying.",
            "turns": [
                "Recording my past two weeks factually from my planner: little interest in activities happened on 3 days, and feeling down or hopeless was 0 days.",
                "Continuing the two-week log: fragmented sleep under four hours occurred on 12 nights, low physical energy on 13 days, and reduced meal appetite on 9 days.",
                "For the remaining items over the past two weeks: feeling bad about myself was 0 days, trouble concentrating on reports happened on 8 days, and restlessness was just occasionally.",
                "To clarify that last restlessness item for the past two weeks: it was 0 days.",
            ],
            "fallback_turns": [
                "Confirming all eight items for the past 14 days: reduced interest 3 days, depressed mood 0 days, sleep trouble 12 days, fatigue 13 days, appetite change 9 days, self-blame 0 days, concentration trouble 8 days, psychomotor restlessness or slowing 0 days.",
            ],
            "review_override": None,
        },
        {
            "session_label": "S3_zh_timeframe_guard_and_override",
            "language": "zh",
            "expected_quadrant": "congruent_low",
            "description": "Traditional Chinese user mentioning older winter insomnia (must not count for past 14 days), clarifying past-two-week frequencies, and overriding one item at batch review.",
            "turns": [
                "舊年冬天趕畢業設計嗰陣幾乎日日失眠，不過講返過去兩星期：做嘢提唔起興趣完全沒有，心情低落亦完全沒有。",
                "至於過去兩星期嘅睡眠其實只係有幾天（三晚）比較難入睡；過去兩星期疲倦有幾天（兩日），食慾改變完全沒有。",
                "最後三項以過去兩星期計：自責完全沒有，難以集中精神完全沒有，動作變慢或坐立不安都係完全沒有。",
            ],
            "fallback_turns": [
                "確認過去兩星期八項情況：睡眠困擾係有幾天（3日），疲倦係有幾天（2日），其餘六項（興趣減少、心情低落、食慾改變、自責、難以集中、動作或坐立不安）喺過去兩星期全部都係完全沒有（0日）。",
            ],
            "review_override": {"item_id": 4, "new_value": 2},
        },
        {
            "session_label": "S4_en_congruent_elevated_invariance",
            "language": "en",
            "expected_quadrant": "congruent_elevated",
            "description": "English user with distressed tone and elevated 14-day symptom burden, followed by deterministic score-invariance, quote-provenance, and demo safety-guard verification.",
            "turns": [
                "These past two weeks have felt awful and exhausting—I lost interest in almost everything on 10 days and felt down and hopeless on 12 days.",
                "Sleep has been terrible on 12 nights over the past two weeks, I felt completely drained of energy on 13 days, and my appetite dropped badly on 8 days.",
                "Across the past two weeks I blamed myself like a failure on 9 days, couldn't concentrate on work on 10 days, and felt restless in my chair on 4 days.",
            ],
            "fallback_turns": [
                "Over the past 14 days specifically: little interest 10 days, depressed mood 12 days, sleep problems 12 days, tired/little energy 13 days, poor appetite 8 days, feeling like a failure 9 days, trouble concentrating 10 days, restless fidgeting 4 days.",
            ],
            "review_override": None,
        },
    ]
