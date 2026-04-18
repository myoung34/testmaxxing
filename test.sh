#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=src
TARGET_COVERAGE=75

# 1) Generate gibberish tests targeting this repo's Python functions
for fn in \
  testmaxxing.generator.split_function_path \
  testmaxxing.generator.split_go_function_path \
  testmaxxing.generator.split_java_function_path \
  testmaxxing.generator.split_javascript_function_path \
  testmaxxing.generator.default_output_path \
  testmaxxing.generator._infer_go_package_name \
  testmaxxing.generator.build_python_test_file \
  testmaxxing.generator.build_go_test_file \
  testmaxxing.generator.build_java_test_file \
  testmaxxing.generator.build_javascript_test_file \
  testmaxxing.generator.write_test_file \
  testmaxxing.generator.build_test_file \
  testmaxxing.gibberish._pick \
  testmaxxing.gibberish._safe_identifier \
  testmaxxing.gibberish._camelize \
  testmaxxing.gibberish.random_arg \
  testmaxxing.gibberish.test_name \
  testmaxxing.gibberish.test_comment \
  testmaxxing.config.GenerationConfig \
  testmaxxing.cli._coverage_target_from_function_path \
  testmaxxing.cli.main
do
  ./venv/bin/python -m testmaxxing \
    --lang python \
    --function "$fn" \
    --tests 30 \
    --sanity 30 \
    --seed 7 \
    --output "./tests/test_${fn//./_}_gibberish.py"
done

# 2) Run coverage against local src/
./venv/bin/python -m pytest -q \
  --cov=src/testmaxxing \
  --cov-report=term-missing \
  --cov-fail-under="${TARGET_COVERAGE}"
