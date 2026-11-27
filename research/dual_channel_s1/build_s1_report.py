"""Generate the Group T Semester 1 Final Report (.docx and Markdown source).

Reads measured outputs from ``results/dual-channel-s1-v2-20261127/summary_v2.json`` and writes:
- ``docs/semester1_final/Final_Report_T.docx``
- ``docs/semester1_final/report_source.md``
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]

NAVY = RGBColor(0x1F, 0x4E, 0x79)
STEEL = RGBColor(0x2E, 0x75, 0xB6)
CHARCOAL = RGBColor(0x22, 0x22, 0x22)
MUTED = RGBColor(0x55, 0x55, 0x55)


def _set_east_asia_font(
    style_or_run, latin_font: str = "Calibri", ea_font: str = "PingFang HK"
):
    style_or_run.font.name = latin_font
    rpr = style_or_run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), latin_font)
    rfonts.set(qn("w:hAnsi"), latin_font)
    rfonts.set(qn("w:eastAsia"), ea_font)


def _shade_cell(cell, hex_color: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)


def _set_cell_margins(cell, top=75, bottom=75, left=105, right=105):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = OxmlElement("w:tcMar")
    for side, val in (
        ("top", top),
        ("bottom", bottom),
        ("left", left),
        ("right", right),
    ):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tc_mar.append(node)
    tc_pr.append(tc_mar)


def _set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = parse_xml(
        f"<w:tblBorders {nsdecls('w')}>"
        '<w:top w:val="single" w:sz="8" w:space="0" w:color="1F4E79"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="1F4E79"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        '<w:left w:val="none"/><w:right w:val="none"/><w:insideV w:val="none"/>'
        "</w:tblBorders>"
    )
    tbl_pr.append(borders)


def _add_page_number_field(run):
    fld_char1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    instr_text = parse_xml(
        r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls("w")
    )
    fld_char2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
    fld_char3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)
    run._r.append(fld_char3)


def _configure_document(doc: Document):
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.PORTRAIT
    sec.page_width = Inches(8.27)  # A4
    sec.page_height = Inches(11.69)
    sec.top_margin = Inches(0.82)
    sec.bottom_margin = Inches(0.82)
    sec.left_margin = Inches(0.88)
    sec.right_margin = Inches(0.88)
    sec.different_first_page_header_footer = True

    hdr_p = sec.header.paragraphs[0]
    hdr_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hr = hdr_p.add_run(
        "Sentiment Analysis for Depression Detection  |  Group T Semester 1 Final Report"
    )
    _set_east_asia_font(hr, "Calibri", "PingFang HK")
    hr.font.size = Pt(8.5)
    hr.font.color.rgb = MUTED

    ftr_p = sec.footer.paragraphs[0]
    ftr_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr1 = ftr_p.add_run("CUHK SEEM Final Year Project (Group T)  —  Page ")
    _set_east_asia_font(fr1, "Calibri", "PingFang HK")
    fr1.font.size = Pt(8.5)
    fr1.font.color.rgb = MUTED
    fr_pg = ftr_p.add_run()
    _set_east_asia_font(fr_pg, "Calibri", "PingFang HK")
    fr_pg.font.size = Pt(8.5)
    fr_pg.font.color.rgb = MUTED
    _add_page_number_field(fr_pg)

    normal = doc.styles["Normal"]
    _set_east_asia_font(normal, "Calibri", "PingFang HK")
    normal.font.size = Pt(10.2)
    normal.font.color.rgb = CHARCOAL
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(5)

    for lvl, (sz, color, sb, sa) in {
        1: (13.8, NAVY, 11, 4),
        2: (11.4, STEEL, 8, 3),
        3: (10.5, CHARCOAL, 6, 2),
    }.items():
        st = doc.styles[f"Heading {lvl}"]
        _set_east_asia_font(st, "Calibri", "PingFang HK")
        st.font.size = Pt(sz)
        st.font.bold = True
        st.font.color.rgb = color
        st.paragraph_format.space_before = Pt(sb)
        st.paragraph_format.space_after = Pt(sa)
        st.paragraph_format.keep_with_next = True


def _add_p(
    doc: Document,
    text: str,
    *,
    bold_prefix: str | None = None,
    italic: bool = False,
    space_after: float = 4.8,
):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        _set_east_asia_font(rb, "Calibri", "PingFang HK")
        rb.bold = True
        rb.font.color.rgb = NAVY
    r = p.add_run(text)
    _set_east_asia_font(r, "Calibri", "PingFang HK")
    r.italic = italic
    return p


def _add_styled_table(
    doc: Document,
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[float],
    caption: str,
    *,
    keep_together: bool = True,
):
    cap_p = doc.add_paragraph()
    cap_p.paragraph_format.space_before = Pt(5)
    cap_p.paragraph_format.space_after = Pt(2)
    cap_p.paragraph_format.keep_with_next = True
    rc = cap_p.add_run(caption)
    _set_east_asia_font(rc, "Calibri", "PingFang HK")
    rc.bold = True
    rc.font.size = Pt(9.2)
    rc.font.color.rgb = NAVY

    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(tbl)

    hdr_tr = tbl.rows[0]._tr.get_or_add_trPr()
    hdr_tr.append(OxmlElement("w:tblHeader"))
    hdr_tr.append(OxmlElement("w:cantSplit"))
    for j, h in enumerate(headers):
        c = tbl.cell(0, j)
        c.width = Inches(col_widths[j])
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _shade_cell(c, "1F4E79")
        _set_cell_margins(c, top=75, bottom=75, left=85, right=85)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        if keep_together:
            p.paragraph_format.keep_with_next = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        _set_east_asia_font(r, "Calibri", "PingFang HK")
        r.bold = True
        r.font.size = Pt(8.8)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for i, row in enumerate(rows):
        tr_pr = tbl.rows[i + 1]._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        bg = "F6F9FC" if i % 2 == 1 else "FFFFFF"
        is_last = i == len(rows) - 1
        for j, val in enumerate(row):
            c = tbl.cell(i + 1, j)
            c.width = Inches(col_widths[j])
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            _shade_cell(c, bg)
            _set_cell_margins(c, top=60, bottom=60, left=85, right=85)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            if keep_together and not is_last:
                p.paragraph_format.keep_with_next = True
            p.alignment = (
                WD_ALIGN_PARAGRAPH.LEFT
                if j == 0 or len(val) > 25
                else WD_ALIGN_PARAGRAPH.CENTER
            )
            r = p.add_run(val)
            _set_east_asia_font(r, "Calibri", "PingFang HK")
            r.font.size = Pt(8.6)
            r.font.color.rgb = CHARCOAL
            if j == 0 and any(
                k in val
                for k in ("Connected Chatbot", "Connected LLM", "Linear SVM", "RQ")
            ):
                r.bold = True

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(2.5)


def _add_figure(doc: Document, img_path: Path, caption: str, width_in: float = 6.35):
    if not img_path.exists():
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(4)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.paragraph_format.keep_with_next = True
    p_img.add_run().add_picture(str(img_path), width=Inches(width_in))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(5)
    rc = p_cap.add_run(caption)
    _set_east_asia_font(rc, "Calibri", "PingFang HK")
    rc.italic = True
    rc.font.size = Pt(8.8)
    rc.font.color.rgb = MUTED


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{100.0 * x:.1f}%"


def _f3(x: float | None) -> str:
    return "—" if x is None else f"{x:.3f}"


def build_reports(
    summary_v2_path: Path, fig_dir: Path, out_dir: Path, test_count: int = 234
) -> dict[str, Path]:
    data = json.loads(summary_v2_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)

    e1a = data["e1"]["e1a_tweeteval"]
    e1b = data["e1"]["e1b_quadrant_divergence"]
    e2 = data["e2"]
    e3 = data["e3_end_to_end"]

    m_maj = e1a["test_models"]["majority"]
    m_nb = e1a["test_models"]["tfidf_multinomial_nb"]
    m_lr = e1a["test_models"]["tfidf_logistic_regression"]
    m_svm = e1a["test_models"]["tfidf_linear_svm"]
    boot_svm_maj = e1a["paired_bootstrap_macro_f1"]["linear_svm_vs_majority"]
    boot_svm_lr = e1a["paired_bootstrap_macro_f1"]["linear_svm_vs_logreg"]

    e1b_models = e1b["models"]
    live_e1b = e1b_models["live_gpt_terra"]
    oracle_e1b = e1b_models["oracle_polarity_ceiling"]

    e2m = e2["methods"]
    live_e2 = e2m["live_dual_channel_chatbot"]
    e3_sessions = e3["live_sessions"]
    e3_audits = e3["architectural_audits"]

    doc = Document()
    _configure_document(doc)

    # --- Title Block ---
    p_uni = doc.add_paragraph()
    p_uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_uni.paragraph_format.space_before = Pt(6)
    p_uni.paragraph_format.space_after = Pt(2)
    ru = p_uni.add_run(
        "THE CHINESE UNIVERSITY OF HONG KONG\n"
        "Department of Systems Engineering and Engineering Management"
    )
    _set_east_asia_font(ru, "Calibri", "PingFang HK")
    ru.bold = True
    ru.font.size = Pt(10.5)
    ru.font.color.rgb = STEEL

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(3)
    rt = p_title.add_run("Sentiment Analysis for Depression Detection")
    _set_east_asia_font(rt, "Calibri", "PingFang HK")
    rt.bold = True
    rt.font.size = Pt(18.5)
    rt.font.color.rgb = NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(6)
    rs = p_sub.add_run(
        "A Dual-Channel Bilingual Chatbot for PHQ-8 Preliminary Screening\n"
        "Semester 1 Final Report  ·  Group T  ·  27 November 2026"
    )
    _set_east_asia_font(rs, "Calibri", "PingFang HK")
    rs.italic = True
    rs.font.size = Pt(10.8)
    rs.font.color.rgb = CHARCOAL

    _add_styled_table(
        doc,
        ["Project Item", "Details"],
        [
            ["Approved Title", "Sentiment Analysis for Depression Detection"],
            [
                "Group & Members",
                "Group T  —  CHAN, Kin Long (1155212039)  ·  LEE, Ka Tung (1155212062)",
            ],
            ["Supervisor", "Prof. Helen Meng"],
            [
                "System Prototype",
                "Bilingual (Traditional Chinese / Cantonese & English) Preliminary Screening Chatbot + Offline Rule Baseline",
            ],
        ],
        [1.75, 4.75],
        "Project Identification",
    )

    # --- Concise, Motivation-Driven Abstract ---
    doc.add_heading("Abstract", level=1)
    _add_p(
        doc,
        "A common pitfall in text-based mental-health projects is treating negative sentiment as a direct proxy for depression. In preliminary screening conversations, however, emotional tone and two-week symptom frequency often diverge: a person angrily complaining about a bus delay expresses negative sentiment without ongoing depressive symptoms (situational distress), whereas someone calmly reporting twelve sleepless nights and daily fatigue in neutral prose has high symptom burden (masked somatic reporting). To resolve this mismatch, we built a bilingual (Traditional Chinese/Cantonese and English) Dual-Channel Preliminary Screening Chatbot based on the eight-item PHQ-8 questionnaire. One channel tracks turn-level sentiment only to guide supportive conversational replies and post-session tone notes, while a separate symptom channel extracts past-14-day frequencies backed by verbatim user quotes, asks follow-up questions on unclear inputs, and requires explicit user review before summing the 0–24 score. "
        f"Across three linked experiments, public TweetEval baselines (Macro-F1 {_f3(m_svm['macro_f1'])} with Linear SVM) and a 48-case bilingual stress test confirmed that even 100% accurate sentiment achieves only 50.0% accuracy as a naive proxy for elevated PHQ-8 burden. On an 80-utterance bilingual extraction test including Hong Kong code-switched stress cases, our chatbot reached {_pct(live_e2['joint_end_to_end_accuracy'])} rule-compliance accuracy with zero false acceptances, and four multi-turn walkthroughs verified end-to-end user review and score invariance to sentiment. All custom screening cases and chatbot walkthroughs use fictional inputs; no clinical validity is claimed.",
    )

    # ==========================================================================
    # Section 1: Introduction, Problem Motivation, and Research Questions
    # ==========================================================================
    doc.add_heading("1. Introduction and Research Questions", level=1)
    _add_p(
        doc,
        "Under our project title, Sentiment Analysis for Depression Detection, our objective is to build a practical preliminary screening chatbot while clarifying what role sentiment analysis should—and should not—play. Standard PHQ-8 screening asks how often eight specific problems (such as reduced interest, depressed mood, poor sleep, low energy, or appetite change) occurred over the past 14 days on a 0–3 scale ('not at all' to 'nearly every day'), giving a total score from 0 to 24 [1, 2]. Emotional tone in a single message and symptom frequency over two weeks therefore measure different things.",
    )
    _add_p(
        doc,
        "In everyday English or Hong Kong Cantonese dialogue, relying on sentiment alone breaks down in two common situations: (1) Situational Distress, where a user vents frustration about an immediate hassle (such as pouring rain or a group-project dispute) while their two-week sleep, energy, and mood are normal (causing false positives); and (2) Masked / Matter-of-Fact Somatic Reporting, where a user calmly states high two-week counts of insomnia, fatigue, and poor concentration without emotional words (causing false negatives). Our Dual-Channel ('Two-Ear') Chatbot separates these two signals so emotional tone improves conversational warmth without ever distorting PHQ-8 scores.",
    )
    _add_p(
        doc,
        "To keep our Semester 1 investigation focused and coherent, we organize our system evaluation around three connected Research Questions (Table 1):",
    )

    _add_styled_table(
        doc,
        [
            "Research Question",
            "Evaluation & Baselines",
            "Main Finding & Role in Storyline",
        ],
        [
            [
                "RQ1: How do classical ML sentiment baselines perform, and why does sentiment polarity fail as a direct PHQ-8 proxy?",
                "Exp 1A: TweetEval splits (N = 12,284; Majority, Naive Bayes, Logistic Reg., Linear SVM).\nExp 1B: 48-case bilingual stress test.",
                "Linear SVM / LR reach ~0.561 Macro-F1 on English tweets but fail on Chinese; even 100% perfect sentiment gets 0% proxy accuracy on Situational Distress & Masked Somatic.",
            ],
            [
                "RQ2: Can a quote-checked conversational extractor handle bilingual & HK code-switched answers while abstaining on vague inputs?",
                "Exp 2: 80 fictional bilingual turns (64 standard + 16 HK code-switched / trap cases) vs. Keyword, calibrated TF-IDF+LR, and Rule Baseline.",
                "Forced ML suffers 100% false acceptances on vague/old-window turns; our chatbot reaches 98.8% on this rule-set (93.8% on HK stress cases) with concrete error analysis.",
            ],
            [
                "RQ3: Does the complete bilingual chatbot preserve user control and score invariance across multi-turn screening?",
                "Exp 3: 4 live multi-turn bilingual walkthroughs + 234 automated unit/UI checks on scoring, quotes, and safety interruption.",
                "All 4 scenarios complete review and scoring accurately; local PHQ-8 totals remain 100% unchanged across 800 sentiment perturbations.",
            ],
        ],
        [2.05, 2.15, 2.30],
        "Table 1. Semester 1 Research Questions Mapped to Experiments and Core Findings.",
        keep_together=True,
    )

    # ==========================================================================
    # Section 2: Literature Review
    # ==========================================================================
    doc.add_heading("2. Literature Review", level=1)
    _add_p(
        doc,
        "Kroenke et al. [1] evaluated PHQ-8 in a survey of 198,678 adults, reporting similar population prevalence under symptom-algorithm and score >= 10 definitions. We consulted the indexed PubMed abstract of [1] rather than the full article; as that abstract notes, PHQ-8 was not validated against a structured psychiatric interview in that survey, so totals represent self-reported symptom summaries rather than clinical diagnoses. Dhingra et al. [2] studied day-count PHQ-8 responses and documented the R1 conversion from 14-day counts into the four 0–3 categories: 0–1 days -> 0, 2–6 days -> 1, 7–11 days -> 2, and 12–14 days -> 3 (separate from their 0–112 day sum). Because 1 reported day maps to category 0 despite symptom presence, showing the user's original words during review is important, and ranges crossing a threshold (such as '6–7 days') require follow-up rather than rounding.",
    )
    _add_p(
        doc,
        "For sentiment classification, TweetEval [3] standardizes SemEval-2017 Twitter splits [12] across negative, neutral, and positive labels using macro-averaged recall. GoEmotions [9] annotates 58,000 Reddit comments with 27 emotion categories, showing finer emotional granularity, yet neither dataset contains past-two-week symptom frequencies. Clinical interview corpora such as DAIC-WOZ [8] include PHQ-8 scores alongside interview transcripts, but require institutional licensing beyond Semester 1.",
    )
    _add_p(
        doc,
        "In healthcare chatbots, Laranjo et al. [4] found across 17 studies that structured state control remained standard because unconstrained generation risks unsafe behavior. Fitzpatrick et al. [5] showed feasibility for the Woebot CBT agent among 70 young adults while noting user frustration with rigid, repetitive replies and misunderstood free text. Geifman and El-Yaniv [6] framed selective classification as trading coverage against error risk among accepted predictions, while Guo et al. [7] showed that model confidence scores can be poorly calibrated. These findings directly motivate allowing natural multi-symptom input while abstaining on unclear wording and requiring user confirmation before scoring.",
    )

    # ==========================================================================
    # Section 3: System Design and Implementation
    # ==========================================================================
    doc.add_heading("3. System Design and Implementation", level=1)
    _add_p(
        doc,
        "Our main deliverable is a connected Streamlit web application supporting Traditional Chinese/Cantonese and English natural conversation, alongside our retained offline per-item rule questionnaire for baseline comparison. Figure 1 illustrates why the system splits incoming messages into two separate channels rather than feeding sentiment into the score.",
    )

    _add_figure(
        doc,
        fig_dir / "fig1_clean_architecture.png",
        "Figure 1. Workflow of the Dual-Channel Preliminary Screening Chatbot, keeping emotional tone separate from quote-backed PHQ-8 symptom extraction and user-confirmed 0–24 scoring.",
        width_in=6.35,
    )

    _add_p(
        doc,
        "Before any external API request is sent, a lightweight pre-API filter checks for explicit demonstration interrupt markers; if triggered, it clears the session immediately without sending text over the network (serving as a workflow safety test rather than a clinical crisis detector). For normal messages, the chatbot communicates with a configured OpenAI-compatible Responses endpoint [10, 11] (which reports the model identifier gpt-6.1-terra via our third-party gateway) using a strict JSON output schema.",
    )
    _add_p(
        doc,
        "In the Affect Channel (Left Ear), the assistant labels each user turn as negative, neutral, positive, or unclear so it can offer a brief empathetic sentence before asking at most one follow-up question, while displaying turn-tone counts in the sidebar strictly as non-scoring context. In the Symptom Channel (Right Ear), each proposed PHQ-8 item update must attach a past-14-day timeframe label and a word-for-word substring quote from the user's message; local validation rejects any fabricated quote or out-of-window score. Vague phrases ('sometimes', '間唔中') or boundary-straddling ranges ('6–7 days') remain unresolved (null) so the chatbot asks a clarifying question. Once all eight items have valid proposals, the user inspects every quote and can edit any 0–3 dropdown in a batch review panel before ticking explicit confirmation. Only those eight confirmed integers are summed into the 0–24 PHQ-8 total, after which a post-session note highlights whether tone and symptom burden were aligned or divergent.",
    )

    # ==========================================================================
    # Section 4: Experiment 1 (Left Ear)
    # ==========================================================================
    doc.add_heading(
        "4. Experiment 1: Sentiment Baselines and Controlled Mismatch Stress Test",
        level=1,
    )
    _add_p(
        doc,
        "To answer RQ1, Experiment 1A trained four classical scikit-learn baselines on the pinned TweetEval sentiment splits (45,615 train, 2,000 validation, 12,284 held-out test) [3]: Majority, Multinomial Naive Bayes, Logistic Regression, and Linear SVM, using TF-IDF word unigrams and bigrams (up to 50,000 features) selected on validation Macro-F1.",
    )

    _add_styled_table(
        doc,
        [
            "Model (Selected Hyperparameter)",
            "Val Macro-F1",
            "Test Acc",
            "Test Macro-F1",
            "Test Macro-Recall",
            "Neg. Recall",
            "Fit (s)",
        ],
        [
            [
                "Majority Baseline",
                _f3(m_maj["val_macro_f1"]),
                _f3(m_maj["accuracy"]),
                _f3(m_maj["macro_f1"]),
                _f3(m_maj["macro_recall"]),
                _f3(m_maj["negative_recall"]),
                f"{m_maj['fit_seconds']:.2f}",
            ],
            [
                f"TF-IDF + Multinomial NB (alpha={m_nb['selected_param']})",
                _f3(m_nb["val_macro_f1"]),
                _f3(m_nb["accuracy"]),
                _f3(m_nb["macro_f1"]),
                _f3(m_nb["macro_recall"]),
                _f3(m_nb["negative_recall"]),
                f"{m_nb['fit_seconds']:.2f}",
            ],
            [
                f"TF-IDF + Logistic Regression (C={m_lr['selected_param']})",
                _f3(m_lr["val_macro_f1"]),
                _f3(m_lr["accuracy"]),
                _f3(m_lr["macro_f1"]),
                _f3(m_lr["macro_recall"]),
                _f3(m_lr["negative_recall"]),
                f"{m_lr['fit_seconds']:.2f}",
            ],
            [
                f"TF-IDF + Linear SVM (C={m_svm['selected_param']})",
                _f3(m_svm["val_macro_f1"]),
                _f3(m_svm["accuracy"]),
                _f3(m_svm["macro_f1"]),
                _f3(m_svm["macro_recall"]),
                _f3(m_svm["negative_recall"]),
                f"{m_svm['fit_seconds']:.2f}",
            ],
        ],
        [2.10, 0.78, 0.72, 0.80, 0.88, 0.68, 0.54],
        "Table 2. Experiment 1A Held-Out Results on Official TweetEval Sentiment Splits (Test N = 12,284).",
    )

    _add_p(
        doc,
        f"Linear SVM and Logistic Regression improved test Macro-F1 by +{_f3(boot_svm_maj['mean_diff'])} over Majority (500-resample paired bootstrap 95% CI [{_f3(boot_svm_maj['ci95_low'])}, {_f3(boot_svm_maj['ci95_high'])}]) with virtually identical accuracy to each other (difference {_f3(boot_svm_lr['mean_diff'])}), though negative-class recall reached only {_f3(m_svm['negative_recall'])}.",
    )
    _add_p(
        doc,
        "Because Semester 1 does not involve human-subject data, Experiment 1B designed a 48-sentence controlled bilingual stress test (24 English + 24 Traditional Chinese/Cantonese; 12 sentences in each of Congruent Low, Situational Distress, Masked Somatic, and Congruent Elevated), where both group members checked each sentence's reference tone label and underlying PHQ-8 profile total. Table 3 and Figure 2 compare sentiment accuracy against the naive screening rule 'Negative Sentiment => PHQ-8 >= 10'.",
    )

    _add_styled_table(
        doc,
        [
            "Model",
            "EN Sent. Acc",
            "ZH Sent. Acc",
            "All Sent. Acc",
            "Overall PHQ Proxy Acc",
            "Situational Distress Proxy Acc",
            "Masked Somatic Proxy Acc",
        ],
        [
            [
                "TweetEval TF-IDF + Multinomial NB",
                _pct(e1b_models["tfidf_multinomial_nb"]["en_polarity"]["accuracy"]),
                _pct(e1b_models["tfidf_multinomial_nb"]["zh_polarity"]["accuracy"]),
                _pct(
                    e1b_models["tfidf_multinomial_nb"]["overall_polarity"]["accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_multinomial_nb"][
                        "naive_negative_implies_elevated_phq8"
                    ]["proxy_accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_multinomial_nb"][
                        "naive_negative_implies_elevated_phq8"
                    ]["by_quadrant"]["situational_distress"]["naive_screening_accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_multinomial_nb"][
                        "naive_negative_implies_elevated_phq8"
                    ]["by_quadrant"]["masked_somatic"]["naive_screening_accuracy"]
                ),
            ],
            [
                "TweetEval TF-IDF + Logistic Regression",
                _pct(
                    e1b_models["tfidf_logistic_regression"]["en_polarity"]["accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_logistic_regression"]["zh_polarity"]["accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_logistic_regression"]["overall_polarity"][
                        "accuracy"
                    ]
                ),
                _pct(
                    e1b_models["tfidf_logistic_regression"][
                        "naive_negative_implies_elevated_phq8"
                    ]["proxy_accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_logistic_regression"][
                        "naive_negative_implies_elevated_phq8"
                    ]["by_quadrant"]["situational_distress"]["naive_screening_accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_logistic_regression"][
                        "naive_negative_implies_elevated_phq8"
                    ]["by_quadrant"]["masked_somatic"]["naive_screening_accuracy"]
                ),
            ],
            [
                "TweetEval TF-IDF + Linear SVM",
                _pct(e1b_models["tfidf_linear_svm"]["en_polarity"]["accuracy"]),
                _pct(e1b_models["tfidf_linear_svm"]["zh_polarity"]["accuracy"]),
                _pct(e1b_models["tfidf_linear_svm"]["overall_polarity"]["accuracy"]),
                _pct(
                    e1b_models["tfidf_linear_svm"][
                        "naive_negative_implies_elevated_phq8"
                    ]["proxy_accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_linear_svm"][
                        "naive_negative_implies_elevated_phq8"
                    ]["by_quadrant"]["situational_distress"]["naive_screening_accuracy"]
                ),
                _pct(
                    e1b_models["tfidf_linear_svm"][
                        "naive_negative_implies_elevated_phq8"
                    ]["by_quadrant"]["masked_somatic"]["naive_screening_accuracy"]
                ),
            ],
            [
                "Connected LLM (Terra Sentiment)",
                _pct(live_e1b["en_polarity"]["accuracy"]),
                _pct(live_e1b["zh_polarity"]["accuracy"]),
                _pct(live_e1b["overall_polarity"]["accuracy"]),
                _pct(
                    live_e1b["naive_negative_implies_elevated_phq8"]["proxy_accuracy"]
                ),
                _pct(
                    live_e1b["naive_negative_implies_elevated_phq8"]["by_quadrant"][
                        "situational_distress"
                    ]["naive_screening_accuracy"]
                ),
                _pct(
                    live_e1b["naive_negative_implies_elevated_phq8"]["by_quadrant"][
                        "masked_somatic"
                    ]["naive_screening_accuracy"]
                ),
            ],
            [
                "100% Perfect Sentiment Reference",
                "100.0%",
                "100.0%",
                "100.0%",
                _pct(
                    oracle_e1b["naive_negative_implies_elevated_phq8"]["proxy_accuracy"]
                ),
                _pct(
                    oracle_e1b["naive_negative_implies_elevated_phq8"]["by_quadrant"][
                        "situational_distress"
                    ]["naive_screening_accuracy"]
                ),
                _pct(
                    oracle_e1b["naive_negative_implies_elevated_phq8"]["by_quadrant"][
                        "masked_somatic"
                    ]["naive_screening_accuracy"]
                ),
            ],
        ],
        [1.90, 0.68, 0.68, 0.70, 0.82, 0.86, 0.86],
        "Table 3. Experiment 1B Controlled Bilingual Stress Test (N = 48; All Columns Report Accuracy — Higher is Better).",
    )

    _add_figure(
        doc,
        fig_dir / "fig2_clean_e1_sentiment.png",
        "Figure 2. (a) Public TweetEval test scores. (b) Controlled bilingual stress test showing that even 94%–100% sentiment accuracy drops to 0%–8% screening accuracy on Situational Distress and Masked Somatic cases.",
        width_in=6.35,
    )

    _add_p(
        doc,
        "As shown in Table 3 and Figure 2(b), English-trained TF-IDF models defaulted to neutral on Chinese script (37.5% accuracy), whereas the connected LLM reached 95.8% in English and 91.7% in Chinese (three mild boundary disagreements where calm routine sentences or a mixed Cantonese complaint ending with '放假去打波都好投入' were labeled positive). More importantly, even 100% perfect sentiment achieved 0.0% screening accuracy on Situational Distress and 0.0% on Masked Somatic cases (50.0% overall), demonstrating why a dedicated symptom-extraction channel is essential.",
    )

    # ==========================================================================
    # Section 5: Experiment 2 (Right Ear + HK Stress Cases & Error Analysis)
    # ==========================================================================
    doc.add_heading(
        "5. Experiment 2: Bilingual Symptom Extraction, Abstention, and Error Analysis",
        level=1,
    )
    _add_p(
        doc,
        "To answer RQ2, we constructed an 80-utterance bilingual test set balanced across the eight PHQ-8 domains (40 English + 40 Cantonese/Traditional Chinese; 40 resolvable answers + 40 must-abstain inputs) and verified zero SHA-256 text overlap against a separate 320-sentence bilingual training set (80 per category 0–3) used to fit a word+character TF-IDF + 5-fold calibrated Logistic Regression baseline. Alongside 64 standard cases (canonical choices, exact day counts, colloquial answers, timeframe contrasts, vague words like 'sometimes'/'間唔中', past-year episodes, boundary-crossing '6–7 days', and pure venting), we included 16 harder Hong Kong student stress cases with Cantonese–English code-switching ('呢 two weeks 逢禮拜一至五返 intern 都 tired 到死'), sarcasm, weekly rates ('三至四晚一個禮拜' = 6–8 nights straddling 6|7), and past-fortnight traps ('上次 mid-term 嗰 two weeks').",
    )

    _add_styled_table(
        doc,
        [
            "Method (N = 80 Test Utterances)",
            "Coverage",
            "Selective Risk",
            "Resolvable Exact",
            "Abstention Recall",
            "Standard-64 Acc",
            "HK-Hard-16 Acc",
            "All-80 Acc",
        ],
        [
            [
                "Naive Keyword Matcher",
                _pct(e2m["naive_keyword_heuristic"]["coverage"]),
                _pct(e2m["naive_keyword_heuristic"]["selective_risk"]),
                _pct(e2m["naive_keyword_heuristic"]["resolvable_exact_rate"]),
                _pct(e2m["naive_keyword_heuristic"]["abstention_recall"]),
                "54.7%",
                "50.0%",
                _pct(e2m["naive_keyword_heuristic"]["joint_end_to_end_accuracy"]),
            ],
            [
                "Calibrated TF-IDF + LR (Forced, tau=0.0)",
                _pct(e2m["tfidf_calibrated_lr_forced"]["coverage"]),
                _pct(e2m["tfidf_calibrated_lr_forced"]["selective_risk"]),
                _pct(e2m["tfidf_calibrated_lr_forced"]["resolvable_exact_rate"]),
                _pct(e2m["tfidf_calibrated_lr_forced"]["abstention_recall"]),
                "35.9%",
                "12.5%",
                _pct(e2m["tfidf_calibrated_lr_forced"]["joint_end_to_end_accuracy"]),
            ],
            [
                "Calibrated TF-IDF + LR (Threshold tau=0.60)",
                _pct(e2m["tfidf_calibrated_lr_tau_060"]["coverage"]),
                _pct(e2m["tfidf_calibrated_lr_tau_060"]["selective_risk"]),
                _pct(e2m["tfidf_calibrated_lr_tau_060"]["resolvable_exact_rate"]),
                _pct(e2m["tfidf_calibrated_lr_tau_060"]["abstention_recall"]),
                "59.4%",
                "43.8%",
                _pct(e2m["tfidf_calibrated_lr_tau_060"]["joint_end_to_end_accuracy"]),
            ],
            [
                "Offline Rule Baseline",
                "0.0%",
                "N/A (0 accepted)",
                "0.0%",
                "100.0%",
                "50.0%",
                "50.0%",
                "50.0%",
            ],
            [
                "Connected Chatbot (Dual-Channel)",
                _pct(live_e2["coverage"]),
                _pct(live_e2["selective_risk"]),
                _pct(live_e2["resolvable_exact_rate"]),
                _pct(live_e2["abstention_recall"]),
                _pct(live_e2["core_64_joint_accuracy"]),
                _pct(live_e2["hard_16_joint_accuracy"]),
                _pct(live_e2["joint_end_to_end_accuracy"]),
            ],
        ],
        [1.82, 0.60, 0.82, 0.68, 0.68, 0.65, 0.65, 0.60],
        "Table 4. Experiment 2 Symptom Extraction and Selective Abstention Across 80 Bilingual Test Utterances.",
    )

    _add_figure(
        doc,
        fig_dir / "fig3_clean_e2_extraction.png",
        "Figure 3. (a) Risk–Coverage curve on 80 bilingual turns. (b) Accuracy comparison between the 64 standard cases and 16 Hong Kong code-switched & trap stress cases.",
        width_in=6.35,
    )

    _add_p(
        doc,
        "Table 4 and Figure 3 illustrate why simple classifiers struggle with conversational screening. Forced TF-IDF + Logistic Regression guessed an integer on every turn (0.0% abstention), falling to 12.5% accuracy on the 16 HK stress cases; even with a 0.60 confidence threshold (56.2% overall), bag-of-words features could not distinguish '12 days during past quarantine' from '12 days in the past two weeks'. Conversely, our offline Rule Baseline (designed for bare option strings where it previously accepted 24/64 template inputs) accepted 0/80 multi-clause chat sentences, leaving selective risk undefined (N/A). Our connected chatbot achieved 98.8% (79/80) on this structured rule-compliance set (93.8% on the 16 stress cases) with 0.0% false acceptances and 100% verbatim quote matches—though accuracy on unscripted real-user conversations would naturally be lower. Table 5 examines four representative failure mechanisms.",
    )

    _add_styled_table(
        doc,
        [
            "Case & Utterance Excerpt",
            "Expected",
            "Observed Output",
            "Why the Error Happened",
        ],
        [
            [
                "E2H_07 (Chatbot): '原本想講呢兩星期日日都冇 mood 玩…其實只係返嚟呢三日提唔起勁啫'",
                "1 (3 days)",
                "Chatbot -> null\n(asked to confirm)",
                "Over-cautious abstention: because the prompt asks for clarification when users retract an answer, mid-sentence self-correction triggered '即係大約3日，係咪咁？' instead of direct extraction.",
            ],
            [
                "E2H_03 (TF-IDF+LR & Keyword): '呢 two weeks 逢禮拜一至五返 intern 都 tired 到死，兩個 weekend 共四日先唔攰'",
                "2 (10 days)",
                "LR -> 1 (p=0.65)\nKeyword -> 1",
                "Negated-clause number trap: lexical models latched onto '四日' (4 rest days NOT tired) rather than inferring 10 tired weekdays.",
            ],
            [
                "E2H_08 (TF-IDF+LR): '…just that single Tuesday night last week when I felt hopeless, only 1 day out of 14'",
                "0 (1 day -> R1 0)",
                "LR -> 3 (p=0.90)\nKeyword -> 1",
                "Number leakage & R1 boundary: the token '14' pushed LR strongly to class 3, while Keyword missed that 1 day maps to category 0 under Dhingra et al. [2].",
            ],
            [
                "E2H_16 (TF-IDF+LR): 'Haha yeah totally loving group projects right now, staring at messy slides at midnight is peak joy'",
                "Abstain (null)",
                "LR -> 0 (p=0.88)",
                "Sarcasm without frequency: surface positive words ('loving', 'joy') gave high class-0 confidence despite no two-week count.",
            ],
        ],
        [2.05, 0.75, 0.98, 2.72],
        "Table 5. Error Analysis of Representative Failure Cases on Hong Kong Code-Switched and Colloquial Inputs.",
    )

    # ==========================================================================
    # Section 6: Experiment 3 (Multi-Turn Walkthroughs & Software Verification)
    # ==========================================================================
    doc.add_heading(
        "6. Experiment 3: Multi-Turn Chatbot Walkthroughs and Safety Verification",
        level=1,
    )
    _add_p(
        doc,
        "To address RQ3, we ran four live multi-turn bilingual screening scenarios end-to-end through the chatbot (Table 6 and Figure 4) and verified our local scoring and safety rules across 234 automated tests (Table 7).",
    )

    readable_names = {
        "S1_zh_situational_distress": "Scenario 1: Cantonese Daily Hassle Venting",
        "S2_en_masked_somatic_clarification": "Scenario 2: English Matter-of-Fact Somatic + Follow-Up",
        "S3_zh_timeframe_guard_and_override": "Scenario 3: Past-Winter Filter + User Review Edit",
        "S4_en_congruent_elevated_invariance": "Scenario 4: High Distress & Score-Invariance Check",
    }
    readable_notes = {
        "situational_distress": "Situational Distress",
        "masked_somatic": "Masked Somatic",
        "congruent_low": "Congruent Low",
        "congruent_elevated": "Congruent Elevated",
    }
    s_rows = []
    for s in e3_sessions:
        cr = s["confirmed_result"] or {}
        s_rows.append(
            [
                readable_names.get(s["session_label"], s["session_label"]),
                s["language"].upper(),
                str(s["user_turns_executed"]),
                "8/8 verbatim" if s["all_quotes_exact_substring"] else "Failed",
                f"{cr.get('total')}/24 ({cr.get('band')})",
                readable_notes.get(
                    str(s["observed_quadrant"]), str(s["observed_quadrant"])
                ),
            ]
        )

    _add_styled_table(
        doc,
        [
            "Walkthrough Scenario",
            "Lang",
            "Turns",
            "Quote Check",
            "Confirmed Score",
            "Post-Session Tone Note",
        ],
        s_rows,
        [2.25, 0.50, 0.52, 0.90, 1.15, 1.18],
        "Table 6. Summary of Four Live Multi-Turn Bilingual Screening Walkthroughs.",
    )

    _add_figure(
        doc,
        fig_dir / "fig4_chatbot_4stage_flow.png",
        "Figure 4. Four-stage walkthrough of Scenario 2 illustrating multi-symptom input, follow-up clarification on 'occasionally', quote-backed batch review, and confirmed 11/24 score with Masked Somatic note.",
        width_in=6.35,
    )

    _add_p(
        doc,
        "Across all four walkthroughs, the chatbot preserved exact original-language quotes, ignored out-of-window winter insomnia in Scenario 3 while respecting manual user score edits at review, and confirmed deterministic PHQ-8 totals. In Table 7, our Score Invariance check confirms at the software level that the local scoring function ignores stored sentiment labels completely (800/800 identical totals when flipping stored turn sentiments); note, however, that during live chat a single LLM call generates both the reply tone and candidate item updates, so their statistical independence in model generation is not claimed.",
    )

    _add_styled_table(
        doc,
        ["Software Boundary Check", "Test Scope", "Observed Failures", "Outcome"],
        [
            [
                "Local Scoring Invariance to Stored Sentiment",
                f"{e3_audits['affect_score_invariance']['configurations_tested']} (200 PHQ vectors × 4 tone traces)",
                "0 score changes",
                "800 / 800 Pass",
            ],
            [
                "Fabricated Quote, Bad Timeframe & Schema Rejection",
                f"{e3_audits['adversarial_quote_and_schema_audit']['adversarial_payloads_tested']} malformed model payloads",
                "0 unrejected payloads",
                "24 / 24 Rejected",
            ],
            [
                "Pre-API Demo Interrupt Clearing & Zero Network Leak",
                f"{e3_audits['pre_api_safety_guard_audit']['cases_tested']} interrupt / guard-error inputs",
                f"{e3_audits['pre_api_safety_guard_audit']['downstream_llm_calls_triggered']} external API calls",
                "12 / 12 Cleared",
            ],
            [
                "Complete Automated Unit & UI Test Suite",
                f"{test_count} repository checks",
                "0 failures",
                f"{test_count} / {test_count} Pass",
            ],
        ],
        [2.75, 1.65, 1.10, 1.00],
        "Table 7. Automated Verification of Scoring Boundaries, Quote Provenance, and Pre-API Interrupts.",
    )

    # ==========================================================================
    # Section 7: Limitations and Practical Challenges
    # ==========================================================================
    doc.add_heading("7. Limitations and Practical Challenges", level=1)
    _add_p(
        doc,
        "1. Fictional Stress Cases vs. Real Users: Apart from public TweetEval tweets, our 48-case and 80-case bilingual sets were written and checked by our team under explicit PHQ-8 rules to avoid collecting sensitive human data without ethics approval. Real users produce typos, fragmented replies, and unexpected topic shifts that will lower extraction accuracy below 98.8%.",
    )
    _add_p(
        doc,
        "2. API Turn Latency & Third-Party Gateway: Live structured-output calls took roughly 8 to 16 seconds per turn through the configured compatible endpoint, which feels slow during interactive chat and motivates testing smaller local models in Semester 2.",
    )
    _add_p(
        doc,
        "3. Quote Matching vs. Full Meaning & Mock Safety Filter: Checking that a quote appears verbatim in the user's message prevents hallucinated citations, but cannot guarantee that the model interpreted indirect idioms accurately—making user batch review essential. Likewise, our pre-API safety filter checks synthetic demo markers only and is not a real crisis detector.",
    )

    # ==========================================================================
    # Section 8: Semester 2 Plan, Work Division & Conclusion
    # ==========================================================================
    doc.add_heading(
        "8. Semester 2 Plan, Work Division, and Conclusion",
        level=1,
    )
    _add_styled_table(
        doc,
        ["Period (2027)", "Planned Semester 2 Work", "Target Outcome"],
        [
            [
                "January",
                "Double-blinded bilingual dataset: both members independently label 120–160 Cantonese code-switched & English turns and measure inter-annotator agreement (Cohen's kappa).",
                "Frozen blinded test set & disagreement analysis.",
            ],
            [
                "February",
                "Local open-weight model comparison: benchmark compact multilingual models locally (e.g., XLM-RoBERTa / Qwen-7B) against the cloud endpoint to cut turn latency below 2 seconds.",
                "Accuracy, abstention & latency benchmark.",
            ],
            [
                "Feb – March",
                "Follow-up question ordering: test whether combining early-turn tone cues with partial symptom answers improves which clarification question is asked next (keeping scoring unchanged).",
                "Turn-efficiency & clarification study.",
            ],
            [
                "March – April",
                "Role-play usability check & final thesis: compare fixed per-item questioning against dual-channel chat using fictional persona cards, and finalize the FYP thesis and presentation.",
                "Usability summary, final codebase & defense.",
            ],
        ],
        [1.15, 3.45, 1.90],
        "Table 8. Semester 2 Research Timeline (January – April 2027).",
        keep_together=True,
    )

    _add_p(
        doc,
        "LEE Ka Tung (1155212062) led literature review, TweetEval dataset preparation, classical ML baselines, and bilingual evaluation analysis; CHAN Kin Long (1155212039) led PHQ-8 scoring/safety boundary rules, multi-turn dialogue state management, and bilingual Streamlit UI integration, with both members jointly reviewing experiments and co-writing this report under Prof. Helen Meng's supervision.",
        bold_prefix="Work Division: ",
    )
    _add_p(
        doc,
        "In conclusion, Semester 1 produced a working bilingual Dual-Channel Preliminary Screening Chatbot backed by three coherent experiments demonstrating why sentiment polarity cannot replace two-week symptom grounding, how quote-verified extraction with selective abstention handles standard and Hong Kong code-switched inputs, and how mandatory user review keeps PHQ-8 scoring transparent and reliable.",
        bold_prefix="Conclusion: ",
    )

    doc.add_heading("References", level=1)
    refs = [
        '[1] K. Kroenke, T. W. Strine, R. L. Spitzer, J. B. W. Williams, J. T. Berry, and A. H. Mokdad, "The PHQ-8 as a measure of current depression in the general population," Journal of Affective Disorders, vol. 114, pp. 163–173, 2009. doi: 10.1016/j.jad.2008.06.026. (Indexed PubMed abstract consulted: https://pubmed.ncbi.nlm.nih.gov/18752852/).',
        '[2] S. S. Dhingra, K. Kroenke, M. M. Zack, T. W. Strine, and L. S. Balluz, "PHQ-8 Days: a measurement option for DSM-5 Major Depressive Disorder (MDD) severity," Population Health Metrics, vol. 9, art. 11, 2011. doi: 10.1186/1478-7954-9-11.',
        '[3] F. Barbieri, J. Camacho-Collados, L. Neves, and L. Espinosa-Anke, "TweetEval: Unified Benchmark and Comparative Evaluation for Tweet Classification," Findings of EMNLP, pp. 1644–1650, 2020. doi: 10.18653/v1/2020.findings-emnlp.148.',
        '[4] L. Laranjo et al., "Conversational agents in healthcare: a systematic review," Journal of the American Medical Informatics Association, vol. 25, no. 9, pp. 1248–1258, 2018. doi: 10.1093/jamia/ocy072.',
        '[5] K. K. Fitzpatrick, A. Darcy, and M. Vierhile, "Delivering Cognitive Behavior Therapy to Young Adults With Symptoms of Depression and Anxiety Using a Fully Automated Conversational Agent (Woebot): A Randomized Controlled Trial," JMIR Mental Health, vol. 4, no. 2, e19, 2017. doi: 10.2196/mental.7785.',
        '[6] Y. Geifman and R. El-Yaniv, "Selective Classification for Deep Neural Networks," Advances in Neural Information Processing Systems (NeurIPS), vol. 30, 2017.',
        '[7] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On Calibration of Modern Neural Networks," Proceedings of ICML, PMLR, vol. 70, pp. 1321–1330, 2017.',
        '[8] J. Gratch et al., "The Distress Analysis Interview Corpus of human and computer interviews," Proceedings of LREC, pp. 3123–3128, 2014.',
        '[9] D. Demszky et al., "GoEmotions: A Dataset of Fine-Grained Emotions," Proceedings of ACL, pp. 4040–4054, 2020. doi: 10.18653/v1/2020.acl-main.372.',
        '[10] OpenAI, "Responses API Reference," OpenAI Platform Documentation, accessed Nov. 2026. https://platform.openai.com/docs/api-reference/responses. (Used for compatible HTTP request/response format; connected third-party gateway reported model identifier gpt-6.1-terra).',
        '[11] OpenAI, "Structured Model Outputs," OpenAI Platform Guide, accessed Nov. 2026. https://platform.openai.com/docs/guides/structured-outputs.',
        '[12] S. Rosenthal, N. Farra, and P. Nakov, "SemEval-2017 Task 4: Sentiment Analysis in Twitter," Proceedings of SemEval, pp. 502–518, 2017. doi: 10.18653/v1/S17-2088.',
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.26)
        p.paragraph_format.first_line_indent = Inches(-0.26)
        p.paragraph_format.space_after = Pt(2.2)
        r = p.add_run(ref)
        _set_east_asia_font(r, "Calibri", "PingFang HK")
        r.font.size = Pt(8.7)

    docx_path = out_dir / "Final_Report_T.docx"
    doc.save(str(docx_path))

    reopened = Document(str(docx_path))
    assert len(reopened.paragraphs) > 30
    assert len(reopened.tables) == 9
    assert any(
        "Sentiment Analysis for Depression Detection" in p.text
        for p in reopened.paragraphs
    )

    md_lines = [
        "# Sentiment Analysis for Depression Detection",
        "## A Dual-Channel Bilingual Chatbot for PHQ-8 Preliminary Screening",
        "**CUHK SEEM Final Year Project — Semester 1 Final Report (Group T)**  ",
        "**Members:** CHAN, Kin Long (1155212039) · LEE, Ka Tung (1155212062)  ",
        "**Supervisor:** Prof. Helen Meng · **Date:** 27 November 2026",
        "",
        "---",
        "",
    ]
    for p in reopened.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
        st = p.style.name if p.style else ""
        if st == "Heading 1":
            md_lines.extend([f"## {txt}", ""])
        elif st == "Heading 2":
            md_lines.extend([f"### {txt}", ""])
        else:
            md_lines.extend([txt, ""])
    md_path = out_dir / "report_source.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return {"docx": docx_path, "md": md_path}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "results" / "dual-channel-s1-v2-20261127" / "summary_v2.json",
    )
    parser.add_argument(
        "--figures",
        type=Path,
        default=ROOT / "docs" / "semester1_final" / "figures",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "docs" / "semester1_final",
    )
    parser.add_argument("--test-count", type=int, default=234)
    args = parser.parse_args()
    paths = build_reports(
        args.summary, args.figures, args.outdir, test_count=args.test_count
    )
    for k, p in paths.items():
        print(f"[REPORT-FINAL] {k}: {p}")


if __name__ == "__main__":
    main()
