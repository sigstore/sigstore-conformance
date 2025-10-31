# Generate an html summary from client conformance reports

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class Result:
    name: str
    total: int
    passed: int
    failed: int
    xfailed: int
    skipped: int
    rekor2_verify: bool = False
    rekor2_sign: bool = False

    def __init__(self, report_path: str):
        with open(report_path) as f:
            data = json.load(f)

        client_name = os.path.basename(report_path).replace('.json', '')
        summary = data.get('summary', {})
        self.name=client_name
        self.total=summary.get('total', 0)
        self.passed=summary.get('passed', 0)
        self.failed=summary.get('failed', 0)
        self.xfailed=summary.get('xfailed', 0)
        self.skipped=summary.get('skipped', 0)

        # look at some especially interesting specific tests
        tests = data.get("tests", [])
        for test in tests:
            nodeid = test.get("nodeid")
            if nodeid == "test/test_bundle.py::test_verify[PATH-rekor2-happy-path]":
                self.rekor2_verify = test.get("outcome") == "passed"
            elif nodeid == "test/test_bundle.py::test_sign_verify_rekor2":
                self.rekor2_sign = test.get("outcome") == "passed"


def generate_html(reports_dir: Path, output_file: Path):
    results: list[Result] = []
    for report_path in reports_dir.glob("**/*.json"):
        results.append(Result(report_path))
    results.sort(key=lambda result: result.name)

    # Start HTML generation
    html = f"""
    <html>
    <head>
        <title>Sigstore Client Conformance Results</title>
        <style>
            body {{ font-family: sans-serif; margin: 2em; }}
            table {{ border-collapse: collapse; }}
            th, td {{ border: 1px solid #ccc; padding: 8px 12px; }}
            th {{ background-color: #f4f4f4; }}
            .failed {{ background-color: #ffe0e0; }}
            .passed {{ background-color: #e0ffe0; }}
        </style>
    </head>
    <body>
        <h1>Sigstore Client Conformance Results</h1>
        <p>Last updated: {datetime.now(UTC).isoformat(timespec="minutes")}Z</p>
        <table>
            <thead>
                <tr>
                    <th>Client</th>
                    <th>Pass Rate</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Skipped</th>
                    <th>Xfailed</th>
                    <th>Rekor v2 verify</th>
                    <th>Rekor v2 sign</th>
                </tr>
            </thead>
            <tbody>
    """
    for res in results:
        status_class = 'passed' if res.failed == 0 else 'failed'
        html += f"""
                <tr class="{status_class}">
                    <td><strong>{res.name}</strong></td>
                    <td>{100 * res.passed / res.total:.2f}%</td>
                    <td>{res.passed}</td>
                    <td>{res.failed}</td>
                    <td>{res.skipped}</td>
                    <td>{res.xfailed}</td>
                    <td>{"✅" if res.rekor2_verify else "❌"}</td>
                    <td>{"✅" if res.rekor2_sign else "❌"}</td>
                </tr>
        """
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w') as f:
        f.write(html)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    generate_html(Path(args.reports_dir), Path(args.output))
