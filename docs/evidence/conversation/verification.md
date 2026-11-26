# Conversational integration verification

Date: 26 November 2026 (Hong Kong). User-authorized scope change: natural multi-turn conversation with PHQ-8 evidence collection. Prior report remains a baseline snapshot; this update is separate.

Automated: 220 tests passed in 3.47 s, including 13 new conversation cases. Ruff check passed; 91 files passed format check. Tests cover multi-domain updates, historical context, quote validation, wrong timeframe, duplicate items, strict integer values, retracting candidates, transport failure/retry, guard-before-provider, explicit confirmation, stale review rejection, UI review and clearing. Transport in these tests is mocked.

Live gateway: use the documented browser smoke sequence below, with authored fictional input. This is a feasibility check, not an accuracy evaluation. All model outputs are displayed for manual checking. No claim of clinical validity, independent gold labels, or safety detection.

During initial upgrade the existing Streamlit process retained the old imported transport method; the new keyword argument failed before requests could run. Restarting the service loaded the updated client. The current launcher uses headless startup to avoid an invisible onboarding prompt. Errors now show a safe failure type and allow retry. No credential is written into the repository.

## Observed live smoke sequence

Three actual fictional user turns were sent through the configured Terra gateway in the browser:

1. Cantonese/Traditional Chinese description of assignment fatigue, ten nights of poor sleep, continuing interest in basketball. Observed: sleep candidate collected (1/8); assistant asked whether interest in other activities had decreased, rather than assuming absence from basketball alone.
2. Explicit absence of interest loss, ten days of low energy, about three days of low mood. Observed: 4/8 collected; assistant asked about appetite.
3. Explicit normal appetite, no guilt/failure, four days of poor concentration, no psychomotor change, correction of sleep to six nights. Observed: 8/8 and invitation to review. The review showed [0,1,1,2,0,0,1,0], with six-night correction and exact user quotes.
4. Checked confirmation and submitted review. Observed total: 5/24. Screenshot: chat-result.jpg. No automatic total before review.

This one successful sequence covers natural wording, contextual short answers, multiple domains and a correction. It does not establish accuracy over arbitrary conversations. The 220-test suite includes mocked provider outputs; these must be distinguished from the three actual model turns above.
