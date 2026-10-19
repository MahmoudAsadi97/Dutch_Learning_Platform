"""Guided preparation preserves authored usage without joining unrelated senses."""
from __future__ import annotations

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from dlp.api.deps import context_dep, settings_dep
from dlp.api.routes_study import router
from dlp.config import Settings
from dlp.domains.curriculum.library import LibraryWord, library_for
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.study import content
from dlp.domains.study.responses import PreparedWord
from dlp.domains.study.schemas import Copy, GrammarPreparation, Word


def localized(nl, en):
    return {"nl": nl, "en": en, "fa": "متن آزمون"}


def transfer_word(stage="a2", identity="v001", *, sense="bench"):
    financial = sense == "bank"
    sentence = ("Ik betaal bij de bank.", "I pay at the bank.") if financial else (
        "Ik zit op de bank.", "I sit on the bench.")
    contexts = [("Bij de bank", "At the bank", *sentence, "present"),
                ("Een betaling", "A payment", "Gisteren betaalde ik bij de bank.",
                 "Yesterday I paid at the bank.", "past"),
                ("Een plan", "A plan", "Morgen zal ik bij de bank betalen.",
                 "Tomorrow I will pay at the bank.", "future")] if financial else [
        ("In het park", "In the park", *sentence, "present"),
        ("Na de wandeling", "After the walk", "Gisteren zat ik op de bank.",
         "Yesterday I sat on the bench.", "past"),
        ("Een afspraak", "An arrangement", "Morgen zal ik op de bank zitten.",
         "Tomorrow I will sit on the bench.", "future")]
    return LibraryWord.model_validate({
        "id": f"{stage}-{identity}", "term": "de bank", "part_of_speech": "noun",
        "topic": localized("Een plaats", "A place"),
        "meaning": localized("een financiële instelling" if financial else "een zitmeubel voor meer personen", sense),
        "example": localized(*sentence), "article": "de", "plural": "banken",
        "forms": [{"label": localized("Meervoud", "Plural"),
                   "text": localized("banken", "banks" if financial else "benches")}],
        "contexts": [{"id": f"{stage}-{identity}-use-{index}",
                      "setting": localized(setting_nl, setting_en),
                      "sentence": localized(sentence_nl, sentence_en),
                      "production_prompt": localized("Beschrijf jouw situatie.", "Describe your situation."),
                      "structure": structure}
                     for index, (setting_nl, setting_en, sentence_nl, sentence_en, structure)
                     in enumerate(contexts, 1)],
    })


def source_word(word, **updates):
    return Word.model_validate({
        "term": word.term, "part_of_speech": word.part_of_speech,
        "meaning": content.bilingual(word.meaning),
        "example": {"nl": "We zitten samen op de bank.", "en": "We sit together on the bench."},
        "minimum_stage": "a2", **updates,
    })


def lesson_payload(stage, words):
    pair = {"nl": "Een situatie", "en": "A situation"}
    return {"stage_id": stage, "topic_id": "family", "skill": "reading", "title": pair,
            "topic_title": pair, "review_status": "unreviewed",
            "preparation": {"words": words, "grammar": []},
            "activities": [{"id": "reading-one", "title": pair}], "activity_id": "reading-one",
            "parts": [], "context": {"title": pair, "text": [pair]},
            "policy": {"ephemeral": True, "pronunciation_assessed": False,
                       "recognized_certificate": False, "audio_locale": "nl-BE"}}


