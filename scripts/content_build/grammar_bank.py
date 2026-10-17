"""Build original Dutch grammar rounds; the CEFR placement and translations remain provisional.

Each source row is an independently authored context, not a generated name substitution.
Options stay in Dutch: English/Persian explain the task and rule, not the answer before checking.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name('grammar')


def build(root: Path = ROOT) -> dict:
    data = json.loads((root / 'content/curriculum/path.json').read_text())
    definitions = json.loads((SOURCE / 'rules.json').read_text())
    seen: set[str] = set()
    for stage in data['stages']:
        groups: list[dict] = []
        current = None
        for line in (SOURCE / f"{stage['id']}.txt").read_text().splitlines():
            if not line.strip():
                continue
            if line.startswith('@'):
                key = line[1:]
                rule = definitions[key]
                current = {'id': f'practice-{key}', 'title': rule['title'],
                           'explanation': rule['explanation'], 'examples': rule['examples'], 'practice': []}
                groups.append(current)
                continue
            if current is None:
                raise ValueError('A question must belong to a rule')
            parts = line.split('|')
            if len(parts) not in (3, 4):
                raise ValueError(f"{stage['id']}: need prompt, answer and one or two distractors: {line}")
            prompt, correct, *wrong = parts
            if len({x.casefold() for x in (correct, *wrong)}) != len(parts)-1:
                raise ValueError('Options must differ')
            if prompt.count('…') != 1 or prompt in seen:
                raise ValueError(f'Prompts need one gap and must be unique across stages: {prompt}')
            seen.add(prompt)
            sentence = prompt.replace('…', correct)
            number = len(current['practice']) + 1
            qid = f"{stage['id']}-{current['id']}-{number:02}"
            options = [correct, *wrong]
            rotation = int(hashlib.sha256(qid.encode()).hexdigest()[:8], 16) % len(options)
            options = options[rotation:] + options[:rotation]
            reason = current['explanation']
            current['practice'].append({
                'id': qid,
                'prompt': {'nl': 'Kies de juiste vorm: ' + prompt,
                           'en': 'Choose the correct Dutch form: ' + prompt,
                           'fa': 'شکل درست هلندی را انتخاب کن: ' + prompt},
                'options': [{'nl': option, 'en': option, 'fa': option} for option in options],
                'answer_index': options.index(correct),
                'explanation': {'nl': f"Juist: {sentence} {reason['nl']}",
                                'en': f"Correct Dutch sentence: {sentence} {reason['en']}",
                                'fa': f"جملهٔ درست هلندی: {sentence} {reason['fa']}"},
                'model_sentence': sentence,
            })
        if len(groups) != 10 or any(len(g['practice']) != 10 for g in groups):
            raise ValueError(f"{stage['id']}: exactly ten rounds with ten authored questions required")
        # Existing rule IDs and evidence remain intact; rebuilding replaces only owned rounds.
        stage['grammar'] = [g for g in stage['grammar'] if not g['id'].startswith('practice-')] + groups
    return data


def main() -> None:
    from dlp.domains.curriculum.schemas import Curriculum
    data = build()
    Curriculum.model_validate(data)
    destination = ROOT / 'content/grammar-bank'
    destination.mkdir(exist_ok=True)
    for stage in data['stages']:
        pack = {'schema_version': 1, 'stage_id': stage['id'], 'review_status': 'unreviewed',
                'rounds': [g for g in stage['grammar'] if g['id'].startswith('practice-')]}
        (destination / f"{stage['id']}.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2) + '\n')
    print('Built 1,200 original grammar questions in 120 ten-question rounds.')


if __name__ == '__main__':
    main()
