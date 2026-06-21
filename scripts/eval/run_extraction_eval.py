import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.eval.extraction_eval import EvalConfig, run_eval  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run extraction accuracy fixtures.")
    parser.add_argument("--fixtures", type=Path, default=Path("scripts/eval/extraction_fixtures.json"))
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--model", default="llama3.2:latest")
    parser.add_argument("--num-ctx", type=int, default=2048)
    parser.add_argument("--num-gpu", type=int, default=0)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    report = run_eval(
        EvalConfig(
            fixtures_path=ROOT / args.fixtures,
            runs=args.runs,
            model=args.model,
            num_ctx=args.num_ctx,
            num_gpu=args.num_gpu,
            markdown_path=ROOT / args.markdown if args.markdown else None,
        )
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
