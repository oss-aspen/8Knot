#!/usr/bin/env python3
"""
Security report parsing utility for GitHub Actions workflows.
Parses Bandit and pip-audit JSON reports and extracts relevant metrics.
"""
import json
import sys
from pathlib import Path


def parse_bandit(report_path):
    """
    Parse Bandit security report and count issues by severity.

    Args:
        report_path: Path to bandit-report.json

    Returns:
        dict: Counts of HIGH, MEDIUM, and LOW severity issues
    """
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


def parse_pip_audit(report_path):
    """
    Parse pip-audit vulnerability report and count vulnerable dependencies.

    Args:
        report_path: Path to pip-audit-report.json

    Returns:
        int: Number of vulnerable dependencies
    """
    try:
        with open(report_path) as f:
            data = json.load(f)
        # pip-audit uses 'dependencies' field for vulnerable packages
        return len(data.get("dependencies", []))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error parsing pip-audit report: {e}", file=sys.stderr)
        return 0


def main():
    if len(sys.argv) < 3:
        print("Usage: parse-security-reports.py <bandit|pip-audit> <report-path>", file=sys.stderr)
        sys.exit(1)

    report_type = sys.argv[1]
    report_path = sys.argv[2]

    if not Path(report_path).exists():
        print(f"Error: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    if report_type == "bandit":
        result = parse_bandit(report_path)
        # Output as simple key=value for easy parsing in bash
        print(f"HIGH={result['HIGH']}")
        print(f"MEDIUM={result['MEDIUM']}")
        print(f"LOW={result['LOW']}")
    elif report_type == "pip-audit":
        result = parse_pip_audit(report_path)
        print(f"VULNS={result}")
    else:
        print(f"Error: Unknown report type '{report_type}'", file=sys.stderr)
        print("Supported types: bandit, pip-audit", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
