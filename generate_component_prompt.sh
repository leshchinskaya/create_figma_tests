#!/bin/bash
echo ">> Generating prompt for component tests..."
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m create_final_tests.prompt_generator \
    --config "$ROOT_DIR/create_final_tests/config_artifacts_component.json" \
    --output "$ROOT_DIR/create_final_tests/artifacts/prompt_component.txt" \
    --json "$ROOT_DIR/create_final_tests/artifacts/component_tests.json"
