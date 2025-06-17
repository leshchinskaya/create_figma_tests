#!/bin/bash
echo ">> Generating prompt for component tests..."
python3 create_final_tests/prompt_generator.py \
    --config create_final_tests/config_artifacts_component.json \
    --output create_final_tests/artifacts/prompt_component.txt
