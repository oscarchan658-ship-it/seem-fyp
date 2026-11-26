# Repository cleanup verification

Date: 2026-11-26 (Hong Kong). Baseline: `07ee3cf`.

## Changes

- Replaced the old architecture description with the connected bilingual chat data flow and current session/privacy boundaries.
- Updated README installation, endpoint configuration, offline baseline instructions and evidence navigation.
- Updated AGENTS.md to reflect the authorized connected fictional-chat scope.
- Removed the superseded 23 November integration and 25 November sprint implementation plans. Their original text remains in Git history. Retained dated measurements, comparison code and research preparation tools.
- Marked the baseline requirement matrix and NLU contract with their actual scope. Replaced stale claims that day-count mapping was not enabled.
- Removed references to unpublished paper-extraction files and corrected the submission-guidance status.
- Fixed the 40-turn boundary: additional messages cannot call the model, a complete summary can still be reviewed and scored, and a failed 40th turn can still be retried. Guard checks remain before the turn-cap return.

## Validation

- Dependency compatibility: `python -m pip check` passed.
- Ruff lint and format checks passed.
- Full suite: 226 tests passed, 85% aggregate statement coverage.
- Three regression tests cover complete/incomplete summaries at the cap, failed last-turn retry and the Streamlit review/result flow at the cap. Targeted chat and bilingual tests: 19 passed.
- Tracked Markdown relative links checked; no missing local link targets after adding this record.
- No live API experiments were rerun. Recorded model and benchmark results are unchanged. Automated API tests use mocked transport.

The report records its original 223-test snapshot; the additional three tests belong to this later maintenance change. No new clinical or model-accuracy claim follows from this cleanup.
