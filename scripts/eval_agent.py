#!/usr/bin/env python3
"""
Agent Evaluation CLI

Runs the golden dataset (tests/eval/golden_dataset.json by default) against a
live Supervisor and reports task success rate, routing/tool-selection accuracy,
step count, token usage, cost-per-task, and a failure-category breakdown.

Deliberately exercises the real Supervisor + sub-agent stack end-to-end
(no mocks) -- see tests/eval/README.md for the disposable-Qdrant requirement
when running the mutating cases.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path to import artemis
sys.path.insert(0, str(Path(__file__).parent.parent))

from artemis.agent.config import AgentConfig
from artemis.agent.run import get_v2_runtime
from artemis.agent.supervisor import Supervisor
from artemis.eval.dataset import load_dataset
from artemis.eval.metrics import compute_metrics
from artemis.eval.report import print_human_summary, write_json_report
from artemis.eval.runner import run_suite
from artemis.utils import get_logger

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the agent eval golden dataset against a live Supervisor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Safe default: skip the two mutating (real-ingest) cases
  python scripts/eval_agent.py --dataset tests/eval/golden_dataset.json --skip-mutating

  # Full suite including mutating cases -- disposable Qdrant only, see tests/eval/README.md
  python scripts/eval_agent.py --dataset tests/eval/golden_dataset.json

  # Real dollar figures (Groq's default model has no public pricing anymore)
  python scripts/eval_agent.py --dataset tests/eval/golden_dataset.json --provider openai --model gpt-4o-mini
        """,
    )
    parser.add_argument(
        "--dataset",
        default="tests/eval/golden_dataset.json",
        help="Path to the golden dataset JSON file (default: tests/eval/golden_dataset.json).",
    )
    parser.add_argument(
        "--skip-mutating",
        action="store_true",
        help="Skip cases that actually call ingest_file/ingest_directory (safe against any Qdrant).",
    )
    parser.add_argument("--provider", choices=["groq", "openai"], help="LLM provider override.")
    parser.add_argument("--model", help="Model name override.")
    parser.add_argument(
        "--reports-dir",
        default=None,
        help="Directory for the timestamped JSON report (default: eval_reports/).",
    )
    args = parser.parse_args()

    try:
        overrides = {}
        if args.provider:
            overrides["provider"] = args.provider
        if args.model:
            overrides["model_name"] = args.model
        config = AgentConfig.from_env(**overrides)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    cases = load_dataset(args.dataset)
    print(f"Loaded {len(cases)} eval case(s) from {args.dataset}")

    config, registry = get_v2_runtime(config)
    supervisor = Supervisor(config, registry)

    results = run_suite(
        cases,
        supervisor,
        model_name=config.model_name,
        skip_mutating=args.skip_mutating,
    )
    if not results:
        print("No cases were run (empty dataset, or all skipped by --skip-mutating).")
        sys.exit(1)

    metrics = compute_metrics(results)
    print_human_summary(metrics, results)

    reports_dir = Path(args.reports_dir) if args.reports_dir else None
    report_path = write_json_report(metrics, results, reports_dir=reports_dir)
    print(f"Report written to: {report_path}")

    sys.exit(0 if metrics.task_success_rate == 1.0 else 1)


if __name__ == "__main__":
    main()
