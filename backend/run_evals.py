#!/usr/bin/env python3
"""
CLI Runner for Resume & CV Evaluation Framework.
Runs benchmarks across all or selected test cases, checks gates, and reports scores.

Usage:
  python backend/run_evals.py
  python backend/run_evals.py --format markdown
  python backend/run_evals.py --format json
  python backend/run_evals.py --case case_senior_frontend_architect
  python backend/run_evals.py --save-report
"""

import argparse
import asyncio
import json
import os
import sys

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.evals import BENCHMARK_DATASET, evaluator
from backend.app.models.resume import LLMConfig


async def main():
    parser = argparse.ArgumentParser(
        description="Run comprehensive evaluation suite with zero-hallucination and ATS checkpoints."
    )
    parser.add_argument(
        "--format",
        choices=["terminal", "markdown", "json"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Specific test case ID to execute (default: all)",
    )
    parser.add_argument(
        "--provider",
        choices=["heuristic", "ollama", "openai", "auto"],
        default="heuristic",
        help="LLM provider to evaluate (default: heuristic)",
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save report to backend/data/latest_eval_report.json and .md",
    )
    args = parser.parse_args()

    cases = BENCHMARK_DATASET
    if args.case:
        cases = [c for c in BENCHMARK_DATASET if c.id == args.case]
        if not cases:
            print(f"Error: Case ID '{args.case}' not found. Available cases:")
            for c in BENCHMARK_DATASET:
                print(f"  - {c.id} ({c.name})")
            sys.exit(1)

    config = LLMConfig(provider=args.provider)
    print(f"Starting evaluation suite across {len(cases)} case(s) using provider '{args.provider}'...\n")

    report = await evaluator.evaluate_suite(cases=cases, config=config)

    if args.format == "terminal":
        print(evaluator.format_terminal(report))
    elif args.format == "markdown":
        print(evaluator.format_markdown(report))
    elif args.format == "json":
        print(json.dumps(report.model_dump(), indent=2))

    if args.save_report:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
        os.makedirs(data_dir, exist_ok=True)
        json_path = os.path.join(data_dir, "latest_eval_report.json")
        md_path = os.path.join(data_dir, "latest_eval_report.md")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(evaluator.format_markdown(report))

        print(f"\n[Saved Reports]\n• JSON: {json_path}\n• Markdown: {md_path}")

    # Exit code: 0 if all passed, 1 if any failed
    sys.exit(0 if report.failed_cases == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
