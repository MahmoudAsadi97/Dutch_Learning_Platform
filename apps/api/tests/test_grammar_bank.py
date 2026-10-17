"""Coverage, reproducibility and answer integrity for the authored grammar rounds."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from dlp.domains.curriculum import grammar
from dlp.domains.curriculum.schemas import STAGE_IDS, Curriculum

ROOT = Path(__file__).resolve().parents[3]


def load_builder():
    spec = importlib.util.spec_from_file_location('grammar_bank', ROOT / 'scripts/content_build/grammar_bank.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_stage_has_ten_original_ten_question_rounds_and_preserves_prior_rules():
    base = json.loads((ROOT / 'content/curriculum/path.json').read_text())
    data = Curriculum.model_validate(grammar.merge(base, ROOT / 'content'))
    assert tuple(s.id for s in data.stages) == STAGE_IDS
    identifiers, prompts, sentences = set(), set(), set()
    for stage in data.stages:
        rounds = [g for g in stage.grammar if g.id.startswith('practice-')]
        assert len(rounds) == 10
        assert len({g.id for g in rounds}) == 10
        assert any(not g.id.startswith('practice-') for g in stage.grammar)
        for topic in rounds:
            assert len(topic.practice) == 10
            for question in topic.practice:
                assert question.id not in identifiers
                assert question.prompt.nl not in prompts
                assert question.model_sentence not in sentences
                identifiers.add(question.id)
                prompts.add(question.prompt.nl)
                sentences.add(question.model_sentence)
                assert len({o.nl.casefold() for o in question.options}) == len(question.options)
                stem = question.prompt.nl.removeprefix('Kies de juiste vorm: ')
                assert stem.count('…') == 1
                assert stem.replace('…', question.options[question.answer_index].nl) == question.model_sentence
                for language in ('nl', 'en', 'fa'):
                    assert question.model_sentence in getattr(question.explanation, language)
    assert len(identifiers) == 1200


def test_grammar_build_is_reproducible_and_keeps_assessments_unchanged():
    current = json.loads((ROOT / 'content/curriculum/path.json').read_text())
    rebuilt = load_builder().build()
    assert grammar.merge(current, ROOT / 'content') == rebuilt
    for previous, result in zip(current['stages'], rebuilt['stages'], strict=True):
        assert {k: v for k, v in previous.items() if k != 'grammar'} == {
            k: v for k, v in result.items() if k != 'grammar'
        }
