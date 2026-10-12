# Interactive learning preview

This standalone preview demonstrates connected practice and a proposed interface. It is separate from
Next.js/FastAPI and the Azure deployment. All responses are fixtures; no credentials or paid services
are used. Learning targets and Dutch/support text are provisional, not human-reviewed.

Open the [owner-private hosted preview](https://taalstudio-learning-preview.nimaa-asadii.chatgpt.site).
To run these files on a laptop, from this directory:

```bash
python -m http.server 8080 --directory dist
```

Open http://localhost:8080. The preview offers the twelve-stage explorer, language support selection,
a connected four-skill appointment mission, a logged hint ladder, writing revision, story/transfer
reflection and official exam links. Device speech synthesis is optional and labelled; it is not
Azure Speech or a pronunciation assessment. Reset clears the current preview session.

Checks:

```bash
node --check dist/app.mjs
node --check dist/model.mjs
node --test tests/demo.test.mjs
```

The tests cover deterministic scenario boundaries and actual event handlers through a small DOM stub.
They do not replace browser, screen-reader or physical-phone testing. No browser rendering verification
was available in the preview workspace used for this version.
