# 🛡️ vigil-action

> GitHub Action for [Vigil](https://github.com/schmidtpeterdaniel/vigil) — Open source license compliance, automated.

Scan your Python dependencies for license conflicts, policy violations, and compliance issues — directly in your CI pipeline.

---

## Quick Start

Add this to any workflow file (e.g. `.github/workflows/compliance.yml`):

```yaml
name: License Compliance

on: [push, pull_request]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Vigil license scan
        uses: schmidtpeterdaniel/vigil-action@v1
```

That's it. Vigil will scan your environment and fail the job if any license violations are found.

---

## With a Policy File

Create a `vigil.yaml` in your repo root to define which licenses are allowed or blocked:

```yaml
# vigil.yaml
policy:
  allow:
    - MIT
    - Apache-2.0
    - BSD-2-Clause
    - BSD-3-Clause
    - ISC

  block:
    - GPL-2.0
    - GPL-3.0
    - AGPL-3.0
    - SSPL-1.0

  warn:
    - LGPL-2.1
    - LGPL-3.0
```

Then reference it in your workflow:

```yaml
      - name: Run Vigil license scan
        uses: schmidtpeterdaniel/vigil-action@v1
        with:
          policy-file: vigil.yaml
```

---

## Generate an HTML Report

```yaml
      - name: Run Vigil license scan
        uses: schmidtpeterdaniel/vigil-action@v1
        with:
          policy-file: vigil.yaml
          format: html
          output-file: compliance-report.html
          upload-report: true   # Uploads as a workflow artifact
```

The HTML report is uploaded as a downloadable artifact on every run.

---

## Full Example — Real-world Setup

```yaml
name: License Compliance

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 9 * * 1'   # Every Monday morning — catches upstream license changes

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install project dependencies
        run: pip install -r requirements.txt

      - name: Run Vigil
        uses: schmidtpeterdaniel/vigil-action@v1
        with:
          policy-file: vigil.yaml
          requirements-file: requirements.txt
          format: html
          output-file: vigil-report.html
          upload-report: true
          fail-on-warning: false
```

---

## Inputs

| Input | Description | Default |
|---|---|---|
| `policy-file` | Path to `vigil.yaml` policy file | `vigil.yaml` |
| `requirements-file` | Path to `requirements.txt`. If omitted, scans full environment | `` |
| `format` | Output format: `terminal`, `json`, `html` | `terminal` |
| `output-file` | Path for report file (used with `html` or `json`) | `vigil-report.html` |
| `fail-on-warning` | Fail the job on warnings too | `false` |
| `upload-report` | Upload HTML report as workflow artifact | `true` |
| `python-version` | Python version to use | `3.11` |
| `vigil-version` | Version of `vigil-cli` to install | `latest` |

---

## Outputs

| Output | Description |
|---|---|
| `has-errors` | `true` if license errors were found |
| `has-warnings` | `true` if license warnings were found |
| `report-path` | Path to the generated report file |
| `total-dependencies` | Number of dependencies scanned |

Use outputs in subsequent steps:

```yaml
      - name: Run Vigil
        id: vigil
        uses: schmidtpeterdaniel/vigil-action@v1

      - name: Comment on PR
        if: steps.vigil.outputs.has-warnings == 'true'
        run: echo "License warnings found — please review the compliance report."
```

---

## Job Summary

Vigil automatically writes a rich Markdown summary to the GitHub Actions job summary page, including a table of all conflicts and a full license breakdown.

---

## License

Apache-2.0 © Schmidt Peter Daniel
