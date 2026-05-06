from __future__ import annotations

import argparse
import sys

from architecture_rules import format_report, run_architecture_checks, to_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run architecture hardening checks.")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args()

    violations = run_architecture_checks()
    if args.json:
        print(to_json(violations))
    else:
        print(format_report(violations))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
