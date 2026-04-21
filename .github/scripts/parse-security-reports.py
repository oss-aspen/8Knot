#!/usr/bin/env python3
"""Parse Bandit JSON reports and output severity counts for use in bash workflows."""
import json
import sys
from pathlib import Path


def parse_bandit(report_path):
    try:
        with open(report_path) as f:
            data = json.load(f)
        results = data.get("results", [])
        return {
            "HIGH": len([r for r in results if r.get("issue_severity") == "HIGH"]),
            "MEDIUM": len([r for r in results if r.get("issue_severity") == "MEDIUM"]),
            "LOW": len([r for r in results if r.get("issue_severity") == "LOW"]),
        }
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error parsing Bandit report: {e}", file=sys.stderr)
        return {"HIGH": 0, "MEDIUM": 0, "LOW": 0}


def main():
    if len(sys.argv) < 2:
        print("Usage: parse-security-reports.py <report-path>", file=sys.stderr)
        sys.exit(1)

    report_path = sys.argv[1]

    if not Path(report_path).exists():
        print(f"Error: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    result = parse_bandit(report_path)
    print(f"HIGH={result['HIGH']}")
    print(f"MEDIUM={result['MEDIUM']}")
    print(f"LOW={result['LOW']}")


if __name__ == "__main__":
    main()