@pytest.mark.parametrize("stage", STAGE_IDS)
def test_every_stage_delivers_existing_authored_usage_through_the_public_response(stage, monkeypatch):
    vocabulary = library_for(stage).vocabulary
    available = [word for word in vocabulary if word.contexts]
    assert len(available) >= 150
    raw = {}
    for directory in ("library", *content.supplements.DIRECTORIES):
        path = content.CONTENT_DIR / directory / f"{stage}.json"
        if path.exists():
            for value in json.loads(path.read_text(encoding="utf-8"))["vocabulary"]:
                raw[value["id"]] = LibraryWord.model_validate(value)
    # Exercise the real older ID-bound records too: their POS and transfer data
    # can be supplied by the overlay rather than present in the original file.
    prepared = [content._prepared_word(stage, raw[word.id]) for word in available]
    payload = lesson_payload(stage, prepared)
    monkeypatch.setattr(content, "lesson", lambda *args, **kwargs: deepcopy(payload))
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[context_dep] = lambda: SimpleNamespace()
    app.dependency_overrides[settings_dep] = lambda: Settings(_env_file=None)
    with TestClient(app) as client:
        response = client.get(f"/study/{stage}/topics/family", params={"skill": "reading"})
    assert response.status_code == 200, response.text
    exposed = response.json()["preparation"]["words"]
    assert len(exposed) == len(available)
    assert '"fa"' not in response.text
    for original, public in zip(available, exposed, strict=True):
        assert public["id"] == original.id
        assert public["example"] == content.bilingual(original.example)
        assert public["article"] == original.article and public["plural"] == original.plural
        assert public["forms"] == [{"label": content.bilingual(form.label), "text": content.bilingual(form.text)}
                                   for form in original.forms]
        assert public["contexts"] == [
            {"id": item.id, "setting": content.bilingual(item.setting), "sentence": content.bilingual(item.sentence),
             "production_prompt": content.bilingual(item.production_prompt), "structure": item.structure}
            for item in original.contexts]


def test_exact_sense_enrichment_keeps_the_reading_example_and_uses_fresh_public_copies():
    authored = transfer_word()
    source = source_word(authored)
    before = source.model_dump()
    prepared = content._prepared_word("a2", source, word_id="a2-read-source-word-1", vocabulary=[authored])
    assert prepared["id"] == "a2-read-source-word-1"
    assert prepared["example"] == source.example.model_dump()
    assert prepared["meaning"] == source.meaning
    assert prepared["article"] == "de" and prepared["plural"] == "banken"
    assert prepared["contexts"][0]["sentence"] == content.bilingual(authored.contexts[0].sentence)
    assert prepared["contexts"][0]["sentence"] != prepared["example"]
    prepared["contexts"][0]["sentence"]["nl"] = "Changed by caller"
    again = content._prepared_word("a2", source, word_id="a2-read-source-word-1", vocabulary=[authored])
    assert again["contexts"][0]["sentence"]["nl"] != "Changed by caller"
    assert source.model_dump() == before
    PreparedWord.model_validate(again)


@pytest.mark.parametrize("case", ["other-sense", "other-dutch-sense", "other-part-of-speech", "other-stage",
                                  "ambiguous", "unknown-id", "foreign-id", "conflicting-id-pos",
                                  "missing-dutch-sense"])
def test_untrusted_matches_never_add_forms_or_contexts(case):
    word = transfer_word()
    source = source_word(word)
    candidates = [word]
    if case == "other-sense":
        candidates = [transfer_word(sense="bank")]
    elif case == "other-dutch-sense":
        source = source.model_copy(update={"meaning": {"nl": "een ophoping zand in het water", "en": "bench"}})
    elif case == "other-part-of-speech":
        source = source.model_copy(update={"part_of_speech": "verb"})
    elif case == "other-stage":
        candidates = [transfer_word(stage="c2")]
    elif case == "ambiguous":
        candidates.append(transfer_word(identity="v002"))
    elif case in {"unknown-id", "foreign-id"}:
        # A named reference must not silently fall back to a matching lemma/sense.
        source = SimpleNamespace(**source.model_dump(), id="a2-unknown" if case == "unknown-id" else "c2-v001")
        source.example = Copy.model_validate(source.example)
    elif case == "conflicting-id-pos":
        source = word.model_copy(update={"part_of_speech": "verb", "forms": [], "contexts": [],
                                         "article": None, "plural": None})
    else:
        source = source.model_copy(update={"meaning": {"en": "bench"}})
    prepared = content._prepared_word("a2", source, word_id="a2-read-source-word-1", vocabulary=candidates)
    assert prepared["example"] == content.bilingual(source.example)
    assert prepared["forms"] == prepared["contexts"] == []
    assert prepared["article"] is None and prepared["plural"] is None


@pytest.mark.parametrize("source_pos", [None, "noun"])
def test_a_known_same_stage_id_recovers_usage_without_replacing_its_source_gloss_or_example(source_pos):
    published = transfer_word()
    source = published.model_copy(update={"meaning": published.meaning.model_copy(update={"en": "a bench for sitting"}),
                                          "example": published.example.model_copy(update={
                                              "nl": "Wij zitten hier samen.", "en": "We sit here together."}),
                                          "part_of_speech": source_pos,
                                          "forms": [], "contexts": [], "article": None, "plural": None})
    prepared = content._prepared_word("a2", source, vocabulary=[published])
    assert prepared["meaning"]["en"] == "a bench for sitting"
    assert prepared["example"]["nl"] == "Wij zitten hier samen."
    assert prepared["part_of_speech"] == "noun"
    assert len(prepared["contexts"]) == 3 and prepared["plural"] == "banken"


