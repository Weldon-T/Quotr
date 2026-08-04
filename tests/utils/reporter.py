"""测试报告工具。

基于测试结果生成结构化报告，用于 Slack 同步和 Release Readiness。
"""
import json
import time
from pathlib import Path
from datetime import datetime


class TestReporter:
    """收集测试结果并输出报告。"""

    def __init__(self):
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "flaky": 0,
            "duration_ms": 0,
            "started_at": None,
            "modules": {},
        }
        self._start = None

    def start(self):
        self._start = time.time()
        self.results["started_at"] = datetime.now().isoformat()

    def record(self, module: str, passed: int = 0, failed: int = 0, skipped: int = 0):
        self.results["modules"][module] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        }
        self.results["total"] += passed + failed + skipped
        self.results["passed"] += passed
        self.results["failed"] += failed
        self.results["skipped"] += skipped

    @property
    def pass_rate(self) -> float:
        total = self.results["total"]
        if total == 0:
            return 100.0
        return (self.results["passed"] / total) * 100

    def summary(self) -> str:
        duration = time.time() - self._start if self._start else 0
        lines = [
            "=" * 50,
            f"Test Report — {self.results['started_at']}",
            f"Duration: {duration:.1f}s",
            f"Total: {self.results['total']} | "
            f"Passed: {self.results['passed']} | "
            f"Failed: {self.results['failed']} | "
            f"Skipped: {self.results['skipped']}",
            f"Pass Rate: {self.pass_rate:.1f}%",
        ]
        for mod, stats in self.results["modules"].items():
            lines.append(f"  {mod}: {stats['passed']}/{stats['passed'] + stats['failed'] + stats['skipped']}")
        lines.append("=" * 50)
        return "\n".join(lines)

    def to_json(self, path: str = None) -> str:
        data = {**self.results, "pass_rate": self.pass_rate}
        json_str = json.dumps(data, indent=2)
        if path:
            Path(path).write_text(json_str)
        return json_str
