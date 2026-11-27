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

In healthcare chatbots, Laranjo et al. [4] found across 17 studies that structured state control remained standard because unconstrained generation risks unsafe behavior. Fitzpatrick et al. [5] showed feasibility for the Woebot CBT agent among 70 young adults while noting user frustration with rigid, repetitive replies and misunderstood free text. Geifman and El-Yaniv [6] framed selective classification as trading coverage against error risk among accepted predictions, while Guo et al. [7] showed that model confidence scores can be poorly calibrated. Recent LLM studies reinforce both the promise and boundaries of generative models in this setting: Yang et al. [13] evaluated LLMs across 11 mental-health and emotion datasets, finding that while ChatGPT generated readable explanations, zero-shot predictions still lagged behind domain-tuned encoders and remained sensitive to prompt phrasing. In the Hong Kong context, Fu et al. [14] (consulted via its structured PubMed/Europe PMC abstract) reported that GPT-3.5 and GPT-4 reached 92.1%–95.3% three-class sentiment accuracy across 6,169 Cantonese web-counseling messages versus 66.0%–70.9% for classical ML models, though still measuring message-level polarity rather than PHQ-8 symptom counts; meanwhile, Jiang et al. [15] documented how spoken–written divergence, unique Cantonese characters, and frequent Cantonese–English code-switching challenge standard Chinese NLP pipelines, motivating both our code-switched stress cases and local 7B model plans.

## 3. System Design and Implementation

Our main deliverable is a connected Streamlit web application supporting Traditional Chinese/Cantonese and English natural conversation, alongside our retained offline per-item rule questionnaire for baseline comparison. Figure 1 illustrates why the system splits incoming messages into two separate channels rather than feeding sentiment into the score.

Figure 1. Workflow of the Dual-Channel Preliminary Screening Chatbot, keeping emotional tone separate from quote-backed PHQ-8 symptom extraction and user-confirmed 0–24 scoring.

Before any external API request is sent, a lightweight pre-API filter checks for explicit demonstration interrupt markers; if triggered, it clears the session immediately without sending text over the network (serving as a workflow safety test rather than a clinical crisis detector). Because direct vendor API endpoints restrict regional student access from Hong Kong, normal messages are sent over HTTPS to a configured OpenAI-compatible Responses gateway [10, 11]. Our client requests model identifier gpt-6.1-terra with store=false, low reasoning effort, strict JSON-schema formatting, and a 3,200-token output cap (1,200 tokens for standalone sentiment), without setting an explicit temperature parameter so the server default applies. Because the gateway is operated by a third party, its underlying base-model weights, provider routing, and server-side sampling temperature cannot be audited independently and are recorded as an explicit system limitation.

Table 2 summarizes the strict JSON output schema returned on each turn and the local deterministic rules checked before any candidate enters session state. In the Affect Channel (Left Ear), the turn sentiment label guides a brief empathetic acknowledgment and updates sidebar tone counts without ever entering score calculation. In the Symptom Channel (Right Ear), vague phrases ('sometimes', '間唔中') or boundary-straddling ranges ('6–7 days') remain null so the chatbot asks a focused follow-up. Once all eight items hold valid proposals, the user reviews every verbatim quote, edits any 0–3 dropdown if needed, and ticks explicit confirmation to sum the 0–24 PHQ-8 total.

Table 2. Structured Turn Output Schema and Deterministic Local Validation Rules.

## 4. Experiment 1: Sentiment Baselines and Controlled Mismatch Stress Test

To answer RQ1, Experiment 1A trained four classical scikit-learn baselines on the pinned TweetEval sentiment splits (45,615 train, 2,000 validation, 12,284 held-out test) [3]: Majority, Multinomial Naive Bayes, Logistic Regression, and Linear SVM, using TF-IDF word unigrams and bigrams (up to 50,000 features) selected on validation Macro-F1.

Table 3. Experiment 1A Held-Out Results on Official TweetEval Sentiment Splits (Test N = 12,284).

