"""Versioned stage grammar rounds, kept separate from assessment content."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from dlp.domains.curriculum.schemas import STAGE_IDS, Grammar


def stamp(root: Path) -> tuple:
    return tuple((p.stem, p.stat().st_mtime_ns, p.stat().st_size)
                 for p in sorted((root / 'grammar-bank').glob('*.json')))


def merge(data: dict, root: Path) -> dict:
    result = deepcopy(data)
    for stage in result['stages']:
        path = root / 'grammar-bank' / f"{stage['id']}.json"
        if not path.exists():
            continue
        pack = json.loads(path.read_text())
        if pack.get('stage_id') != stage['id'] or stage['id'] not in STAGE_IDS:
            raise ValueError('grammar stage must match its file')
        if pack.get('review_status') != 'unreviewed' or pack.get('schema_version') != 1:
            raise ValueError('unsupported grammar review or schema version')
        rounds = [Grammar.model_validate(g) for g in pack['rounds']]
        if len(rounds) != 10 or len({g.id for g in rounds}) != 10:
            raise ValueError('grammar bank requires ten distinct rounds')
        ids = {g['id'] for g in stage['grammar']}
        for group in rounds:
            if not group.id.startswith('practice-') or group.id in ids or len(group.practice) != 10:
                raise ValueError('grammar bank has conflicting or incomplete rounds')
            if any(not q.id.startswith(f"{stage['id']}-{group.id}-") for q in group.practice):
                raise ValueError('grammar questions must belong to their stage and round')
            ids.add(group.id)
            stage['grammar'].append(group.model_dump())
    return result
