#!/bin/bash
echo ">> Generating prompt for scenario tests..."
python3 create_final_tests/prompt_generator.py \
    --config create_final_tests/config_artifacts_scenario.json \
    --output create_final_tests/artifacts/prompt_scenario.txt
