# Azure Speech fixtures

Recorded *shapes* of the REST replies (short-audio recognition, detailed format) used by
`tests/test_speech_azure.py`. They document the contract the adapters parse; they are not proof of a
live call. `stt_success.json` follows the documented fields (`RecognitionStatus`, `Offset` and
`Duration` in 100-ns ticks, `DisplayText`, `NBest[]`); `stt_nomatch.json` is the empty result.
Synthesis returns raw RIFF/WAV bytes, so the test builds one with the tone generator.
