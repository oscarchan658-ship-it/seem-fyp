# Sentiment Analysis for Depression Detection

- Keep the approved project title. Current behavior is documented in README.md, architecture.md and docs/CONVERSATION_UPGRADE.md. Earlier verification records describe dated snapshots, not current requirements.
- Use Python 3.12, Streamlit and pytest. The default entry point is app.py (bilingual connected chat); questionnaire_app.py retains the offline baseline used by the parser experiments.
- Scores come only from explicit confirmation of eight unique item IDs and strict integer values 0–3. Sentiment and model confidence cannot supply missing answers or change scores.
- Check the independent Guard before model interpretation. A non-normal decision or Guard failure clears the conversation and blocks scoring. The current Guard uses demonstration markers only; do not describe it as a crisis detector.
- Connected chat is authorized for fictional demonstrations. Keep history and source quotes in the current session only; send them only to the configured compatible API after the start consent. Do not persist chat text or secrets. Offline baseline and research tools have separate data contracts.
- Preserve public benchmark provenance and distinguish exploratory authored cases from independently annotated evaluation. Never infer clinical validity from software tests or sentiment metrics.
- Before publishing changes, run dependency checks, Ruff lint/format and the complete pytest suite. Add regression tests for behavior fixes. Record actual outcomes; never rewrite historical experiment results to match later software changes.
