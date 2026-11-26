# Literature extraction and design evidence

Accessed 26 November 2026. This is a focused narrative review, not a systematic search. Papers were selected for questionnaire measurement, sentiment benchmarking, conversational health systems and abstention. Source PDFs/HTML are retained in the delivery's `sources` directory; extracted text is in `seem-fyp/docs/literature/source_text`. Paraphrases below are not direct quotations. Original research findings are never presented as results of this FYP.

## 1 Kroenke et al 2009

**The PHQ-8 as a measure of current depression in the general population.** Journal of Affective Disorders 114, 163–173. DOI: https://doi.org/10.1016/j.jad.2008.06.026 . PMID 18752852.

**Read:** indexed abstract through Europe PMC; full paper not obtained. The review must not imply a full-text appraisal of this source.

**Method and evidence:** telephone BRFSS survey, 198,678 respondents. Compared PHQ-8 algorithm and score threshold definitions, reporting similar prevalence estimates (9.1% and 8.6%) and associations with impairment.

**Limit:** the abstract explicitly states that the questionnaire algorithm, rather than an independent structured psychiatric interview, was the criterion standard. Findings in that population do not validate this software or a translated conversational administration.

**Design consequence:** keep eight self-reported symptom-frequency values separate from sentiment. Treat the total as a questionnaire-derived summary. Do not report sentiment F1 as depression accuracy. Do not infer absence of immediate risk from a low total.

## 2 Dhingra et al 2011

**PHQ-8 Days: a measurement option for DSM-5 Major Depressive Disorder (MDD) severity.** Population Health Metrics 9, 11. DOI: https://doi.org/10.1186/1478-7954-9-11 . Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC3108293/ .

**Read:** Methods (Survey and measures), Results, Discussion and limitations in full-text HTML.

**Method and evidence:** analysis of BRFSS day-count responses. The Methods record a previous conversion from 0–1, 2–6, 7–11 and 12–14 days to the four ordinal categories. The article also studies a separate 0–112 days total; that total is NOT the 0–24 score implemented here.

**Limit:** the reference criterion is derived from questionnaire symptom criteria; this is not independent validation of the current prototype. Interpretation of a range or approximate count still requires choices. Our ±1 rule for approximate counts is an engineering convention, not a rule established by this paper.

**Design consequence:** retain the cited R1 conversion, expose the original structured day interval during review, and label its conversion. One day can map to category zero while still indicating symptom presence. A bare display of “not at all” would erase this distinction. Added regression checks exercise preservation, editing and clearing of that evidence.

## 3 Barbieri et al 2020

**TweetEval: Unified Benchmark and Comparative Evaluation for Tweet Classification.** Findings of EMNLP, 1644–1650. DOI: https://doi.org/10.18653/v1/2020.findings-emnlp.148 . PDF: https://aclanthology.org/2020.findings-emnlp.148.pdf .

**Read:** PDF pp. 2–4: tasks, Table 2, §2.2 metrics, baselines and Table 3; introduction and discussion.

**Method and evidence:** seven classification tasks with fixed splits; sentiment is positive/neutral/negative. The sentiment task uses macro-averaged recall, whereas most other tasks use macro-F1. The published SVM uses both word and character features.

**Limit:** Twitter language, labels and population differ from a health conversation. The paper's Table 2 counts differ from the downloaded repository version. Our manifest records the actual downloaded counts and SHA; we do not present this as an exact reproduction of its SVM.

**Design consequence:** preserve official train/validation/test files; select settings on validation; report Macro Recall alongside Macro-F1, accuracy and class-specific errors. Use a majority comparator. Our word-only SVM is a transparent lower-cost baseline, not a state-of-the-art claim.

## 4 Laranjo et al 2018

**Conversational agents in healthcare: a systematic review.** JAMIA 25, 1248–1258. DOI: https://doi.org/10.1093/jamia/ocy072 . Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC6118869/ .

**Read:** abstract, methods, discussion, strengths and limitations, conclusion. The review retrieved 1,513 citations and included 17 articles describing 14 agents. Finite-state and frame-based dialogue management were common. Patient safety was rarely evaluated.

**Limit:** the review concerns an earlier period and does not assess contemporary GPT models. It cannot prove effectiveness of this project.

**Design consequence:** explicit states and fallback paths are defensible engineering choices. Separate technical reliability, interpretation accuracy, usability and clinical efficacy. Report the demo guard as a mock, not a tested crisis classifier.

