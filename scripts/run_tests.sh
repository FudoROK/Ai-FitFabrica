#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setup_test_env.sh
source "${SCRIPT_DIR}/setup_test_env.sh"

pytest -q "$@"
