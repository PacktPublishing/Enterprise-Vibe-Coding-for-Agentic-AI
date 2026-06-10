#!/usr/bin/env bash

set -euo pipefail

EXPECTED_AGENT="release-captain"
EXPECTED_AGENT_FILE=".github/agents/release-captain.agent.md"

PAYLOAD=""
if [ ! -t 0 ]; then
  PAYLOAD=$(cat || true)
fi

if [ -n "$PAYLOAD" ] && command -v jq >/dev/null 2>&1; then
  AGENT_NAME=$(printf '%s' "$PAYLOAD" | jq -r '.agent.name // .agentName // empty')
  AGENT_FILE=$(printf '%s' "$PAYLOAD" | jq -r '.agent.file // .agentFile // empty')

  if [ -n "$AGENT_NAME" ] && [ "$AGENT_NAME" != "$EXPECTED_AGENT" ]; then
    echo "↩︎  secrets-scanner: agent '$AGENT_NAME' is not '$EXPECTED_AGENT' — skipping."
    exit 0
  fi
  if [ -n "$AGENT_FILE" ] && [[ "$AGENT_FILE" != *"$EXPECTED_AGENT_FILE" ]]; then
    echo "↩︎  secrets-scanner: agent file '$AGENT_FILE' is out of scope — skipping."
    exit 0
  fi
fi

echo "🔎 Running release secret scan (agent: $EXPECTED_AGENT)..."

FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$FILES" ]; then
  echo "No changed files detected."
  exit 0
fi

# Run Gitleaks against changed files
echo "$FILES" | while read -r file; do
  if [ -f "$file" ]; then
    echo "Scanning $file"
    gitleaks detect \
      --no-git \
      --source "$file" \
      --redact \
      --verbose
  fi
done

echo "✅ Secret scan completed successfully."