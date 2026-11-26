# Bilingual conversation verification

26 November 2026. Base commit a65294a with local integration; Python 3.12.

## Automated checks

`python -m pytest -q`: 223 passed in 3.61s. This result was observed directly from the full suite after the bilingual changes; no live API calls are made by this suite.
`python -m ruff check .`: All checks passed.
`python -m ruff format --check .`: 95 files already formatted.

The three new bilingual tests cover English review/edit/result, preserving state and result across language switches, English failure/retry copy, and the provider language instruction while retaining original quotes. The earlier conversation tests cover the proposal and confirmation paths. No new statement coverage number is claimed.

## Connected English browser demonstration

Actual Streamlit app at 127.0.0.1:8501; English selected. Three fictional user turns through the configured compatible gateway, using service-reported gpt-6.1-terra. First turn described sleep and fatigue; second clarified low mood, fatigue and interest; third supplied the remaining domains and corrected sleep from ten nights to six. The review showed [0,1,1,2,0,0,1,0]. After the checkbox and confirmation button, the displayed total was 5/24. See english-review.txt, english-result.txt and english-result.jpg.

Earlier Chinese connected demonstration is in ../conversation/verification.md. These are functional demonstrations, not independent, representative or clinical evaluations. No conversation token/latency benchmark was collected. Fictional transcripts were deliberately captured as test evidence; the application itself does not persist conversations.

## Report review

Report updated to distinguish rule baseline, sentiment pilot and new bilingual chat. All four report figures are English. Numerical tables were checked against saved experiment JSON; full-text versus abstract-only literature access is disclosed. Report contains 12 references (nine research readings, one original dataset attribution and two API documents). Rendered 14-page DOCX/PDF visually inspected; no text clipping or broken tables observed. School-specific submission requirements and individual contribution declarations still require student verification.
