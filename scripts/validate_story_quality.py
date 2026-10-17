"""Audit authored story structure and duplication without certifying language quality.

This command and the learner catalogue share the same structural inventory rules.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# The CLI also works from a fresh source checkout without an editable API install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api/src"))

from dlp.domains.curriculum.story_inventory import (
    LANGS,
    PACKS,
    STAGES,
    audit,
    normal,
    quantities,
    shingles,
    tokens,
)

__all__ = ["LANGS", "PACKS", "STAGES", "audit", "normal", "quantities", "shingles", "tokens"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", type=Path, default=Path(__file__).resolve().parents[1] / "content")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero for structural errors.")
    parser.add_argument("--require-targets", action="store_true", help="Also fail unfinished authored-story and word targets.")
    args = parser.parse_args()
    result = audit(args.content)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["claim"])
    for row in result["stages"]:
        print(f"{row['stage']:7} authored={row['authored_stories']:3} legacy={row['legacy_stories']:3} "
              f"words={row['distinct_vocabulary']:3} authored_shortfall={row['authored_story_shortfall']}")
    counts = Counter(issue["code"] for issue in result["issues"])
    print("Findings: " + json.dumps(dict(sorted(counts.items()))))
    print("Inventory: " + result["inventory_status"])
    return int((args.strict and result["structural_errors"] > 0)
               or (args.require_targets and result["inventory_status"] == "incomplete"))


if __name__ == "__main__":
    raise SystemExit(main())
