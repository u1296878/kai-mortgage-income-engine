import argparse
from pathlib import Path

from eval.extraction.harness import DEFAULT_LABELS, EvalConfig, run_eval


def main() -> int:
    parser = argparse.ArgumentParser(description="Run extraction accuracy and variance evals.")
    parser.add_argument("--provider", choices=("anthropic", "ollama"), required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--model")
    parser.add_argument("--num-ctx", type=int, default=2048)
    parser.add_argument("--num-gpu", type=int, default=0)
    parser.add_argument("--results-dir", type=Path, default=Path("eval/extraction/results"))
    parser.add_argument("--tolerance", type=float, default=1.0)
    args = parser.parse_args()
    report, _result = run_eval(
        EvalConfig(
            provider=args.provider,
            runs=args.runs,
            labels_path=args.labels,
            model=args.model,
            num_ctx=args.num_ctx,
            num_gpu=args.num_gpu,
            results_dir=args.results_dir,
            tolerance=args.tolerance,
        )
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