## 5 Fitzpatrick et al 2017

**Delivering Cognitive Behavior Therapy to Young Adults With Symptoms of Depression and Anxiety Using a Fully Automated Conversational Agent (Woebot): A Randomized Controlled Trial.** JMIR Mental Health 4(2), e19. DOI: https://doi.org/10.2196/mental.7785 . Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC5478797/ .

**Read:** Methods, Results, qualitative process feedback and Limitations. The unblinded feasibility trial randomized 70 young adults to two weeks of conversational CBT or an information-only control. It reports a difference in PHQ-9 change; users also reported failures to understand unexpected responses and repetitive dialogue.

**Limit:** small, short intervention with no longer-term follow-up; treatment content differs between arms. The study does not isolate the value of sentiment classification and is not a PHQ-8 data-collection experiment.

**Design consequence:** motivates measuring misunderstandings and repetition, not claims that our chatbot treats depression. A future user study should isolate interface changes with equivalent content rather than borrowing Woebot's efficacy claim.

## 6 Geifman and El-Yaniv 2017

**Selective Classification for Deep Neural Networks.** NeurIPS 30. PDF: https://proceedings.neurips.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf .

**Read:** PDF pp. 1–3, motivation and risk/coverage framework; experimental context.

**Evidence:** selective prediction trades coverage for prediction risk; demonstrated with image classifiers.

**Limit:** its guarantees do not automatically apply to our rule parser or GPT. Clarification is an interaction, not merely rejecting a sample.

**Design consequence:** report coverage and accepted-candidate errors together. A parser that rejects every input is not useful merely because it makes no accepted errors. Our synthetic diagnostic contrasts a simple keyword matcher with the existing context-aware rule system without claiming the paper's risk guarantee.

## 7 Guo et al 2017

**On Calibration of Modern Neural Networks.** ICML, PMLR 70, 1321–1330. https://proceedings.mlr.press/v70/guo17a.html .

**Read:** PDF pp. 1–3, calibration definition, introduction and evaluation; abstract's post-processing findings.

**Evidence:** neural classification confidence can differ from empirical correctness; evaluates calibration methods including temperature scaling.

**Limit:** not evidence that a self-reported LLM confidence is calibrated, nor that our SVM margins are probabilities.

**Design consequence:** do not display SVM margins or an LLM self-rating as diagnostic confidence. The sentiment pilot returns a class only; the new conversation adapter additionally returns replies and evidence-linked proposals, without a diagnostic confidence. Hard scoring and confirmation rules remain independent.

## 8 Gratch et al 2014

**The Distress Analysis Interview Corpus of human and computer interviews.** LREC, 3123–3128. https://aclanthology.org/L14-1421/ .

**Read:** PDF pp. 1–3, overview, interview types and population. Describes human, teleconference, Wizard-of-Oz and automated interviews, recordings and questionnaire information.

**Limit:** this general corpus paper is not proof that we have permission or access to a specific release, nor evidence of completed PHQ-label experiments.

**Design consequence:** keep E1 sentiment/context/fusion prediction conditional on appropriate data access, participant grouping and documented labels. Do not substitute TweetEval polarity labels for depression labels.

## 9 Demszky et al 2020

**GoEmotions: A Dataset of Fine-Grained Emotions.** ACL, 4040–4054. https://aclanthology.org/2020.acl-main.372/ .

**Read:** PDF pp. 1–3: taxonomy, data collection and annotation; abstract and discussion. Contains about 58k English Reddit comments annotated for 27 emotions or neutral.

**Limit:** emotion taxonomy and domain differ from three-class polarity and PHQ symptom frequency. More emotion classes do not supply depression ground truth.

**Design consequence:** retain three classes for this semester, keep fine-grained emotion as an optional extension, and explain the distinction between emotion, sentiment and symptom-frequency labels.

## Cross-source synthesis

The evidence supports studying three separate layers: general sentiment classification, interpretation of questionnaire responses, and reliable confirmation/scoring. It does not support combining their metrics into a single “depression accuracy.” We contribute an integration and evaluation baseline, not a novel clinical instrument. The current limitations—language transfer, synthetic diagnostic cases, unvalidated wording and mock crisis handling—follow directly from the mismatch between our evidence and the evidence required for clinical claims.
