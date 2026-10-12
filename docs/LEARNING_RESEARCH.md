# Learning research and bounded product decisions

Checked 12 October 2026. This is an implementation memo, not proof of the platform's effectiveness. The papers below concern human learners, particular tasks and languages. None validates the present generated Belgian Dutch curriculum or automated assessor.

## Three additions worth building

### 1. Return to the skill in a different situation

After a learner corrects a sentence or completes a mission, offer a short later task that uses the same communicative function with different facts. Changing a dentist appointment can become changing a bicycle repair booking. Keep the learning target, change the date, participant and constraint. A correction made with help remains useful practice; it does not establish independent retention.

Store the original attempt, help exposure and revision separately. A later independent success requires the first attempt in a different session, after a configurable minimum delay, with no hint, model answer or override. A suggested next-day delay is a product policy to trial, not a research-derived CEFR pass rule. Present the learner with “You used this yesterday; try it in a new situation” rather than an unexplained weakness score.

The underlying retrieval and spacing principles are established. The exact schedule and transfer between Dutch situations are product hypotheses. Keep the feature small: one review card and one changed-context variant per existing mission. Do not generate an entire new syllabus at runtime.

Acceptance: assisted correction never clears an independent-review need; a same-session retry never counts as delayed evidence; the changed facts resolve deterministically; existing attempt history is retained. Evaluate useful independence on unseen tasks at one and seven days, not clicks, immediate fluency or points.

### 2. Practise repairing a misunderstanding

Introduce one controlled misunderstanding in an existing information-gap mission. The conversation partner may repeat the wrong time or offer an unavailable slot. The learner needs to notice, ask for clarification, correct the detail and confirm the arrangement. Difficulty varies by the language required: a beginner may select “Kunt u dat herhalen?”; a B1 learner can explain the conflict; advanced learners can tactfully handle competing interpretations.

The fictional misunderstanding is declared in the lesson contract and limited to approved branches. The system must never fabricate a real appointment or mislead the learner about an actual service. The task outcome checks the final workable arrangement in code. The feedback identifies both successful repair and any unresolved detail. Do not judge communication through grammatical correctness alone.

Human task-based interaction research supports active participation and opportunities for negotiation; it does not prove that model-generated dialogue has the same educational effect. This is a differentiated product combination, not a claim that nobody has implemented repair practice.

Acceptance: the partner cannot make an invalid booking valid; the learner can succeed through a suitable clarification phrase without guessing hidden facts; the scenario offers a reviewed fallback after bounded turns; errors in factual arrangements are distinguished from language issues. Compare task success and clarification use on an unseen conversation against an ordinary role-play baseline.

### 3. Listen, commit to a provisional interpretation, then revise

Use a listen-first flow: show the situation and one goal, play the audio, ask for a provisional answer, optionally record confidence (“sure / partly sure / unsure”), then offer a second listen and revision. Transcript and translation stay available on demand and their use is recorded as help. Ask a short reflection such as “Which words changed your answer?”; do not turn every exercise into a metacognition questionnaire.

A learner who discovers a mistake after replay has made useful progress. Preserve the initial interpretation separately from the assisted final answer. Confidence is diagnostic, never a grade or a mastery substitute. Low-confidence correct answers can suggest later retrieval; high-confidence incorrect answers can suggest clarification practice. Avoid punitive streaks.

Process-based listening has empirical support, including self-directed online work. Evidence for improved self-efficacy is mixed. Therefore claim a supported teaching approach, not guaranteed confidence improvement. The three-button confidence affordance itself needs usability and learning validation.

Acceptance: text is not shown automatically before listening; translation is reachable and does not lock the learner out; audio replay, transcript and hints cannot retroactively rewrite first-attempt evidence; controls work with keyboard, screen reader and on the owner's actual phone. Evaluate new-clip comprehension later, plus optional-confidence completion rate and perceived effort.

## Feedback design decision

Use the existing grounded correction tool. Show a compact corrected form and one targeted explanation, with further explanation on request. Let the learner revise, preserving the draft. Prompting can be useful for oral self-repair, but a prompt is not always superior to an explicit answer: task, proficiency and target matter. Avoid lengthy generated reports by default. A correct revision of the same draft is not sufficient evidence of long-term acquisition; later original writing matters.

## Primary evidence and limits

