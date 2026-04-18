import argparse

from testmaxxing.config import GenerationConfig
from testmaxxing.generator import write_test_file


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="testmaxxing",
        description="Generate only passing gibberish tests for a given function path.",
    )
    parser.add_argument(
        "--function",
        required=True,
        help=(
            "Target function path. Python: module.function/module:function. "
            "Go: package.Function/package:Function. "
            "Java: package.Class.method or package.Class:method. "
            "JavaScript: module.function or module:function."
        ),
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="python",
        choices=["python", "go", "java", "javascript", "js"],
        help="Generator language target (default: python).",
    )
    parser.add_argument(
        "--tests",
        type=int,
        default=25,
        help="Number of gibberish tests to generate (default: 25).",
    )
    parser.add_argument(
        "--sanity",
        type=int,
        default=30,
        choices=range(0, 101),
        metavar="0-100",
        help="100 = corporate cringe, 0 = full chaos (default: 30).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output file path (default: inferred from --function).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible gibberish.",
    )

    args = parser.parse_args()
    config = GenerationConfig(
        function_path=args.function,
        lang=args.lang,
        tests=args.tests,
        sanity=args.sanity / 100.0,
        output=args.output,
        seed=args.seed,
    )

    out = write_test_file(config)
    print(f"Generated {config.tests} always-passing gibberish tests.")
    print(f"Lang: {config.lang}")
    print(f"Target: {config.function_path}")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
