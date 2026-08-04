"""
CI 执行入口 — 唯一测试运行方式。

  python run_ci.py                    # 全量单 session，带层级标签
  python run_ci.py --layer smoke      # L0（GitHub Actions PR）
  python run_ci.py --layer critical   # L1（GitHub Actions 定时）
  python run_ci.py --layer regression # L2（GitHub Actions 手动）
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

REPORT_DIR = Path("tests/reports")
REPORT_DIR.mkdir(exist_ok=True)

PYTEST = f'"{sys.executable}" -m pytest tests/ -v --tb=line -p no:xdist'

ALL_MARKERS = "smoke or critical or security or regression or payment or a11y or migration or concurrency or ai or performance"

LAYERS = {
    "smoke":      ("L0-Smoke",      "smoke"),
    "critical":   ("L1-Critical",   "smoke or critical or security"),
    "regression": ("L2-Regression",  ALL_MARKERS),
}


def _parse_pytest_output(text: str) -> dict:
    m = re.search(r"(\d+) passed.*?(\d+) failed.*?(\d+) skipped", text)
    if m:
        return {"passed": int(m[1]), "failed": int(m[2]), "skipped": int(m[3])}
    return {"passed": 0, "failed": 0, "skipped": 0}


def run_single_layer(name: str, display: str, markers: str):
    """单层：pytest → ci_layer_{name}.json → HtmlReport.from_layer_files() → HTML。"""
    print(f"\n{'='*60}\n  {display}\n  Markers: {markers}\n{'='*60}")

    log = REPORT_DIR / f"pytest_{name}.log"
    start = time.time()
    with open(log, "w") as f:
        subprocess.run(
            f'{PYTEST} -m "{markers}"',
            shell=True, stdout=f, stderr=subprocess.STDOUT, timeout=7200,
            env={**__import__('os').environ, "QUOTR_CI_LAYER": name},
        )
    duration = time.time() - start
    stats = _parse_pytest_output(log.read_text())

    from tests.utils.html_reporter import HtmlReport
    merged = HtmlReport.from_layer_files()
    path = merged.generate() if merged.total > 0 else None

    print(f"  {stats['passed']} passed, {stats['failed']} failed, {stats['skipped']} skipped ({duration:.0f}s)")
    if path:
        print(f"  Report: {path}")
    return {**stats, "total": sum(stats.values()), "duration": duration, "report": str(path) if path else ""}


def run_full():
    """全量单 session。一次 pytest → pytest_terminal_summary 直接生成 HTML。"""
    print(f"\n{'='*60}\n  Full Suite (single session, no expiry)\n{'='*60}")

    log = REPORT_DIR / "pytest_full.log"
    start = time.time()
    with open(log, "w") as f:
        subprocess.run(
            f'{PYTEST} -m "{ALL_MARKERS}"',
            shell=True, stdout=f, stderr=subprocess.STDOUT, timeout=7200,
        )
    duration = time.time() - start
    stats = _parse_pytest_output(log.read_text())

    print(f"  {stats['passed']} passed, {stats['failed']} failed, {stats['skipped']} skipped ({duration:.0f}s)")
    print(f"  Report: tests/reports/latest.html")
    return {**stats, "total": sum(stats.values()), "duration": duration}


def main():
    parser = argparse.ArgumentParser(description="Quotr CI Runner")
    parser.add_argument("--layer", choices=["smoke", "critical", "regression"])
    args = parser.parse_args()

    if args.layer:
        display, markers = LAYERS[args.layer]
        r = run_single_layer(args.layer, display, markers)
    else:
        r = run_full()

    sys.exit(1 if r.get("failed", 0) > 0 else 0)


if __name__ == "__main__":
    main()
