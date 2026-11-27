# Sentiment Analysis for Depression Detection
## A Dual-Channel Bilingual Chatbot for PHQ-8 Preliminary Screening
**CUHK SEEM Final Year Project — Semester 1 Final Report (Group T)**  
**Members:** CHAN, Kin Long (1155212039) · LEE, Ka Tung (1155212062)  
**Supervisor:** Prof. Helen Meng · **Date:** 27 November 2026

---

THE CHINESE UNIVERSITY OF HONG KONG
Department of Systems Engineering and Engineering Management

Sentiment Analysis for Depression Detection

A Dual-Channel Bilingual Chatbot for PHQ-8 Preliminary Screening
Semester 1 Final Report  ·  Group T  ·  27 November 2026

Project Identification

## Abstract

A common pitfall in text-based mental-health projects is treating negative sentiment as a direct proxy for depression. In preliminary screening conversations, however, emotional tone and two-week symptom frequency often diverge: a person angrily complaining about a bus delay expresses negative sentiment without ongoing depressive symptoms (situational distress), whereas someone calmly reporting twelve sleepless nights and daily fatigue in neutral prose has high symptom burden (masked somatic reporting). To resolve this mismatch, we built a bilingual (Traditional Chinese/Cantonese and English) Dual-Channel Preliminary Screening Chatbot based on the eight-item PHQ-8 questionnaire. One channel tracks turn-level sentiment only to guide supportive conversational replies and post-session tone notes, while a separate symptom channel extracts past-14-day frequencies backed by verbatim user quotes, asks follow-up questions on unclear inputs, and requires explicit user review before summing the 0–24 score. Across three linked experiments, public TweetEval baselines (Macro-F1 0.561 with Linear SVM) and a 48-case bilingual stress test confirmed that even 100% accurate sentiment achieves only 50.0% accuracy as a naive proxy for elevated PHQ-8 burden. On an 80-utterance bilingual extraction test including Hong Kong code-switched stress cases, our chatbot reached 98.8% rule-compliance accuracy with zero false acceptances, and four multi-turn walkthroughs verified end-to-end user review and score invariance to sentiment. All custom screening cases and chatbot walkthroughs use fictional inputs; no clinical validity is claimed.

## 1. Introduction and Research Questions

Under our project title, Sentiment Analysis for Depression Detection, our objective is to build a practical preliminary screening chatbot while clarifying what role sentiment analysis should—and should not—play. Standard PHQ-8 screening asks how often eight specific problems (such as reduced interest, depressed mood, poor sleep, low energy, or appetite change) occurred over the past 14 days on a 0–3 scale ('not at all' to 'nearly every day'), giving a total score from 0 to 24 [1, 2]. Emotional tone in a single message and symptom frequency over two weeks therefore measure different things.

In everyday English or Hong Kong Cantonese dialogue, relying on sentiment alone breaks down in two common situations: (1) Situational Distress, where a user vents frustration about an immediate hassle (such as pouring rain or a group-project dispute) while their two-week sleep, energy, and mood are normal (causing false positives); and (2) Masked / Matter-of-Fact Somatic Reporting, where a user calmly states high two-week counts of insomnia, fatigue, and poor concentration without emotional words (causing false negatives). Our Dual-Channel ('Two-Ear') Chatbot separates these two signals so emotional tone improves conversational warmth without ever distorting PHQ-8 scores.

To keep our Semester 1 investigation focused and coherent, we organize our system evaluation around three connected Research Questions (Table 1):

Table 1. Semester 1 Research Questions Mapped to Experiments and Core Findings.

## 2. Literature Review

Kroenke et al. [1] evaluated PHQ-8 in a survey of 198,678 adults, reporting similar population prevalence under symptom-algorithm and score >= 10 definitions. We consulted the indexed PubMed abstract of [1] rather than the full article; as that abstract notes, PHQ-8 was not validated against a structured psychiatric interview in that survey, so totals represent self-reported symptom summaries rather than clinical diagnoses. Dhingra et al. [2] studied day-count PHQ-8 responses and documented the R1 conversion from 14-day counts into the four 0–3 categories: 0–1 days -> 0, 2–6 days -> 1, 7–11 days -> 2, and 12–14 days -> 3 (separate from their 0–112 day sum). Because 1 reported day maps to category 0 despite symptom presence, showing the user's original words during review is important, and ranges crossing a threshold (such as '6–7 days') require follow-up rather than rounding.

