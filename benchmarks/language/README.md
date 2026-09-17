# Language benchmark

Forty cases in six categories (grammar, Belgian lexicon, appointment intent, register,
Persian comprehension, time expressions) that any `ChatModel` can be run against. Results
land in `results/` (ignored by Git) tagged with provider, model, prompt version and commit.

```
python benchmarks/language/harness.py --provider expected   # dry run: scoring accepts correct answers (100 %)
python benchmarks/language/harness.py --provider wrong      # dry run: scoring rejects wrong answers (0 %)
python benchmarks/language/harness.py --provider local      # Ollama model from .env (LOCAL_CHAT_MODEL)
```

The two dry runs are a plumbing test. They say nothing about any model. A real
comparison between models only happens in Phase B, with the same cases and the same
prompt version, and the numbers are recorded in `DECISIONS.md` before a model is chosen.

Cases are provisional and unreviewed, like the rest of the fixed Dutch content.
