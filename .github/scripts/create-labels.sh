#!/usr/bin/env bash
# Creates/updates the repo's labels from .github/labels.yml using the GitHub CLI.
# Requires: gh (authenticated), yq (https://github.com/mikefarah/yq).
set -euo pipefail

REPO="${1:-karastoyanov/InstanceMate}"
LABELS_FILE="$(dirname "$0")/../labels.yml"

if ! command -v yq >/dev/null 2>&1; then
  echo "yq is required (https://github.com/mikefarah/yq). Install it or apply labels.yml manually with 'gh label create'." >&2
  exit 1
fi

count=$(yq '. | length' "$LABELS_FILE")
for i in $(seq 0 $((count - 1))); do
  name=$(yq -r ".[$i].name" "$LABELS_FILE")
  color=$(yq -r ".[$i].color" "$LABELS_FILE")
  description=$(yq -r ".[$i].description" "$LABELS_FILE")

  if gh label list --repo "$REPO" --json name --jq '.[].name' | grep -qxF "$name"; then
    gh label edit "$name" --repo "$REPO" --color "$color" --description "$description"
  else
    gh label create "$name" --repo "$REPO" --color "$color" --description "$description"
  fi
done