| Source | Finding relevant here | Limit for this platform |
| --- | --- | --- |
| Karpicke & Roediger (2008), *The Critical Importance of Retrieval for Learning*, DOI [10.1126/science.1152408](https://doi.org/10.1126/science.1152408); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/18276894/) | Retrieval practice after successful learning benefited delayed foreign-language vocabulary recall. | Paired vocabulary recall is not a four-skill communicative proficiency test. |
| Belardi et al. (2021), [*Spacing, Feedback, and Testing Boost Vocabulary Learning in a Web Application*](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2021.757262/full), DOI 10.3389/fpsyg.2021.757262; [2025 correction](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1629682/full) | 79 German-speaking participants learned Finnish word pairs; spacing and feedback/testing influenced recall two days later. | Small paired-associate study; reported percentage-point improvements must not become marketing predictions for Dutch learners. The correction fixes percent versus percentage-point wording. |
| Butler et al. (2017), [*Retrieving and applying knowledge to different examples promotes transfer of learning*](https://scholars.duke.edu/publication/1292911), DOI 10.1037/xap0000142 | Four experiments found better new-example transfer following varied examples during retrieval practice. | Geological concepts and two-day testing, not Dutch conversations. This supports trying varied practice; it does not prove the selected mission variants work. |
| Mackey (1999), [*Input, Interaction, and Second Language Development*](https://www.cambridge.org/core/journals/studies-in-second-language-acquisition/article/abs/input-interaction-and-second-language-development/D09BD3D63DC401DC57FC3ABB4B332588), DOI 10.1017/S0272263199004027 | A task-based study with 34 adult ESL learners linked active interaction to grammatical development. | Small human-interaction study; learner developmental readiness matters; not validation of unrestricted chatbot dialogue. |
| Lyster & Saito (2010), [*Oral Feedback in Classroom SLA: A Meta-Analysis*](https://www.cambridge.org/core/journals/studies-in-second-language-acquisition/article/abs/oral-feedback-in-classroom-sla/4999EE1C8379B2BF026B148EAF373CA1), DOI 10.1017/S0272263109990520 | Fifteen classroom studies, 827 learners: oral corrective feedback had durable effects; prompts showed larger effects than recasts in this synthesis. | Teacher feedback and selected targets; automated feedback accuracy still requires separate review. Does not imply every error should trigger an interruption. |
| Bitchener & Knoch (2010), [*The Contribution of Written Corrective Feedback to Language Development: A Ten Month Investigation*](https://academic.oup.com/applij/article-abstract/31/2/193/177926), DOI 10.1093/applin/amp016 | Examined feedback on two English article functions in 52 low-intermediate ESL learners, using subsequent writing and delayed tests. | Narrow targets; a repaired draft must not be treated as proof of general grammar mastery. |
| Vandergrift & Tafaghodtari (2010), [*Teaching L2 Learners How to Listen Does Make a Difference*](https://onlinelibrary.wiley.com/doi/10.1111/j.1467-9922.2009.00559.x), DOI 10.1111/j.1467-9922.2009.00559.x | 106 French learners: guided prediction, monitoring and evaluation outperformed the comparison group on final comprehension. | Semester instruction with intact classes, not a single interaction widget or Belgian Dutch benchmark. |
| Pei, Suwanthep & Lu (2023), [*The effect of self-directed online metacognitive listening practice...*](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2023.1285059/full), DOI 10.3389/fpsyg.2023.1285059 | 89 intermediate Chinese EFL learners over 14 weeks: listening comprehension improved; little evidence of increased self-efficacy. | Quasi-experiment and specific learner group. Confidence collection should be optional; increased confidence is not an assured outcome. |
| Lu et al. (2025), [*From belief to evidence: simpler immediate feedback improves language learning and confidence in semi-open-ended questions*](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2025.1654809/full), DOI 10.3389/feduc.2025.1654809 | In its semi-open-ended language-task experiment, concise correct-response feedback performed better than more elaborate variants. | One specific setting and short delayed tests, no longer than one week. Use as a reason to test concise feedback, not a universal replacement for explanations. |

## Defer

Do not add autonomous curriculum certification, generated songs, expensive avatars, hidden accent scores or another agent framework as a result of this review. First validate the reviewed language, task consistency and independent transfer. Regional and informal speech can be receptive material with appropriate labels; Standard Belgian Dutch remains the production target.

Research-backed does not mean research-validated. A feature flag, original reviewed materials, recorded assistance and comparison with a simpler baseline are the appropriate next steps.
