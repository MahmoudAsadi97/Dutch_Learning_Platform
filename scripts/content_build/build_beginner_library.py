"""Build the original, unreviewed beginner spiral library from authored scenes.

The source contains 100 distinct settings. Each setting has five vocabulary
items, three progressively expanded versions and an answerable comprehension
question. Reuse between stages is intentional spiral review, not a CEFR
frequency claim. No textbook text, OCR or external model output is loaded here.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name('beginner_source.txt')
STAGES = ('pre-a1', 'a1', 'pre-a2')
LANGUAGES = ('nl', 'en', 'fa')


def trilingual(line: str) -> dict[str, str]:
    pieces = line.split('|')
    if len(pieces) != 3 or not all(p.strip() for p in pieces):
        raise ValueError(f'Invalid trilingual source: {line!r}')
    return dict(zip(LANGUAGES, pieces, strict=True))


def normalized(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(c))


def occurrences(term: str, text: str) -> bool:
    """Recognise article-free terms and the explicitly authored inflections."""
    lemma = re.sub(r'^(de|het) ', '', normalized(term))
    text = normalized(text)
    alternatives = {
        'terugkomen': ('terugkomen', 'terug te komen'),
        'schoonmaken': ('schoonmaken', 'schoon te maken'),
        'lang': ('lang', 'lange'), 'groot': ('groot', 'grote'),
        'zwaar': ('zwaar', 'zware'), 'droog': ('droog', 'droge'),
        'koud': ('koud', 'koude'), 'oud': ('oud', 'oude'),
        'goed': ('goed', 'goede'), 'slecht': ('slecht', 'slechte'),
        'best': ('best', 'beste'),
    }.get(lemma, (lemma, lemma + 'e', lemma + 'en', lemma + 's'))
    return any(re.search(r'(?<!\w)' + re.escape(word) + r'(?!\w)', text) for word in alternatives)


def split_compounds(text: str) -> str:
    """Shorten authored semicolon clauses without adding invented filler."""
    return re.sub(r';\s+([a-zA-Z])', lambda m: '. ' + m[1].upper(), text)


def build() -> None:
    scenes = [block.splitlines() for block in SOURCE.read_text(encoding='utf-8').strip().split('\n---\n')]
    assert len(scenes) == 100, len(scenes)
    for stage_index, stage_id in enumerate(STAGES):
        vocabulary = []
        stories = []
        unmatched = []
        for scene_index, lines in enumerate(scenes, 1):
            assert len(lines) == 12, (scene_index, len(lines))
            title, topic = map(trilingual, lines[:2])
            paragraphs = [trilingual(line) for line in lines[3 + stage_index * 2:5 + stage_index * 2]]
            if stage_index:
                paragraphs = [{lang: split_compounds(value) for lang, value in paragraph.items()} for paragraph in paragraphs]
            ids = []
            for offset, raw in enumerate(lines[2].split(';'), 1):
                term, meaning_nl, meaning_en, meaning_fa = raw.split('~')
                identifier = f'{stage_id}-v{(scene_index - 1) * 5 + offset:03d}'
                example = next((paragraph for paragraph in paragraphs if occurrences(term, paragraph['nl'])), None)
                if example is None:
                    unmatched.append((scene_index, term, [p['nl'] for p in paragraphs]))
                    example = {lang: ' '.join(p[lang] for p in paragraphs) for lang in LANGUAGES}
                vocabulary.append({
                    'id': identifier, 'term': term, 'topic': topic,
                    'meaning': {'nl': meaning_nl, 'en': meaning_en, 'fa': meaning_fa},
                    'example': example,
                })
                ids.append(identifier)
            answer, distractor = trilingual(lines[10]), trilingual(lines[11])
            answer_index = (scene_index + stage_index) % 2
            options = [answer, distractor] if answer_index == 0 else [distractor, answer]
            stories.append({
                'id': f'{stage_id}-s{scene_index:03d}',
                'title': title, 'topic': topic, 'paragraphs': paragraphs,
                'vocabulary_ids': ids,
                'question': {
                    'prompt': trilingual(lines[9]), 'options': options,
                    'answer_index': answer_index,
                    'explanation': {lang: ' '.join(p[lang] for p in paragraphs) for lang in LANGUAGES},
                },
            })
        if unmatched:
            for item in unmatched:
                print('UNMATCHED', stage_id, *item)
            raise ValueError(f'{len(unmatched)} target words absent from {stage_id}')
        assert len(vocabulary) == 500
        assert len({normalized(v['term']) for v in vocabulary}) == 500
        assert len({v['id'] for v in vocabulary}) == 500
        assert len(stories) == len({s['id'] for s in stories}) == 100
        assert set(ids for s in stories for ids in s['vocabulary_ids']) == {v['id'] for v in vocabulary}
        assert sum(s['question']['answer_index'] for s in stories) == 50
        assert len({tuple(p['nl'] for p in s['paragraphs']) for s in stories}) == 100
        data = {
            'schema_version': 1,
            'stage_id': stage_id,
            'review_status': 'unreviewed',
            'vocabulary': vocabulary,
            'stories': stories,
        }
        destination = ROOT / 'content' / 'library' / f'{stage_id}.json'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{stage_id}: {len(vocabulary)} vocabulary cards; {len(stories)} stories; all 500 targets covered')


if __name__ == '__main__':
    build()
