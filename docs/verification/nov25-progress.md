# Research Sprint execution ledger

Historical plan: the 25 November sprint checklist was removed during repository cleanup; it remains in Git history. Reproduction commands: ../reproducibility/research-sprint.md

Baseline: 502a86d. Date: 2026-11-25 JST.

- Ruling: Native worktree creation remained pending without a checkout. Created sibling Git worktree fyp-research-sprint on research/nov25-sprint to continue authorized implementation. Original plan retained in source checkout.
- Pre-flight: R1 must cross provider, schema, evidence checks, controller and policy replay. Local interval evidence must remain unavailable to untrusted model JSON.
- Pre-flight: Blind IDs require a private reversible mapping before existing compare/freeze can consume annotations. Coverage metadata stays outside annotation sheets.
- Human inputs pending: A/B labels, adjudication, authored Oracle replies, chosen model artifacts, Dataset A authorization and participant labels, FMEA ratings.
- Task 1: R1 local interval provenance implemented across provider, schema, evidence, controller, offline replay and sentiment-divergence features. RED→GREEN tests observed.
- Task 2: 96-case candidate generator, blinded A/B and followup issue/restore/freeze implemented. Gold columns stay empty. RED→GREEN tests observed.
- Task 3: Coverage-aware Development split, E2a/E2b metrics and sealed pairs, Validation threshold selection implemented. Existing annotation callers retained.
- Task 4: Local NLI/structured-worker/sentiment adapters, E1 controlled comparison, Oracle prediction freeze, E3 policy runner and fixed-grid risk coverage implemented. Model artifacts and human data remain external dependencies.
- Task 5: Separate synthetic rehearsal executed, benchmark and CSV-backed figures produced. Formal E1/E2/E3 remain NOT RUN. FMEA ratings remain blank.
- Review: Independent reviewer reproduced and reported six integration gaps. Fixed R1 JSON reconstruction, initial-turn threshold checks and model signatures, sealed E2b pair/author provenance, Oracle prediction freeze, risk coverage output and model-load NOT RUN records. Final review found no remaining Important issues; focused review regressions passed.
- Environment: Initial sandbox AppTest blocked in asyncio socketpair accept. Re-running with approved permissions passed; no application workaround introduced.
- Ruling: Deprecation in installed scikit-learn 1.9.1 made explicit penalty='l2' warn. Use its L2 default with the same fixed liblinear/C settings.
