# Semester 1 evidence register

Execution date: 26 November 2026. Base Git commit: `a65294abdddf5fffa6a58ec53250b2ba12e3e47c`; integration is an uncommitted working tree on `codex/semester-report-evidence`. The delivery manifest hashes the actual source files. Earlier commit counts and old rehearsal results must not be combined with this run.

| Requirement or question | Implementation | Executed evidence |
|---|---|---|
| Confirmed unique answers only; sentiment independent | controller.py, scoring.py, sentiment_service.py | tests/test_sentiment_service.py and existing controller/scoring tests; tests.txt |
| Preserve source meaning for R1 day conversion | schemas.py, controller.py, answer_display.py, app.py | tests/test_answer_display.py |
| Guard before optional remote invocation | app.py send dispatch | test_sentiment_service interruption check |
| Reject invalid model output; fallback | terra_client.py, sentiment_service.py | tests/test_terra_client.py; two observed connection failures in pilot |
| RQ1 reproducible general sentiment | research/sentiment_benchmark.py | sentiment_metrics.json, sentiment_selection.json; full results in delivery |
| RQ2 accepted accuracy versus coverage | research/diagnostic_cases.py | parser_diagnostic.json; 64 AI-authored fixtures |
| Bilingual feasibility | research/sentiment_pilot.py, scripts/run_connected.py | terra_summary.json; 48 actual requests with failures retained |
| Live integration | Streamlit with configured third-party endpoint | prototype.jpg; fictional positive Chinese input, first item still in clarification |

Latest full pytest run: 207 passed in 6.94 s, 84% statements under existing coverage settings. Ruff check and format check passed; pip check reported no broken requirements. Runtime Python 3.12.14. Model training and data library versions are pinned in requirements-research.txt. The added serve_connected.py launcher was subsequently linted and CLI-help checked; it does not alter questionnaire logic.

Clinical validation, a real-user study, independently annotated E2, depression-label E1 and formal policy E3 are NOT RUN. SafetyGuard is a mock. The original 96-case annotation handoff is not present in this checkout.
