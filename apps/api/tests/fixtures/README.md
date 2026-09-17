# Test fixtures

Deterministic inputs for CI and failure-injection tests. They exercise plumbing only and
never count as verification of a provider.

- `chat_replies.json` — canned structured replies for `FixtureChatModel`, keyed by prompt version.
- `tone_1s.wav` — a generated 1-second tone (mono, 16 kHz, 16-bit PCM). It is **not** a recording of speech; it lets the audio pipeline and the fixture transcriber run without a microphone. Its sidecar `tone_1s.json` holds the transcript the fixture transcriber returns for it.
- `dutch_sentence.wav` — reserved name for a real recorded Dutch sentence captured on the owner's laptop through the microphone check page (see `OWNER_ACTIONS.md`). Absent until it has been recorded.
