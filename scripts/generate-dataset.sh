#!/usr/bin/env bash
# Canonical dataset-quality generation launcher.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${ROOT}/scripts/generate-pilot.sh" "$@"