For sentiment classification, TweetEval [3] standardizes SemEval-2017 Twitter splits [12] across negative, neutral, and positive labels using macro-averaged recall. GoEmotions [9] annotates 58,000 Reddit comments with 27 emotion categories, showing finer emotional granularity, yet neither dataset contains past-two-week symptom frequencies. Clinical interview corpora such as DAIC-WOZ [8] include PHQ-8 scores alongside interview transcripts, but require institutional licensing beyond Semester 1.

In healthcare chatbots, Laranjo et al. [4] found across 17 studies that structured state control remained standard because unconstrained generation risks unsafe behavior. Fitzpatrick et al. [5] showed feasibility for the Woebot CBT agent among 70 young adults while noting user frustration with rigid, repetitive replies and misunderstood free text. Geifman and El-Yaniv [6] framed selective classification as trading coverage against error risk among accepted predictions, while Guo et al. [7] showed that model confidence scores can be poorly calibrated. These findings directly motivate allowing natural multi-symptom input while abstaining on unclear wording and requiring user confirmation before scoring.

## 3. System Design and Implementation

Our main deliverable is a connected Streamlit web application supporting Traditional Chinese/Cantonese and English natural conversation, alongside our retained offline per-item rule questionnaire for baseline comparison. Figure 1 illustrates why the system splits incoming messages into two separate channels rather than feeding sentiment into the score.

Figure 1. Workflow of the Dual-Channel Preliminary Screening Chatbot, keeping emotional tone separate from quote-backed PHQ-8 symptom extraction and user-confirmed 0–24 scoring.

Before any external API request is sent, a lightweight pre-API filter checks for explicit demonstration interrupt markers; if triggered, it clears the session immediately without sending text over the network (serving as a workflow safety test rather than a clinical crisis detector). For normal messages, the chatbot communicates with a configured OpenAI-compatible Responses endpoint [10, 11] (which reports the model identifier gpt-6.1-terra via our third-party gateway) using a strict JSON output schema.

In the Affect Channel (Left Ear), the assistant labels each user turn as negative, neutral, positive, or unclear so it can offer a brief empathetic sentence before asking at most one follow-up question, while displaying turn-tone counts in the sidebar strictly as non-scoring context. In the Symptom Channel (Right Ear), each proposed PHQ-8 item update must attach a past-14-day timeframe label and a word-for-word substring quote from the user's message; local validation rejects any fabricated quote or out-of-window score. Vague phrases ('sometimes', '間唔中') or boundary-straddling ranges ('6–7 days') remain unresolved (null) so the chatbot asks a clarifying question. Once all eight items have valid proposals, the user inspects every quote and can edit any 0–3 dropdown in a batch review panel before ticking explicit confirmation. Only those eight confirmed integers are summed into the 0–24 PHQ-8 total, after which a post-session note highlights whether tone and symptom burden were aligned or divergent.

## 4. Experiment 1: Sentiment Baselines and Controlled Mismatch Stress Test

To answer RQ1, Experiment 1A trained four classical scikit-learn baselines on the pinned TweetEval sentiment splits (45,615 train, 2,000 validation, 12,284 held-out test) [3]: Majority, Multinomial Naive Bayes, Logistic Regression, and Linear SVM, using TF-IDF word unigrams and bigrams (up to 50,000 features) selected on validation Macro-F1.

Table 2. Experiment 1A Held-Out Results on Official TweetEval Sentiment Splits (Test N = 12,284).

Linear SVM and Logistic Regression improved test Macro-F1 by +0.344 over Majority (500-resample paired bootstrap 95% CI [0.334, 0.353]) with virtually identical accuracy to each other (difference -0.000), though negative-class recall reached only 0.450.

Because Semester 1 does not involve human-subject data, Experiment 1B designed a 48-sentence controlled bilingual stress test (24 English + 24 Traditional Chinese/Cantonese; 12 sentences in each of Congruent Low, Situational Distress, Masked Somatic, and Congruent Elevated), where both group members checked each sentence's reference tone label and underlying PHQ-8 profile total. Table 3 and Figure 2 compare sentiment accuracy against the naive screening rule 'Negative Sentiment => PHQ-8 >= 10'.

Table 3. Experiment 1B Controlled Bilingual Stress Test (N = 48; All Columns Report Accuracy — Higher is Better).

Figure 2. (a) Public TweetEval test scores. (b) Controlled bilingual stress test showing that even 94%–100% sentiment accuracy drops to 0%–8% screening accuracy on Situational Distress and Masked Somatic cases.

