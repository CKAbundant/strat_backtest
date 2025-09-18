#!/bin/bash
set -e
file_path=$(jq -r '.tool_input.file_path' 2>/dev/null || exit 1)

# Only process Python files
if [[ "$file_path" == *.py ]]; then
    cd "$CLAUDE_PROJECT_DIR"
    uv run black --line-length 88 "$file_path"
    uv run isort --profile black "$file_path"
fi