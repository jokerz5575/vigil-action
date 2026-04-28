#!/usr/bin/env python3
"""
Vigil GitHub Action runner.
Executes the license scan and writes outputs to the GitHub Actions environment.
"""
from __future__ import annotations

import argparse
import os
import sys
import json
from pathlib import Path


def set_output(name: str, value: str) -> None:
    """Write a GitHub Actions output variable."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{name}={value}\n")
    else:
        # Fallback for local testing
        print(f"::set-output name={name}::{value}")


def set_summary(content: str) -> None:
    """Write to the GitHub Actions job summary."""
    github_step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_step_summary:
        with open(github_step_summary, "a") as f:
            f.write(content + "\n")


def annotate_error(message: str, title: str = "Vigil License Error") -> None:
    print(f"::error title={title}::{message}")


def annotate_warning(message: str, title: str = "Vigil License Warning") -> None:
    print(f"::warning title={title}::{message}")


def print_group(title: str) -> None:
    print(f"::group::{title}")


def end_group() -> None:
    print("::endgroup::")


def main() -> int:
    parser = argparse.ArgumentParser(description="Vigil GitHub Action runner")
    parser.add_argument("--policy", default="vigil.yaml")
    parser.add_argument("--requirements", default="")
    parser.add_argument("--format", default="terminal")
    parser.add_argument("--output", default="vigil-report.html")
    parser.add_argument("--fail-on-warning", default="false")
    args = parser.parse_args()

    fail_on_warning = args.fail_on_warning.lower() == "true"

    # Import vigil
    try:
        from vigil_licenses.scanner import LicenseScanner, LicensePolicy
        from vigil_licenses.reporter import generate_report, ReportFormat
    except ImportError:
        print("::error::vigil-cli is not installed. Please check your workflow configuration.")
        return 1

    # Load policy if file exists
    policy = None
    if args.policy and Path(args.policy).exists():
        print(f"📋 Loading policy from {args.policy}")
        policy = LicensePolicy.from_yaml(args.policy)
    else:
        if args.policy and args.policy != "vigil.yaml":
            print(f"::warning::Policy file '{args.policy}' not found. Running without policy.")
        print("ℹ️  No policy file found — running with default settings.")

    scanner = LicenseScanner(policy=policy)

    # Resolve requirements path
    req_file = args.requirements if args.requirements and Path(args.requirements).exists() else None

    print_group("🛡️ Vigil License Compliance Scan")
    print(f"Scanning {'requirements file: ' + req_file if req_file else 'installed environment'}...")

    report = scanner.scan(
        requirements_file=req_file,
        project_name=os.environ.get("GITHUB_REPOSITORY", "").split("/")[-1] or None,
    )

    # Always render terminal output inside the group
    generate_report(report, fmt=ReportFormat.TERMINAL)
    end_group()

    # Write HTML/JSON report if requested
    fmt_map = {"html": ReportFormat.HTML, "json": ReportFormat.JSON}
    if args.format in fmt_map:
        generate_report(report, fmt=fmt_map[args.format], output_path=args.output)
        print(f"📄 Report written to {args.output}")

    # GitHub Actions annotations for each conflict
    for conflict in report.conflicts:
        msg = f"{conflict.package} ({conflict.license_spdx}): {conflict.reason}"
        if conflict.recommendation:
            msg += f" → {conflict.recommendation}"

        from vigil_core.models import ConflictSeverity
        if conflict.severity == ConflictSeverity.ERROR:
            annotate_error(msg)
        else:
            annotate_warning(msg)

    # Write job summary
    _write_job_summary(report)

    # Set action outputs
    set_output("has_errors", str(report.has_errors).lower())
    set_output("has_warnings", str(report.has_warnings).lower())
    set_output("report_path", args.output if args.format in fmt_map else "")
    set_output("total_dependencies", str(report.total_dependencies))

    # Determine exit code
    if report.has_errors:
        print("\n❌ Compliance check FAILED — license errors must be resolved.")
        return 1

    if fail_on_warning and report.has_warnings:
        print("\n⚠️  Compliance check FAILED — warnings found and --fail-on-warning is set.")
        return 1

    print("\n✅ Compliance check passed.")
    return 0


def _write_job_summary(report) -> None:
    """Write a rich Markdown summary to the GitHub Actions job summary."""
    from vigil_core.models import ConflictSeverity

    lines = ["## 🛡️ Vigil Compliance Report\n"]

    # Stats row
    error_count = sum(1 for c in report.conflicts if c.severity == ConflictSeverity.ERROR)
    warn_count  = sum(1 for c in report.conflicts if c.severity == ConflictSeverity.WARNING)

    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Dependencies scanned | {report.total_dependencies} |")
    lines.append(f"| Unique licenses | {len(report.license_summary)} |")
    lines.append(f"| Errors | {'🔴 ' if error_count else ''}{error_count} |")
    lines.append(f"| Warnings | {'🟡 ' if warn_count else ''}{warn_count} |")
    lines.append("")

    # Conflicts table
    if report.conflicts:
        lines.append("### Issues Found\n")
        lines.append("| Severity | Package | License | Reason |")
        lines.append("|---|---|---|---|")
        for c in report.conflicts:
            icon = "🔴" if c.severity == ConflictSeverity.ERROR else "🟡"
            lines.append(f"| {icon} {c.severity.value.upper()} | `{c.package}` | `{c.license_spdx}` | {c.reason} |")
        lines.append("")
    else:
        lines.append("### ✅ No license issues detected.\n")

    # License breakdown
    if report.license_summary:
        lines.append("<details><summary>License Breakdown</summary>\n")
        lines.append("| License | Packages |")
        lines.append("|---|---|")
        for spdx, count in sorted(report.license_summary.items(), key=lambda x: -x[1]):
            lines.append(f"| `{spdx}` | {count} |")
        lines.append("\n</details>")

    lines.append("\n---")
    lines.append("*Generated by [Vigil](https://github.com/schmidtpeterdaniel/vigil) — Open source compliance, automated.*")

    set_summary("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
