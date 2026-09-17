"""Language-benchmark harness.

Runs every case in `cases.jsonl` through any `ChatModel` and scores the structured
reply. Every result file is tagged with the provider, the model and the prompt
version so runs on different backends can be compared later.

This is a plumbing test until real models are compared in Phase B: the `--provider
expected` and `--provider wrong` dry runs prove that scoring accepts correct answers
and rejects wrong ones, nothing more. They are not a model selection.

    python benchmarks/language/harness.py --provider expected      # plumbing dry run, must score 100 %
    python benchmarks/language/harness.py --provider wrong         # plumbing dry run, must score 0 %
    python benchmarks/language/harness.py --provider local         # Ollama on the laptop
    python benchmarks/language/harness.py --provider azure --tier strong   # Phase B
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api" / "src"))

from pydantic import BaseModel, Field  # noqa: E402

from dlp.providers.base import ChatMessage, ChatModel, ChatResult, ProviderError  # noqa: E402

PROMPT_VERSION = "benchmark-v1"
CASES_PATH = HERE / "cases.jsonl"
RESULTS_DIR = HERE / "results"

SYSTEM_PROMPT = (
    "Je bent een taalassistent voor Belgisch Standaardnederlands (niveau A2). "
    "Volg de opdracht precies en antwoord kort. Geef geen uitleg tenzij gevraagd."
)


class BenchmarkAnswer(BaseModel):
    answer: str = Field(description="the answer to the task, and nothing else")
    notes: str = Field(default="", description="optional short remark")


@dataclass
class Case:
    id: str
    category: str
    instruction: str
    input: str
    expected: dict[str, Any]
    scoring: str  # exact | any_of | contains_all | json_field


@dataclass
class CaseResult:
    case_id: str
    category: str
    passed: bool
    answer: str
    expected: dict[str, Any]
    latency_ms: int
    input_tokens: int
    output_tokens: int
    attempts: int
    error: str = ""


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).strip().lower()
    text = re.sub(r"[\"'“”‘’`]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(".!?")


def load_cases(path: Path = CASES_PATH) -> list[Case]:
    cases: list[Case] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        raw = json.loads(line)
        cases.append(Case(**raw))
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case ids")
    return cases


def score(case: Case, answer: str) -> bool:
    got = normalise(answer)
    if case.scoring == "exact":
        return got == normalise(case.expected["answer"])
    if case.scoring == "any_of":
        return any(got == normalise(option) for option in case.expected["any_of"])
    if case.scoring == "contains_all":
        return all(normalise(part) in got for part in case.expected["contains_all"])
    if case.scoring == "json_field":
        try:
            value = json.loads(answer)
        except json.JSONDecodeError:
            return False
        return all(normalise(str(value.get(key, ""))) == normalise(str(expected))
                   for key, expected in case.expected["fields"].items())
    raise ValueError(f"unknown scoring rule {case.scoring}")


def build_messages(case: Case) -> list[ChatMessage]:
    task = f"Opdracht: {case.instruction}\nInvoer: {case.input}"
    if case.scoring == "json_field":
        task += "\nZet in het veld 'answer' een JSON-string met de gevraagde velden."
    return [ChatMessage("system", SYSTEM_PROMPT), ChatMessage("user", task)]


class ExpectedAnswerModel(ChatModel):
    """Dry-run model that answers every case correctly (plumbing check)."""

    name = "dry-run-expected"
    model = "expected-answers"

    def __init__(self, cases: list[Case]) -> None:
        self._by_input = {case.input: case for case in cases}

    def complete(self, messages, *, schema=None, max_output_tokens=400, temperature=0.2,
                 prompt_version="v0", request_id="") -> ChatResult:
        case = self._by_input[messages[-1].content.split("Invoer: ", 1)[1].split("\nZet in", 1)[0]]
        if case.scoring == "exact":
            answer = case.expected["answer"]
        elif case.scoring == "any_of":
            answer = case.expected["any_of"][0]
        elif case.scoring == "contains_all":
            answer = " ".join(case.expected["contains_all"])
        else:
            answer = json.dumps(case.expected["fields"], ensure_ascii=False)
        parsed = BenchmarkAnswer(answer=answer)
        return ChatResult(text=parsed.model_dump_json(), parsed=parsed, provider=self.name, model=self.model,
                          prompt_version=prompt_version, input_tokens=1, output_tokens=1, latency_ms=0, attempts=1)


class WrongAnswerModel(ChatModel):
    """Dry-run model that answers every case wrongly (plumbing check)."""

    name = "dry-run-wrong"
    model = "wrong-answers"

    def complete(self, messages, *, schema=None, max_output_tokens=400, temperature=0.2,
                 prompt_version="v0", request_id="") -> ChatResult:
        parsed = BenchmarkAnswer(answer="dit is geen juist antwoord")
        return ChatResult(text=parsed.model_dump_json(), parsed=parsed, provider=self.name, model=self.model,
                          prompt_version=prompt_version, input_tokens=1, output_tokens=1, latency_ms=0, attempts=1)


def build_model(provider: str, tier: str, cases: list[Case]) -> ChatModel:
    if provider == "expected":
        return ExpectedAnswerModel(cases)
    if provider == "wrong":
        return WrongAnswerModel()
    from dlp.config import Settings
    from dlp.providers.registry import build_chat

    settings = Settings(chat_provider=provider)  # type: ignore[arg-type]
    return build_chat(settings, tier)


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def run(model: ChatModel, cases: list[Case], *, limit: int | None = None) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases[:limit]:
        started = time.monotonic()
        try:
            result = model.complete(build_messages(case), schema=BenchmarkAnswer, max_output_tokens=200,
                                    temperature=0.0, prompt_version=PROMPT_VERSION, request_id=f"bench-{case.id}")
            answer = result.parsed.answer if isinstance(result.parsed, BenchmarkAnswer) else result.text
            results.append(CaseResult(case.id, case.category, score(case, answer), answer, case.expected,
                                      result.latency_ms, result.input_tokens, result.output_tokens, result.attempts))
        except ProviderError as exc:
            results.append(CaseResult(case.id, case.category, False, "", case.expected,
                                      int((time.monotonic() - started) * 1000), 0, 0, 0, error=str(exc)))
    return results


def summarise(results: list[CaseResult]) -> dict[str, Any]:
    by_category: dict[str, dict[str, int]] = {}
    for item in results:
        bucket = by_category.setdefault(item.category, {"passed": 0, "total": 0})
        bucket["total"] += 1
        bucket["passed"] += int(item.passed)
    passed = sum(1 for r in results if r.passed)
    return {
        "passed": passed,
        "total": len(results),
        "score": round(passed / len(results), 4) if results else 0.0,
        "by_category": by_category,
        "errors": sum(1 for r in results if r.error),
        "total_tokens": sum(r.input_tokens + r.output_tokens for r in results),
        "mean_latency_ms": int(sum(r.latency_ms for r in results) / len(results)) if results else 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", default="expected", choices=["expected", "wrong", "fixture", "local", "azure"])
    parser.add_argument("--tier", default="small", choices=["small", "strong"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    cases = load_cases()
    model = build_model(args.provider, args.tier, cases)
    results = run(model, cases, limit=args.limit)
    summary = summarise(results)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "kind": "plumbing-dry-run" if args.provider in ("expected", "wrong") else "model-run",
        "provider": model.name,
        "model": model.model,
        "tier": args.tier,
        "prompt_version": PROMPT_VERSION,
        "git_commit": git_commit(),
        "timestamp": stamp,
        "note": "dry runs prove the scoring plumbing only and are not a model selection",
        "summary": summary,
        "results": [asdict(r) for r in results],
    }
    out = args.out or RESULTS_DIR / f"{stamp}-{model.name}-{re.sub(r'[^A-Za-z0-9._-]', '_', model.model)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"provider={model.name} model={model.model} prompt={PROMPT_VERSION} kind={report['kind']}")
    for category, bucket in sorted(summary["by_category"].items()):
        print(f"  {category:20s} {bucket['passed']:3d}/{bucket['total']}")
    print(f"  {'TOTAL':20s} {summary['passed']:3d}/{summary['total']}  score={summary['score']:.2%}  "
          f"errors={summary['errors']}  tokens={summary['total_tokens']}")
    print(f"written {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