As shown in Table 3 and Figure 2(b), English-trained TF-IDF models defaulted to neutral on Chinese script (37.5% accuracy), whereas the connected LLM reached 95.8% in English and 91.7% in Chinese (three mild boundary disagreements where calm routine sentences or a mixed Cantonese complaint ending with '放假去打波都好投入' were labeled positive). More importantly, even 100% perfect sentiment achieved 0.0% screening accuracy on Situational Distress and 0.0% on Masked Somatic cases (50.0% overall), demonstrating why a dedicated symptom-extraction channel is essential.

## 5. Experiment 2: Bilingual Symptom Extraction, Abstention, and Error Analysis

To answer RQ2, we constructed an 80-utterance bilingual test set balanced across the eight PHQ-8 domains (40 English + 40 Cantonese/Traditional Chinese; 40 resolvable answers + 40 must-abstain inputs) and verified zero SHA-256 text overlap against a separate 320-sentence bilingual training set (80 per category 0–3) used to fit a word+character TF-IDF + 5-fold calibrated Logistic Regression baseline. Alongside 64 standard cases (canonical choices, exact day counts, colloquial answers, timeframe contrasts, vague words like 'sometimes'/'間唔中', past-year episodes, boundary-crossing '6–7 days', and pure venting), we included 16 harder Hong Kong student stress cases with Cantonese–English code-switching ('呢 two weeks 逢禮拜一至五返 intern 都 tired 到死'), sarcasm, weekly rates ('三至四晚一個禮拜' = 6–8 nights straddling 6|7), and past-fortnight traps ('上次 mid-term 嗰 two weeks').

Table 4. Experiment 2 Symptom Extraction and Selective Abstention Across 80 Bilingual Test Utterances.

Figure 3. (a) Risk–Coverage curve on 80 bilingual turns. (b) Accuracy comparison between the 64 standard cases and 16 Hong Kong code-switched & trap stress cases.

Table 4 and Figure 3 illustrate why simple classifiers struggle with conversational screening. Forced TF-IDF + Logistic Regression guessed an integer on every turn (0.0% abstention), falling to 12.5% accuracy on the 16 HK stress cases; even with a 0.60 confidence threshold (56.2% overall), bag-of-words features could not distinguish '12 days during past quarantine' from '12 days in the past two weeks'. Conversely, our offline Rule Baseline (designed for bare option strings where it previously accepted 24/64 template inputs) accepted 0/80 multi-clause chat sentences, leaving selective risk undefined (N/A). Our connected chatbot achieved 98.8% (79/80) on this structured rule-compliance set (93.8% on the 16 stress cases) with 0.0% false acceptances and 100% verbatim quote matches—though accuracy on unscripted real-user conversations would naturally be lower. Table 5 examines four representative failure mechanisms.

Table 5. Error Analysis of Representative Failure Cases on Hong Kong Code-Switched and Colloquial Inputs.

## 6. Experiment 3: Multi-Turn Chatbot Walkthroughs and Safety Verification

To address RQ3, we ran four live multi-turn bilingual screening scenarios end-to-end through the chatbot (Table 6 and Figure 4) and verified our local scoring and safety rules across 234 automated tests (Table 7).

Table 6. Summary of Four Live Multi-Turn Bilingual Screening Walkthroughs.

Figure 4. Four-stage walkthrough of Scenario 2 illustrating multi-symptom input, follow-up clarification on 'occasionally', quote-backed batch review, and confirmed 11/24 score with Masked Somatic note.

Across all four walkthroughs, the chatbot preserved exact original-language quotes, ignored out-of-window winter insomnia in Scenario 3 while respecting manual user score edits at review, and confirmed deterministic PHQ-8 totals. In Table 7, our Score Invariance check confirms at the software level that the local scoring function ignores stored sentiment labels completely (800/800 identical totals when flipping stored turn sentiments); note, however, that during live chat a single LLM call generates both the reply tone and candidate item updates, so their statistical independence in model generation is not claimed.

Table 7. Automated Verification of Scoring Boundaries, Quote Provenance, and Pre-API Interrupts.

## 7. Limitations and Practical Challenges

1. Fictional Stress Cases vs. Real Users: Apart from public TweetEval tweets, our 48-case and 80-case bilingual sets were written and checked by our team under explicit PHQ-8 rules to avoid collecting sensitive human data without ethics approval. Real users produce typos, fragmented replies, and unexpected topic shifts that will lower extraction accuracy below 98.8%.

