# Project map

## Run the system

- app.py: bilingual natural conversation, requires the configured compatible API.
- conversation.py: proposal validation, session flow, corrections and confirmed scoring.
- bilingual_provider.py and localization.py: language instructions and interface text.
- questionnaire_app.py: retained rule-based questionnaire baseline; can run offline.
- phq8_engine.py: deterministic sum of eight confirmed responses.
- terra_client.py: structured API transport; keys supplied in memory or environment.

## Reproduce and inspect

- README.md: installation, runtime and experiment commands.
- research/sentiment_benchmark.py: public English sentiment benchmark.
- research/diagnostic_cases.py: authored rule-parser diagnostic.
- research/sentiment_pilot.py: authored bilingual sentiment pilot.
- docs/evidence/: executed results, test logs and fictional browser demonstrations.
- docs/report/: current English report and figures.
- docs/literature/reading_matrix.md: research appraisal with source links.

Raw datasets, downloaded full papers, personal university forms and credentials are not part of the published repository. Results summaries are committed; full reproducibility outputs and the trained SVM are in the local delivery bundle or can be regenerated. The bilingual chat uses the remote model and does not require the SVM artifact.

Earlier architecture and verification documents describe the retained baseline. See docs/CONVERSATION_UPGRADE.md for the newer scope and requirements mapping. Clinical validation, independent multi-turn extraction evaluation and an operational crisis detector are not completed.