Linear SVM improved test Macro-F1 by +0.344 over Majority (500-resample paired bootstrap 95% CI [0.334, 0.353]) and performed almost identically to Logistic Regression on test Macro-F1 (0.5607 vs. 0.5611; 95% CI [-0.005, +0.004]), though negative-class recall reached only 0.450.

Because Semester 1 does not involve human-subject data, Experiment 1B designed a 48-sentence controlled bilingual stress test (24 English + 24 Traditional Chinese/Cantonese; 12 sentences in each of Congruent Low, Situational Distress, Masked Somatic, and Congruent Elevated), where both group members checked each sentence's reference tone label and underlying PHQ-8 profile total. Table 4 and Figure 2 compare sentiment accuracy against the naive screening rule 'Negative Sentiment => PHQ-8 >= 10'.

Table 4. Experiment 1B Controlled Bilingual Stress Test (N = 48; All Columns Report Accuracy — Higher is Better).

Figure 2. (a) Public TweetEval test scores. (b) Controlled bilingual stress test showing that even 94%–100% sentiment accuracy drops to 0%–8% screening accuracy on Situational Distress and Masked Somatic cases.

As shown in Table 4 and Figure 2(b), English-trained TF-IDF models defaulted to neutral on Chinese script (37.5% accuracy), whereas the connected LLM reached 95.8% in English and 91.7% in Chinese (three mild boundary disagreements where calm routine sentences or a mixed Cantonese complaint ending with '放假去打波都好投入' were labeled positive). Notice that the English TF-IDF models appear to score 66.7%–83.3% on Situational Distress proxy accuracy only through a double error—failing to read Chinese complaints and defaulting to neutral—whereas once sentiment is recognized accurately (93.8%–100.0%), Situational Distress proxy accuracy collapses to 8.3% and 0.0%, and Masked Somatic proxy accuracy sits at 0.0% (50.0% overall). This confirms why a separate symptom-extraction channel is essential.

## 5. Experiment 2: Bilingual Symptom Extraction, Abstention, and Error Analysis

To answer RQ2, we constructed an 80-utterance bilingual test set balanced across the eight PHQ-8 domains (40 English + 40 Cantonese/Traditional Chinese; 40 resolvable answers + 40 must-abstain inputs) and verified zero SHA-256 text overlap against a separate 320-sentence bilingual training set (80 per category 0–3) used to fit a word+character TF-IDF + 5-fold calibrated Logistic Regression baseline. Alongside 64 standard cases (canonical choices, exact day counts, colloquial answers, timeframe contrasts, vague words like 'sometimes'/'間唔中', past-year episodes, boundary-crossing '6–7 days', and pure venting), we included 16 harder Hong Kong student stress cases with Cantonese–English code-switching ('呢 two weeks 逢禮拜一至五返 intern 都 tired 到死'), sarcasm, weekly rates ('三至四晚一個禮拜' = 6–8 nights straddling 6|7), and past-fortnight traps ('上次 mid-term 嗰 two weeks').

Table 5. Experiment 2 Symptom Extraction and Selective Abstention Across 80 Bilingual Test Utterances.

Figure 3. (a) Risk–Coverage curve on 80 bilingual turns. (b) Accuracy comparison between the 64 standard cases and 16 Hong Kong code-switched & trap stress cases.

Table 5 and Figure 3 illustrate why simple classifiers struggle with conversational screening. Forced TF-IDF + Logistic Regression guessed an integer on every turn (0.0% abstention), falling to 12.5% accuracy on the 16 HK stress cases; even with a 0.60 confidence threshold (56.2% overall), bag-of-words features could not distinguish '12 days during past quarantine' from '12 days in the past two weeks'. Conversely, our offline Rule Baseline (designed for bare option strings where it previously accepted 24/64 template inputs) accepted 0/80 multi-clause chat sentences, leaving selective risk undefined (N/A). Our connected chatbot achieved 98.8% (79/80) on this structured rule-compliance set (93.8% on the 16 stress cases) with 0.0% false acceptances and 100% verbatim quote matches—though accuracy on unscripted real-user conversations would naturally be lower. Table 6 examines four representative failure mechanisms.

