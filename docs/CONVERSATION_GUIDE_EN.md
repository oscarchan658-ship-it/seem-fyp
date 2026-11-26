# English conversation demo guide

The default app supports English and Traditional Chinese. This is a fictional research demonstrator, not a diagnosis or a validated bilingual PHQ-8 administration.

## Run

Use Python 3.12 and the requirements-research.txt dependencies. From the repository directory, run:

```bash
python scripts/serve_connected.py --base-url https://car.cheng-x.online/v1
```

The launcher requests the key without echoing it and does not save it to disk. Open http://127.0.0.1:8501 and select English in the Language sidebar. If the server is already running, use that page instead of starting a second server. Alternatively run `python -m streamlit run app.py` and enter the key in the session-only sidebar field.

## Demonstrate

1. Start a fictional conversation. Describe recent life in natural language. Several symptoms may appear in the same message.
2. Clarify missing frequencies over the past two weeks. The model should ask focused follow-ups rather than require a rigid numbered questionnaire.
3. Correct an earlier statement. Check that the review cites the correction and preserves the actual day count in the summary.
4. Once all eight frequencies are available, open Review summary. Read the summaries, original quotes and options. Edit any wrong option, check the confirmation box and submit.
5. Switch language using the sidebar. Existing messages and quotes retain their original wording; future replies use the selected language. Evidence and the confirmed total remain unchanged.

The recorded English demo used [0,1,1,2,0,0,1,0] after correcting sleep from ten nights to six, then displayed 5/24 after confirmation. This is one functional check, not an accuracy estimate. The app requires a working compatible API. Failed requests expose a retry action and do not create new candidates or scores. A 40-turn limit bounds the conversation.

## Understand the evidence

The public TweetEval experiment evaluates English sentiment, the 64 authored parser cases evaluate the retained rule baseline, and the 48 authored bilingual pilot sentences evaluate single-sentence sentiment. None measures the new multi-turn extraction accuracy. The current automated suite has 223 passing tests, including mocked transport. The independent guard recognizes demonstration markers only and cannot detect ordinary crisis language.

The full English report, literature reading matrix, saved model results and Chinese explanation are included in the delivery bundle. `questionnaire_app.py` retains the earlier offline questionnaire baseline.
