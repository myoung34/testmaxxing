import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from testmaxxing.config import GenerationConfig
from testmaxxing.generator import (
    split_function_path,
    split_go_function_path,
    split_java_function_path,
    split_javascript_function_path,
    write_test_file,
)


def _coverage_target_from_function_path(function_path: str, lang: str) -> str:
    if lang == "go":
        try:
            package_path, _ = split_go_function_path(function_path)
            return package_path
        except ValueError:
            return "./..."
    if lang == "java":
        try:
            package_name, _, _ = split_java_function_path(function_path)
            return package_name
        except ValueError:
            return function_path
    if lang == "javascript":
        try:
            module_path, _ = split_javascript_function_path(function_path)
            return module_path
        except ValueError:
            return function_path
    try:
        module_name, _ = split_function_path(function_path)
        return module_name
    except ValueError:
        if ":" in function_path:
            return function_path.split(":", 1)[0]
        if "." in function_path:
            return function_path.rsplit(".", 1)[0]
        return function_path


def _run_command(command: list[str], env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    output = f"{result.stdout}{result.stderr}"
    if result.returncode != 0:
        raise RuntimeError(
            "Coverage run failed while attempting --percentage.\n"
            f"Command: {' '.join(command)}\n"
            f"{output}"
        )
    return output


def _parse_percent(text: str, patterns: list[str]) -> float:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match:
            return float(match.group(1))
    raise RuntimeError("Failed to parse coverage percentage from command output.")


def _run_python_coverage_percent(cov_target: str) -> float:
    fd, cov_json_path = tempfile.mkstemp(prefix="testmaxxing_cov_", suffix=".json")
    os.close(fd)
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", "src")
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        f"--cov={cov_target}",
        f"--cov-report=json:{cov_json_path}",
    ]
    _run_command(command, env=env)

    try:
        data = json.loads(Path(cov_json_path).read_text(encoding="utf-8"))
        return float(data["totals"]["percent_covered"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("Failed to parse coverage JSON output.") from exc
    finally:
        Path(cov_json_path).unlink(missing_ok=True)


def _run_go_coverage_percent(cov_target: str) -> float:
    if shutil.which("go") is None:
        raise RuntimeError("Go coverage requested but 'go' is not available in PATH.")

    fd, cov_profile_path = tempfile.mkstemp(prefix="testmaxxing_go_cov_", suffix=".out")
    os.close(fd)
    try:
        package = cov_target or "./..."
        try:
            _run_command(["go", "test", package, "-coverprofile", cov_profile_path])
        except RuntimeError:
            _run_command(["go", "test", "./...", "-coverprofile", cov_profile_path])

        output = _run_command(["go", "tool", "cover", "-func", cov_profile_path])
        return _parse_percent(output, [r"total:\s+\(statements\)\s+([0-9]+(?:\.[0-9]+)?)%"])
    finally:
        Path(cov_profile_path).unlink(missing_ok=True)


def _run_java_coverage_percent() -> float:
    root = Path.cwd()
    gradlew = root / "gradlew"
    mvnw = root / "mvnw"
    pom_xml = root / "pom.xml"

    if gradlew.exists():
        _run_command([str(gradlew), "test", "jacocoTestReport", "--quiet"])
        candidates = [root / "build/reports/jacoco/test/jacocoTestReport.csv"]
    elif mvnw.exists():
        _run_command([str(mvnw), "-q", "test", "jacoco:report"])
        candidates = [root / "target/site/jacoco/jacoco.csv"]
    elif pom_xml.exists() and shutil.which("mvn") is not None:
        _run_command(["mvn", "-q", "test", "jacoco:report"])
        candidates = [root / "target/site/jacoco/jacoco.csv"]
    else:
        raise RuntimeError(
            "Java coverage requested but no Gradle/Maven setup with JaCoCo was detected."
        )

    for candidate in candidates:
        if not candidate.exists():
            continue
        with candidate.open(encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))
        if not rows:
            continue

        instruction_missed = sum(int(row.get("INSTRUCTION_MISSED", "0")) for row in rows)
        instruction_covered = sum(int(row.get("INSTRUCTION_COVERED", "0")) for row in rows)
        total = instruction_missed + instruction_covered
        if total > 0:
            return (instruction_covered / total) * 100.0

        line_missed = sum(int(row.get("LINE_MISSED", "0")) for row in rows)
        line_covered = sum(int(row.get("LINE_COVERED", "0")) for row in rows)
        line_total = line_missed + line_covered
        if line_total > 0:
            return (line_covered / line_total) * 100.0

    raise RuntimeError("Java coverage command ran, but no parsable JaCoCo CSV report was found.")


def _run_javascript_coverage_percent() -> float:
    root = Path.cwd()
    package_json = root / "package.json"
    if not package_json.exists():
        raise RuntimeError("JavaScript coverage requested but package.json was not found.")

    if (root / "pnpm-lock.yaml").exists() and shutil.which("pnpm") is not None:
        command = ["pnpm", "test", "--", "--coverage"]
    elif (root / "yarn.lock").exists() and shutil.which("yarn") is not None:
        command = ["yarn", "test", "--coverage"]
    elif shutil.which("npm") is not None:
        command = ["npm", "test", "--", "--coverage", "--watchAll=false"]
    else:
        raise RuntimeError(
            "JavaScript coverage requested but none of npm/pnpm/yarn are available in PATH."
        )

    output = _run_command(command)
    return _parse_percent(
        output,
        [
            r"All files[^\n]*\|\s*([0-9]+(?:\.[0-9]+)?)\s*\|",
            r"Statements\s*:\s*([0-9]+(?:\.[0-9]+)?)%",
            r"Lines\s*:\s*([0-9]+(?:\.[0-9]+)?)%",
        ],
    )


def _run_coverage_percent(lang: str, cov_target: str) -> float:
    if lang == "go":
        return _run_go_coverage_percent(cov_target)
    if lang == "java":
        return _run_java_coverage_percent()
    if lang == "javascript":
        return _run_javascript_coverage_percent()
    return _run_python_coverage_percent(cov_target)


def _attempt_target_coverage(base_config: GenerationConfig, target_percentage: int) -> tuple[str, float, int]:
    cov_target = _coverage_target_from_function_path(
        base_config.function_path, base_config.lang
    )
    step = max(1, base_config.tests)
    max_tests = max(step, 500)
    current_tests = step
    last_output = ""
    achieved = 0.0

    while current_tests <= max_tests:
        config = GenerationConfig(
            function_path=base_config.function_path,
            lang=base_config.lang,
            tests=current_tests,
            sanity=base_config.sanity,
            output=base_config.output,
            seed=base_config.seed,
        )
        last_output = write_test_file(config)
        achieved = _run_coverage_percent(config.lang, cov_target)
        if achieved >= target_percentage:
            return last_output, achieved, current_tests
        current_tests += step

    return last_output, achieved, current_tests - step


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
    parser.add_argument(
        "--percentage",
        type=int,
        default=None,
        choices=range(1, 101),
        metavar="1-100",
        help=(
            "Best-effort target coverage percentage. "
            "Regenerates with larger test counts and reruns language coverage until target or max attempts."
        ),
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

    if args.percentage is not None:
        try:
            out, achieved, used_tests = _attempt_target_coverage(config, args.percentage)
        except RuntimeError as exc:
            parser.exit(1, f"{exc}\n")
        print(f"Generated {used_tests} always-passing gibberish tests.")
        print(
            f"Attempted coverage target: {args.percentage}% (achieved {achieved:.1f}%)."
        )
    else:
        out = write_test_file(config)
        print(f"Generated {config.tests} always-passing gibberish tests.")
    print(f"Lang: {config.lang}")
    print(f"Target: {config.function_path}")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
