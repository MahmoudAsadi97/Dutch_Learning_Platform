# Video lessons

A learner picks a level, a topic and a form, and gets a short presenter video in Belgian Dutch: between
twenty seconds and two and a half minutes, with Dutch subtitles, a transcript that follows the playhead
with English and Persian under every scene, a glossary to save words from, and two or three questions.
The script is written by the chat model and checked by the same validator as the stories; the voice and
the picture come from the configured renderer.

## Flow

```
POST /videos {stage, topic, kind} ──▶ video_lessons row (queued) ──▶ job: video_script
                                                                        │
                                   script prompt (stage profile · topic · form · known words)
                                                                        │
                                             chat_strong.complete(schema=VideoScript)
                                                                        │
                                          check_script (validator + scene counts + minimum length)
                                            ok ──▶ reserve video_seconds ──▶ renderer.start
                                            not ok ──▶ one rewrite with the findings · then failed (quality)
                                                                        │
                                                               job: video_render (polls)
                                                                        │
                           fetch ──▶ subtitle track → cues ──▶ remux (index first) ──▶ blob ──▶ ready
```

* `domains/videos/schemas.py` — `VideoScript`: title, 3–7 scenes (`paragraphs`, what the presenter says),
  English and Persian per scene, one on-screen keyword per scene, glossary, questions with `evidence`.
  The field names match the story draft so `validate_draft` checks both.
* `domains/videos/prompts.py` — the presenter prompt (`video-script-v1`): Belgian Standard Dutch rules, the
  brief as JSON (level, length in words and seconds, sentence limits, grammar, new words), the form
  (*uitleg*: explain with everyday examples; *verhaal*: tell a short story in the present tense).
* `domains/videos/service.py` — `video_profile` (the stage profile bounded to 3–6 scenes and to the
  seconds that fit), `check_script`, the two jobs, views, learner actions.
* `domains/videos/media.py` — pulls the subtitle track out of the rendered file as cues, attaches each
  cue to its scene, remuxes for progressive playback, measures the duration, writes WebVTT.
* `providers/video_azure.py` — the Azure text-to-speech avatar (batch synthesis API 2024-08-01).
* `providers/video_local.py` — scene cards: any voice over drawn cards, assembled with ffmpeg.
* `api/routes_videos.py` — `/videos`, `/videos/{id}`, `/videos/{id}/media` (byte ranges),
  `/videos/{id}/subtitles.vtt`, `/watched`, `/answers`, `/rating`, `/words`, `/retry`.

## Length

`VIDEO_MIN_SECONDS` (20) and `VIDEO_MAX_SECONDS` (150) bound the writer's brief: the stage profile's word
range is clipped so the spoken script fits (about 2.3 words per second plus a pause per scene), and the
floor is raised where a level's shortest story would not fill twenty seconds. A script that would still
speak for less than the minimum fails the check (`video_too_short`) and is sent back with the instruction
to add a scene. The result per level:

| Level | Words | Spoken |
|---|---|---|
| pre-A1 | 40–95 | ≈ 21–47 s |
| A1 | 60–130 | ≈ 30–62 s |
| A2 | 110–200 | ≈ 51–93 s |
| B1 | 154–280 | ≈ 71–127 s |
| C2 | 170–310 | ≈ 78–140 s |

## Renderers

| `VIDEO_PROVIDER` | Picture | Voice | Where |
|---|---|---|---|
| `avatar` | a standard Azure avatar (`VIDEO_AVATAR_CHARACTER` `lisa`, `VIDEO_AVATAR_STYLE` `graceful-sitting`), H.264 MP4 with the subtitles soft-embedded by the service | `AZURE_TTS_VOICE` | Azure; batch avatar synthesis is available in West Europe |
| `cards` | one flat card per scene with the keyword and the title, drawn by ffmpeg (`VIDEO_FONT` or fontconfig's default) | the configured voice (Piper locally, Azure in the cloud) | anywhere with ffmpeg |
| `fixture` | the cards, small and fast, with the tone voice | fixture | tests |
| `auto` (default) | avatar when speech is Azure, cards otherwise, fixture when the voice is a fixture | | |

Both real renderers return an MP4 with a subtitle text track; `media.finalize` treats them the same.
The avatar job is asynchronous on the service side: `video_render` polls every twenty seconds and gives up
after `VIDEO_RENDER_TIMEOUT_SECONDS` (1200) or ninety polls, releasing the reserved seconds. The job's
time to live on the service is 24 hours; the job is deleted once the file is stored.

The avatar needs the Speech resource's custom domain for managed-identity sign-in. It is derived from
`AZURE_SPEECH_RESOURCE_ID` (the account name) or set with `AZURE_SPEECH_ENDPOINT`; with a subscription key
the regional endpoint works as well.

## Cost and limits

The standard avatar is billed per second of video (West Europe: $1 per minute for batch synthesis, plus
the characters synthesised at the usual text-to-speech rate). Before a render starts the estimated
seconds are reserved against `video_seconds` (`USAGE_DAILY_VIDEO_SECONDS` 300, `USAGE_TOTAL_VIDEO_SECONDS`
7200); the measured duration is committed when the file is stored and the reservation is released when
the render fails. The writer's model calls and tokens are reserved like the stories'. At most two videos
per learner are in the making at once. A learner who runs out of videotime sees it on the tile
(`allowance_video`), and the Settings page shows the counter.

## Playback

The file is served by the API from blob storage with HTTP byte ranges (`Accept-Ranges`, `206`), through
the same-origin proxy, so the player can seek without downloading everything. Subtitles are a separate
WebVTT track built from the stored cues; the transcript highlights the scene the playhead is in and a
click on a scene seeks to its first cue. Watching to the end (or *Klaar met kijken*) awards ten points
once, each correct answer three; words are saved to the word bank with `source_kind = video`.

## Honesty

The interface labels the script as generated and unreviewed, the voice as synthetic and the presenter
as virtual ("geen echte persoon"). No pronunciation or level judgement is attached to watching.

## Trying it on the laptop

```
python scripts/run.py dev        # VIDEO_PROVIDER=auto → scene cards with the Piper voice
```

Open **Video's**, choose a level and a topic, and wait: the 8B model writes the script in one to three
minutes, the cards render in seconds. `VIDEO_FONT=/path/to/a.ttf` picks the font for the cards when
fontconfig has none. `cd apps/api && python -m pytest tests/test_videos.py` runs the engine with the
fixture renderer.
