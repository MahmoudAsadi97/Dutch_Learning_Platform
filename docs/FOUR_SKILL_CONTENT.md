# Four-skill lesson expansion

## Available practice

The original appointment lesson remains available. Three original A2-targeted practice packs add different communication goals. A2 is a provisional teaching target, not a certified assessment level.

| Mission | Reading | Listening | Speaking | Writing | Independent transfer |
|---|---|---|---|---|---|
| Lunch bestellen | Menu, prices, ordering location | Sold-out item and takeaway option | Explain a need, select an available lunch, confirm | Tell a friend the order, price and location | Order a drink in another café |
| Een aankoop terugbrengen | Fictional shop conditions and closing time | Size problem and available replacement | Explain a problem, choose replacement or voucher, confirm | Request a solution from the shop | Return a different garment |
| Een bericht voor de les | Changed classroom and instructions | Ways to obtain exercises and office closing time | Ask for missed work, choose delivery format, confirm | Turn a blunt message into a polite email | Request a library reading list |

Each pack has two reading questions, two listening questions, vocabulary, Persian instructions and text hints, a spoken or typed practice conversation, a short writing task and a speech-only independent transfer. Typed dialogue is never counted as spoken performance. Choosing an option successfully is task completion, not proof of pronunciation quality or general language mastery.

## Source use and review

The supplied collection contains seven scanned PDFs, 683 pages, without extractable text or accompanying audio. This implementation used targeted visual inspection, supported by imperfect English-language OCR for navigation. It does not claim a complete verified transcription or comprehensive curriculum extraction.

Source-page references below identify task patterns only. No scan, illustration, original recording, OCR dump, or copied exercise is included in the repository or application.

| Supplied file / PDF page | Pattern used |
|---|---|
| Dutch pdf3.pdf / 39 | Listen for prices; connect spoken amounts to written information |
| Dutch pdf 5.pdf / 119 | Read a menu and understand an order |
| Dutch pdf6.pdf / 11 | Explain an ordering problem; practise independently or with help |
| Dutch pdf 5.pdf / 46 | Explain a purchase problem and request a remedy |
| Dutch pdf6.pdf / 72 | Adapt a message to its recipient; request information by email |

All new scenarios, prices, businesses and messages are fictional, newly written practice content. Store-return conditions are scenario facts, not consumer-rights advice. Both Dutch and Persian content still need competent human language review. Every localized text remains `unreviewed`; the learner sees the concise review label. Audio uses the configured synthetic voice and keeps its synthetic-audio label. Source recordings were not supplied.

Review priorities: natural Belgian Standard Dutch, suitability for beginner learners, Persian accuracy, factual agreement across modalities, and whether distractors have exactly one defensible answer. Recheck availability, prices, pronoun/register consistency and synthetic pronunciation. Do not mark a pack reviewed solely because automated tests pass.

## Language targets for reviewer confirmation

- Lunch: polite requests with *ik wil graag / mag ik*, prices, *op zijn*, *hier eten / meenemen*.
- Shopping: describe size with *te klein / te groot*, ask *kan ik ruilen?*, recognise *kasticket* and *tegoedbon*.
- Course: recognise changes of place/time, ask *kunt u …?*, explain absence, add a suitable greeting and closing to an email.
- Across packs: ask for repetition, select explicitly and confirm understanding. Reference material is an aid, not a rule that every acceptable answer must match one fixed sentence.

## Implementation and boundaries

The mission catalog is available at `/missions` and on the dashboard. Progress can be selected per mission; records remain separate by skill. Existing sessions and the original appointment mission retain their identifiers.

Service scenarios add typed, authoritative choices to the existing conversation workflow. The model interprets an utterance; code rejects an unavailable choice or premature confirmation. A changed choice requires fresh confirmation. Cancellation cannot complete the task. Character replies for these service tasks use authored phase lines and the validated choice, avoiding invented prices or remedies. This is a constrained conversation, not unrestricted role-play. It makes one interpretation call per turn; the existing allowance mechanism retains conservative reservation and actual-use accounting.

Learning screens retain explanations, quotations, corrections, assistance labels, meaningful progress and audio labels. They no longer display model/provider identifiers, prompt versions, evidence UUIDs, model latency, session UUIDs, or discarded unsupported feedback. Diagnostic records remain in the backend/export. Connection diagnostics are collapsed under Technical support in settings.

## Verification and rollout

Tests cover schema and word limits, transfer restrictions, state serialization, unsupported choices, confirmation sequencing, cancellation, one-call service turns, catalog loading, progress separation and browser workflows. Fixture speech/model tests verify plumbing, not live Azure speech quality or linguistic validity.

Deployment requires **both** updated API and web images. Run the release migration job using the new API image before updating application revisions: it loads all mission packs into PostgreSQL. No new Azure service is needed. Retain the deployed runtime's `DLP_API_DIR` and `PUBLIC_ORIGIN` settings and keep the API private. Update digest pins in the private local parameter file. Do not use an older foundation parameter file that would disable public web ingress or overwrite current image pins.

After deployment, open `/missions`, confirm four cards, complete a new lesson, reload and inspect its separate progress, test a real spoken turn and synthetic playback, and confirm feedback contains useful language advice without implementation metadata. Human content review and physical-phone testing remain separate release checks.