def test_pack_does_not_select_an_unrelated_library_sense_from_a_lemma_in_the_story(monkeypatch):
    financial = transfer_word(sense="bank")
    monkeypatch.setattr(content, "_vocabulary_for", lambda stage: (financial,))
    word = Word(term="zitten", part_of_speech="verb", meaning={"nl": "een zittende houding hebben", "en": "to sit"},
                example={"nl": "Ik zit op de bank.", "en": "I sit on the bench."}, minimum_stage="a2")
    grammar = GrammarPreparation(title={"nl": "Een zin", "en": "A sentence"},
                                 explanation={"nl": "Dit is een zin.", "en": "This is a sentence."},
                                 examples=[word.example])
    source = SimpleNamespace(id="a2-source", words=[word], lines=[word.example], grammar=[grammar])
    canonical = SimpleNamespace(id="family", vocabulary=[])
    result = content._pack_preparation("a2", canonical, source)
    assert [item["term"] for item in result["words"]] == ["zitten"]
    assert result["words"][0]["contexts"] == []
    assert result["grammar"] == [grammar.model_dump()]


@pytest.mark.parametrize("area", ["meaning", "example", "form-label", "form-text", "setting", "sentence", "prompt"])
def test_public_vocabulary_contract_rejects_hidden_third_language_fields(area):
    prepared = content._word(transfer_word())
    targets = {"meaning": prepared["meaning"], "example": prepared["example"],
               "form-label": prepared["forms"][0]["label"], "form-text": prepared["forms"][0]["text"],
               "setting": prepared["contexts"][0]["setting"], "sentence": prepared["contexts"][0]["sentence"],
               "prompt": prepared["contexts"][0]["production_prompt"]}
    targets[area]["fa"] = "hidden"
    with pytest.raises(ValidationError, match="Extra inputs"):
        PreparedWord.model_validate(prepared)


def test_vocabulary_only_cache_tracks_overlay_changes_and_does_not_validate_legacy_stories(tmp_path, monkeypatch):
    base = transfer_word()
    path = tmp_path / "library/a2.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"stage_id": "a2", "vocabulary": [base.model_dump()],
                                "stories": ["deliberately not a legacy story model"]}), encoding="utf-8")
    monkeypatch.setattr(content, "CONTENT_DIR", tmp_path)
    before = content._vocabulary_for("a2")
    assert before[0].contexts[0].setting.nl == "In het park"
    overlay = tmp_path / "vocabulary-transfer/a2.json"
    overlay.parent.mkdir()
    entry = base.model_dump(include={"term", "part_of_speech", "article", "plural", "forms", "contexts"})
    entry["word_id"] = base.id
    entry["contexts"][0]["setting"]["nl"] = "Een andere, langere situatie"
    overlay.write_text(json.dumps({"schema_version": 1, "stage_id": "a2", "review_status": "unreviewed",
                                   "entries": [entry]}), encoding="utf-8")
    after = content._vocabulary_for("a2")
    assert after[0].contexts[0].setting.nl == "Een andere, langere situatie"
    assert before[0].contexts[0].setting.nl == "In het park"


def test_a_real_original_reading_keeps_source_evidence_separate_from_authored_usage():
    source = next(item for item in content.readings_for("pre-a1") if item.id == "pre-a1-read-citroenproef")
    result = content.lesson("pre-a1", source.topic_id, "reading", activity_id=source.id)
    assert result["context"]["text"] == [content.bilingual(line) for line in source.lines]
    for original, prepared in zip(source.words, result["preparation"]["words"], strict=True):
        assert prepared["example"] == content.bilingual(original.example)
        assert prepared["example"] in result["context"]["text"]
    sour = next(word for word in result["preparation"]["words"] if word["term"] == "zuur")
    assert len(sour["contexts"]) == 3
    assert any(item["sentence"] != sour["example"] for item in sour["contexts"])
    assert '"fa"' not in json.dumps(result)
