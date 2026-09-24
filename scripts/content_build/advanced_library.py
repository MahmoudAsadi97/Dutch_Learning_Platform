"""Assemble advanced libraries from original multilingual editorial source files.

The 750-term collection is not a frequency list or a certified CEFR inventory.
C1, the C2 bridge and C2 deliberately revisit some complete anecdotes with other
material around them. They never gain apparent difficulty through filler tails.
All language and educational calibration remains explicitly unreviewed.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LANGS = ('nl', 'en', 'fa')
ALIASES = {
    'de wederhoor': 'het wederhoor',
    'de motiveringsgebrek': 'het motiveringsgebrek',
    'de wilsgebrek': 'het wilsgebrek',
    'de rendement': 'het rendement',
    'de waardenconflict': 'het waardenconflict',
}


def tri(nl, en, fa):
    return dict(zip(LANGS, (nl, en, fa)))


TOPICS = [
    ('bestuur', tri('Bestuur en inspraak', 'Governance and participation', 'اداره و مشارکت')),
    ('onderzoek', tri('Onderzoek en bewijs', 'Research and evidence', 'پژوهش و شواهد')),
    ('werk', tri('Werk en samenwerking', 'Work and collaboration', 'کار و همکاری')),
    ('media', tri('Media en taal', 'Media and language', 'رسانه و زبان')),
    ('recht', tri('Rechten en verantwoordelijkheid', 'Rights and responsibility', 'حقوق و مسئولیت')),
    ('omgeving', tri('Omgeving en duurzaamheid', 'Environment and sustainability', 'محیط زیست و پایداری')),
    ('cultuur', tri('Cultuur en herinnering', 'Culture and memory', 'فرهنگ و حافظه')),
    ('zorg', tri('Zorg en samenleving', 'Care and society', 'مراقبت و جامعه')),
    ('economie', tri('Economie en verdeling', 'Economics and distribution', 'اقتصاد و توزیع')),
    ('ethiek', tri('Ethiek en technologie', 'Ethics and technology', 'اخلاق و فناوری')),
]


def normal(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def translated(value):
    assert set(value) == set(LANGS), value
    assert all(isinstance(value[k], str) and value[k].strip() for k in LANGS), value
    assert re.search(r'[\u0600-\u06ff]', value['fa']), value
    assert normal(value['en']) != normal(value['nl']), value


def read_bank():
    result = {}
    current = None
    for line in (HERE / 'advanced_bank.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        if line.startswith('['):
            current = line.strip('[]')
            result[current] = {}
            continue
        term, definition, english, persian = line.split('|')
        term = ALIASES.get(term, term)
        assert term not in result[current]
        result[current][term] = tri(definition, english, persian)
    assert len(result) == 10
    assert all(len(terms) == 75 for terms in result.values())
    return result


def read_examples():
    result = {}
    for part in ('civic', 'public', 'social'):
        source = json.loads((HERE / f'advanced_examples_{part}.json').read_text())
        for term, example in source.items():
            term = ALIASES.get(term, term)
            assert term not in result, term
            translated(example)
            result[term] = example
    assert len(result) == 750
    assert len({normal(x['nl']) for x in result.values()}) == 750
    return result


def read_stories(bank):
    result = {}
    for part in ('civic', 'public', 'social', 'econ_ethics'):
        source = json.loads((HERE / f'advanced_story_{part}.json').read_text())
        for topic, items in source.items():
            assert topic not in result, topic
            assert len(items) == 15, (topic, len(items))
            all_terms = []
            for item in items:
                item['terms'] = [ALIASES.get(t, t) for t in item['terms']]
                assert len(item['terms']) == 5, (topic, item['title'])
                assert len(set(item['terms'])) == 5
                assert 2 <= len(item['paragraphs']) <= 12
                translated(item['title'])
                for paragraph in item['paragraphs']:
                    translated(paragraph)
                all_terms.extend(item['terms'])
            assert len(set(all_terms)) == 75, (topic, Counter(all_terms))
            assert set(all_terms) == set(bank[topic]), (topic, set(all_terms) ^ set(bank[topic]))
            result[topic] = items
    assert set(result) == set(bank)
    return result


def last_sentence(paragraph):
    parts = re.split(r'(?<=[.!?؟])\s+', paragraph.strip())
    return parts[-1].strip()


def question_for(story, companions, answer_index):
    """Practice checks ask which concrete outcome belongs to the current story.

    Distractors are real outcomes of different anecdotes in the same topic,
    not invented alleged facts about the current story or level-test scoring.
    """
    correct = {lang: last_sentence(story['paragraphs'][-1][lang]) for lang in LANGS}
    candidates = []
    seen = {normal(correct['nl'])}
    for other in companions:
        if other is story:
            continue
        option = {lang: last_sentence(other['paragraphs'][-1][lang]) for lang in LANGS}
        if normal(option['nl']) in seen:
            continue
        seen.add(normal(option['nl']))
        candidates.append(option)
    assert len(candidates) >= 3
    options = candidates[:3]
    options.insert(answer_index, correct)
    return {
        'prompt': tri('Welke uitspraak past bij de afloop van dit verhaal?',
                      'Which statement matches the outcome of this story?',
                      'کدام گفته با پایان این داستان سازگار است؟'),
        'options': options,
        'answer_index': answer_index,
        'explanation': tri(
            'De laatste alinea beschrijft deze uitkomst: ' + correct['nl'],
            'The final paragraph describes this outcome: ' + correct['en'],
            'بند آخر این نتیجه را بیان می‌کند: ' + correct['fa']),
    }


def validate(pack):
    words = pack['vocabulary']
    stories = pack['stories']
    assert len(words) == 500 and len(stories) == 100
    assert len({w['id'] for w in words}) == 500
    assert len({normal(w['term']) for w in words}) == 500
    assert len({s['id'] for s in stories}) == 100
    assert len({normal(s['title']['nl']) for s in stories}) == 100
    assert len({normal(' '.join(p['nl'] for p in s['paragraphs'])) for s in stories}) == 100
    by_id = {w['id']: w for w in words}
    used = set()
    for word in words:
        for key in ('meaning', 'topic', 'example'):
            translated(word[key])
        assert len(word['example']['nl']) < 600, word['id']
        lemma = re.sub(r'^(de|het) ', '', normal(word['term']))
        assert lemma in normal(word['example']['nl']), word['term']
    for story in stories:
        translated(story['title']); translated(story['topic'])
        assert len(story['paragraphs']) >= 2
        for p in story['paragraphs']:
            translated(p)
            assert len(p['nl']) <= 600, (story['id'], 'paragraph exceeds speech request size')
        ids = story['vocabulary_ids']
        assert len(ids) == 5 and len(set(ids)) == 5
        assert set(ids).issubset(by_id)
        used.update(ids)
        text = normal(' '.join(p['nl'] for p in story['paragraphs']))
        for word_id in ids:
            lemma = re.sub(r'^(de|het) ', '', normal(by_id[word_id]['term']))
            assert lemma in text, (story['id'], by_id[word_id]['term'])
        q = story['question']
        translated(q['prompt']); translated(q['explanation'])
        assert 0 <= q['answer_index'] < 4 and len(q['options']) == 4
        for o in q['options']:
            translated(o)
        assert len({normal(o['nl']) for o in q['options']}) == 4
    assert used == set(by_id)
    assert Counter(s['question']['answer_index'] for s in stories) == {0: 25, 1: 25, 2: 25, 3: 25}


def main():
    bank = read_bank()
    examples = read_examples()
    assert set(examples) == {term for terms in bank.values() for term in terms}
    pool = read_stories(bank)
    source = json.loads((ROOT / 'content/curriculum/path.json').read_text())
    original = {s['id']: {normal(v['term']): v for v in s['vocabulary']} for s in source['stages']}
    for stage_index, stage_id in enumerate(('c1', 'pre-c2', 'c2')):
        chosen = list(range(10)) if stage_id == 'c1' else list(range(5, 15)) if stage_id == 'pre-c2' else list(range(5)) + list(range(10, 15))
        vocabulary = []
        stories = []
        reused = 0
        for topic_index, (topic, label) in enumerate(TOPICS):
            for source_index in chosen:
                story = pool[topic][source_index]
                word_ids = []
                for term in story['terms']:
                    previous = original[stage_id].get(normal(term))
                    word_id = f'{stage_id}-v{len(vocabulary)+1:03d}'
                    # Existing stage material remains untouched in path.json.
                    # Reuse its meaning where the same term belongs in this library.
                    meaning = previous['meaning'] if previous else bank[topic][term]
                    reused += int(previous is not None)
                    vocabulary.append({'id': word_id, 'term': term, 'topic': label,
                                       'meaning': meaning, 'example': examples[term]})
                    word_ids.append(word_id)
                index = len(stories)
                companions = pool[topic][source_index+1:] + pool[topic][:source_index]
                question = question_for(story, companions, (index+stage_index)%4)
                stories.append({'id': f'{stage_id}-s{index+1:03d}',
                                'title': story['title'], 'topic': label,
                                'paragraphs': story['paragraphs'],
                                'vocabulary_ids': word_ids,
                                'question': question})
        pack = {'schema_version': 1, 'stage_id': stage_id, 'review_status': 'unreviewed',
                'vocabulary': vocabulary, 'stories': stories}
        validate(pack)
        path = ROOT / 'content/library' / f'{stage_id}.json'
        path.write_text(json.dumps(pack, ensure_ascii=False, indent=2)+'\n')
        print(f'{stage_id}: {len(vocabulary)} words, {len(stories)} stories, {reused} prior terms reused')


if __name__ == '__main__':
    main()
