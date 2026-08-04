"""Performance: API 延迟基线测试。

每次 RC 自动运行，采集 P50/P95/P99 并与上次基线对比。
"""
import time
import json
import pytest
from pathlib import Path
from dataclasses import dataclass, field
from statistics import mean, median, quantiles
from typing import Optional
from tests.api.client import APIClient

BASELINE_FILE = Path(__file__).parent / "latency_baseline.json"


@dataclass
class LatencySample:
    endpoint: str
    method: str
    durations_ms: list[float] = field(default_factory=list)

    @property
    def p50(self) -> float: return median(self.durations_ms) if self.durations_ms else 0

    @property
    def p95(self) -> float:
        if len(self.durations_ms) < 20:
            return max(self.durations_ms) if self.durations_ms else 0
        return quantiles(self.durations_ms, n=20)[18]

    @property
    def p99(self) -> float:
        if len(self.durations_ms) < 100:
            return max(self.durations_ms) if self.durations_ms else 0
        return quantiles(self.durations_ms, n=100)[98]

    @property
    def avg(self) -> float: return mean(self.durations_ms) if self.durations_ms else 0

    @property
    def error_rate(self) -> float:
        if not self.durations_ms:
            return 0
        errors = sum(1 for d in self.durations_ms if d < 0)  # negative = error flag
        return errors / len(self.durations_ms)


class LatencyCollector:
    """采集 API 响应时间并对比基线。"""

    WARMUP_ROUNDS = 3
    MEASURE_ROUNDS = 20

    def __init__(self, client: APIClient):
        self.client = client
        self.samples: dict[str, LatencySample] = {}

    def measure(self, name: str, method: str, path: str, body: dict = None) -> "LatencyCollector":
        """测量指定端点的响应时间。"""
        sample = LatencySample(endpoint=path, method=method)

        # Warmup
        for _ in range(self.WARMUP_ROUNDS):
            if method == "POST":
                self.client.post(path, body or {})
            else:
                self.client.get(path)

        # Measurement
        for _ in range(self.MEASURE_ROUNDS):
            start = time.perf_counter()
            try:
                if method == "POST":
                    resp = self.client.post(path, body or {})
                else:
                    resp = self.client.get(path)
                elapsed = (time.perf_counter() - start) * 1000
                if resp.status_code == 200:
                    sample.durations_ms.append(elapsed)
                else:
                    sample.durations_ms.append(-1.0)  # flag as error
            except Exception:
                sample.durations_ms.append(-1.0)

        self.samples[name] = sample
        return self

    def load_baseline(self) -> dict:
        if BASELINE_FILE.exists():
            return json.loads(BASELINE_FILE.read_text())
        return {}

    def save_baseline(self):
        data = {}
        for name, s in self.samples.items():
            data[name] = {"p50": s.p50, "p95": s.p95, "p99": s.p99, "avg": s.avg, "n": s.MEASURE_ROUNDS}
        BASELINE_FILE.parent.mkdir(exist_ok=True)
        BASELINE_FILE.write_text(json.dumps(data, indent=2))

    def compare_to_baseline(self) -> list[str]:
        """对比当前结果与基线，返回退化告警列表。"""
        baseline = self.load_baseline()
        alerts = []
        for name, s in self.samples.items():
            if name not in baseline:
                continue
            prev_p95 = baseline[name]["p95"]
            if prev_p95 > 0 and s.p95 > prev_p95 * 1.05:
                change_pct = (s.p95 - prev_p95) / prev_p95 * 100
                alerts.append(f"[SLOWER] {name}: P95 {prev_p95:.0f}ms → {s.p95:.0f}ms (+{change_pct:.1f}%)")
            if s.error_rate > 0.01:
                alerts.append(f"[ERRORS] {name}: error rate {s.error_rate:.1%}")
        return alerts

    def report(self) -> str:
        lines = ["API Latency Report", "-" * 40]
        for name, s in self.samples.items():
            lines.append(
                f"  {name}: P50={s.p50:.0f}ms P95={s.p95:.0f}ms P99={s.p99:.0f}ms "
                f"avg={s.avg:.0f}ms errors={s.error_rate:.1%}"
            )
        alerts = self.compare_to_baseline()
        if alerts:
            lines.append("\n  Degradation Alerts:")
            for a in alerts:
                lines.append(f"    {a}")
        return "\n".join(lines)


# ==================== Tests ====================


@pytest.mark.performance
@pytest.mark.p2
class TestAPILatency:

    def test_critical_endpoints_latency(self, logged_in_app):
        """关键端点延迟采集并与基线对比。"""
        token = logged_in_app.page.evaluate("() => localStorage.getItem('token') || ''")
        if not token:
            pytest.skip("未获取到 auth token")
        client = APIClient(token=token)
        collector = LatencyCollector(client)
        collector.measure("query_org", "POST", "/api/query-org")
        collector.measure("get_projects", "POST", "/api/get-projects")
        collector.measure("get_suppliers", "POST", "/api/get-customer-supplier-list")
        collector.measure("meetings", "GET", "/api/qms/v1/meetings")
        print(collector.report())
        alerts = collector.compare_to_baseline()
        if alerts:
            print(f"Performance alerts:\n" + "\n".join(alerts))
        # 不阻塞 Release，仅报告
