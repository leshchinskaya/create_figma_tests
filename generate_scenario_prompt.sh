#!/bin/bash
echo ">> Generating prompt for scenario tests..."
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m create_final_tests.prompt_generator \
    --config "$ROOT_DIR/create_final_tests/config_artifacts_scenario.json" \
    --output "$ROOT_DIR/create_final_tests/artifacts/prompt_scenario.txt" \
    --json "$ROOT_DIR/create_final_tests/artifacts/final_tests.json"