2. API Turn Latency & Third-Party Gateway: Live structured-output calls took roughly 8 to 16 seconds per turn through the configured compatible endpoint, which feels slow during interactive chat and motivates testing smaller local models in Semester 2.

3. Quote Matching vs. Full Meaning & Mock Safety Filter: Checking that a quote appears verbatim in the user's message prevents hallucinated citations, but cannot guarantee that the model interpreted indirect idioms accurately—making user batch review essential. Likewise, our pre-API safety filter checks synthetic demo markers only and is not a real crisis detector.

## 8. Semester 2 Plan, Work Division, and Conclusion

Table 8. Semester 2 Research Timeline (January – April 2027).

Work Division: LEE Ka Tung (1155212062) led literature review, TweetEval dataset preparation, classical ML baselines, and bilingual evaluation analysis; CHAN Kin Long (1155212039) led PHQ-8 scoring/safety boundary rules, multi-turn dialogue state management, and bilingual Streamlit UI integration, with both members jointly reviewing experiments and co-writing this report under Prof. Helen Meng's supervision.

Conclusion: In conclusion, Semester 1 produced a working bilingual Dual-Channel Preliminary Screening Chatbot backed by three coherent experiments demonstrating why sentiment polarity cannot replace two-week symptom grounding, how quote-verified extraction with selective abstention handles standard and Hong Kong code-switched inputs, and how mandatory user review keeps PHQ-8 scoring transparent and reliable.

## References

[1] K. Kroenke, T. W. Strine, R. L. Spitzer, J. B. W. Williams, J. T. Berry, and A. H. Mokdad, "The PHQ-8 as a measure of current depression in the general population," Journal of Affective Disorders, vol. 114, pp. 163–173, 2009. doi: 10.1016/j.jad.2008.06.026. (Indexed PubMed abstract consulted: https://pubmed.ncbi.nlm.nih.gov/18752852/).

[2] S. S. Dhingra, K. Kroenke, M. M. Zack, T. W. Strine, and L. S. Balluz, "PHQ-8 Days: a measurement option for DSM-5 Major Depressive Disorder (MDD) severity," Population Health Metrics, vol. 9, art. 11, 2011. doi: 10.1186/1478-7954-9-11.

[3] F. Barbieri, J. Camacho-Collados, L. Neves, and L. Espinosa-Anke, "TweetEval: Unified Benchmark and Comparative Evaluation for Tweet Classification," Findings of EMNLP, pp. 1644–1650, 2020. doi: 10.18653/v1/2020.findings-emnlp.148.

[4] L. Laranjo et al., "Conversational agents in healthcare: a systematic review," Journal of the American Medical Informatics Association, vol. 25, no. 9, pp. 1248–1258, 2018. doi: 10.1093/jamia/ocy072.

[5] K. K. Fitzpatrick, A. Darcy, and M. Vierhile, "Delivering Cognitive Behavior Therapy to Young Adults With Symptoms of Depression and Anxiety Using a Fully Automated Conversational Agent (Woebot): A Randomized Controlled Trial," JMIR Mental Health, vol. 4, no. 2, e19, 2017. doi: 10.2196/mental.7785.

[6] Y. Geifman and R. El-Yaniv, "Selective Classification for Deep Neural Networks," Advances in Neural Information Processing Systems (NeurIPS), vol. 30, 2017.

[7] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On Calibration of Modern Neural Networks," Proceedings of ICML, PMLR, vol. 70, pp. 1321–1330, 2017.

[8] J. Gratch et al., "The Distress Analysis Interview Corpus of human and computer interviews," Proceedings of LREC, pp. 3123–3128, 2014.

[9] D. Demszky et al., "GoEmotions: A Dataset of Fine-Grained Emotions," Proceedings of ACL, pp. 4040–4054, 2020. doi: 10.18653/v1/2020.acl-main.372.

[10] OpenAI, "Responses API Reference," OpenAI Platform Documentation, accessed Nov. 2026. https://platform.openai.com/docs/api-reference/responses. (Used for compatible HTTP request/response format; connected third-party gateway reported model identifier gpt-6.1-terra).

[11] OpenAI, "Structured Model Outputs," OpenAI Platform Guide, accessed Nov. 2026. https://platform.openai.com/docs/guides/structured-outputs.

[12] S. Rosenthal, N. Farra, and P. Nakov, "SemEval-2017 Task 4: Sentiment Analysis in Twitter," Proceedings of SemEval, pp. 502–518, 2017. doi: 10.18653/v1/S17-2088.