Table 6. Error Analysis of Representative Failure Cases on Hong Kong Code-Switched and Colloquial Inputs.

## 6. Experiment 3: Multi-Turn Chatbot Walkthroughs and Safety Verification

To address RQ3, we ran four live multi-turn bilingual screening scenarios end-to-end through the chatbot (Table 7 and Figure 4) and verified our local scoring and safety rules across 234 automated tests (Table 8).

Table 7. Summary of Four Live Multi-Turn Bilingual Screening Walkthroughs.

Figure 4. Actual Streamlit interface screenshots from Scenario 2: (left) multi-turn chat, non-scoring sidebar affect counter, and quote-backed batch review panel; (right) confirmed 11/24 score with Masked Somatic comparison banner.

Across all four walkthroughs, the chatbot preserved exact original-language quotes, ignored out-of-window winter insomnia in Scenario 3 while respecting manual user score edits at review (changing item 4 fatigue from 1 to 2, updating the provisional total from 2/24 to the confirmed 3/24), and confirmed deterministic PHQ-8 totals. In Table 8, our Score Invariance check confirms at the software level that the local scoring function ignores stored sentiment labels completely (800/800 identical totals when flipping stored turn sentiments); note, however, that during live chat a single LLM call generates both the reply tone and candidate item updates, so their statistical independence in model generation is not claimed.

Table 8. Automated Verification of Scoring Boundaries, Quote Provenance, and Pre-API Interrupts.

## 7. Limitations and Practical Challenges

1. Fictional Stress Cases vs. Real Users: Apart from public TweetEval tweets, our 48-case and 80-case bilingual sets were written and checked by our team under explicit PHQ-8 rules to avoid collecting sensitive human data without ethics approval. Real users produce typos, fragmented replies, and unexpected topic shifts that will lower extraction accuracy below 98.8%.

2. API Turn Latency & Third-Party Gateway: Live structured-output calls took roughly 8 to 16 seconds per turn through the configured compatible endpoint, which feels slow during interactive chat and motivates testing smaller local models in Semester 2.

3. Quote Matching vs. Full Meaning & Mock Safety Filter: Checking that a quote appears verbatim in the user's message prevents hallucinated citations, but cannot guarantee that the model interpreted indirect idioms accurately—making user batch review essential. Likewise, our pre-API safety filter checks synthetic demo markers only and is not a real crisis detector.

## 8. Semester 2 Plan, Work Division, and Conclusion

Table 9. Semester 2 Research Timeline (January – April 2027).

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

[13] K. Yang, S. Ji, T. Zhang, Q. Xie, Z. Kuang, and S. Ananiadou, "Towards Interpretable Mental Health Analysis with Large Language Models," Proceedings of EMNLP, pp. 6056–6077, 2023. doi: 10.18653/v1/2023.emnlp-main.370. https://aclanthology.org/2023.emnlp-main.370/.

[14] Z. Fu, Y. C. Hsu, C. S. Chan, C. M. Lau, J. Liu, and P. S. F. Yip, "Efficacy of ChatGPT in Cantonese Sentiment Analysis: Comparative Study," Journal of Medical Internet Research, vol. 26, e51069, 2024. doi: 10.2196/51069. (Indexed structured abstract consulted via Europe PMC; PMID 38289662).

[15] J. Jiang, A. K. Y. Truong, Y. Chen, Q. Bao, S. Wang, P. Chen, J. Wang, L. Kong, Y. Li, and C. Wu, "Developing and Utilizing a Large-Scale Cantonese Dataset for Multi-Tasking in Large Language Models," Findings of EMNLP, pp. 1924–1944, 2025. doi: 10.18653/v1/2025.findings-emnlp.102. https://aclanthology.org/2025.findings-emnlp.102/.
