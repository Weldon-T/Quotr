"""AI Golden Baseline — BERTScore + RAGAs + structured metrics evaluation.

依赖: pip install bert-score ragas datasets

测试流程:
  1. 加载 Golden Baseline 图纸集
  2. 通过 API 触发 AI 解析（或从已缓存结果加载）
  3. 计算结构化指标（F1、数量偏差、Schema 合规）
  4. 计算 BERTScore（材料名称/描述语义相似度）
  5. 计算 RAGAs（Context Relevance / Faithfulness / Answer Relevance）
  6. 与上次基线对比，生成退化报告
"""
import json
import pytest
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

FIXTURES_DIR = Path(__file__).parent / "fixtures"
BASELINE_FILE = FIXTURES_DIR / "baseline_v1.json"


@dataclass
class AISample:
    """一个 Golden Baseline 样本。"""
    id: str
    drawing_path: str               # 图纸文件路径
    ground_truth: dict              # 人工标注: {room_types, materials, quantities, total_cost}
    ground_truth_texts: list[str]   # 用于 BERTScore 的参考文本（材料名、描述）
    ground_truth_contexts: list[str]  # 预期检索到的成本数据


@dataclass
class AIEvaluationResult:
    """单次评估的完整结果。"""
    sample_id: str
    # 结构化
    detection_f1: float
    quantity_error_pct: float
    schema_valid: bool
    # BERTScore
    bertscore_f1: float
    # RAGAs
    context_relevance: float
    faithfulness: float
    answer_relevance: float
    # 业务
    total_cost_error_pct: float
    # 原始输出
    raw_output: dict = field(default_factory=dict)


class AIBaselineEvaluator:
    """
    AI 管线评估器。

    封装了结构化对比 + BERTScore + RAGAs 的完整评估流程。
    """

    def __init__(self):
        self.samples: list[AISample] = []
        self.results: list[AIEvaluationResult] = []

    # ---- 加载 ----

    def load_samples(self, baseline_file: Path = BASELINE_FILE) -> "AIBaselineEvaluator":
        """加载 Golden Baseline 样本集。"""
        if baseline_file.exists():
            data = json.loads(baseline_file.read_text())
            for item in data:
                self.samples.append(AISample(**item))
        return self

    def add_sample(self, sample: AISample) -> "AIBaselineEvaluator":
        self.samples.append(sample)
        return self

    # ---- 执行 ----

    def run_ai_pipeline(self, drawing_path: str) -> dict:
        """
        调用 Quotr AI 管线处理图纸。

        TODO: 入职后接入实际 API。当前为占位——返回模拟结构。
        """
        # 实际实现: POST /api/ai/takeoff 或调用 SDK
        # response = self.api_client.takeoff(drawing_path)
        # return response.json()
        return {
            "elements": [],
            "total_cost": 0,
            "materials": [],
            "descriptions": [],
            "retrieved_contexts": [],
        }

    # ---- 评估 ----

    def evaluate_structured(self, output: dict, gt: dict) -> tuple[float, float, bool]:
        """结构化对比：F1、数量偏差、Schema 合规。"""
        # TODO: 实现实际的结构化对比逻辑
        f1 = 0.0
        qty_error = 0.0
        schema_ok = True
        return f1, qty_error, schema_ok

    def evaluate_bertscore(self, predictions: list[str], references: list[str]) -> float:
        """使用 BERTScore 计算语义相似度。"""
        try:
            from bert_score import score
            _, _, F1 = score(predictions, references, lang="en", verbose=False)
            return float(F1.mean().item())
        except ImportError:
            return -1.0  # 表示 BERTScore 未安装

    def evaluate_ragas(
        self,
        questions: list[str],
        contexts: list[list[str]],
        answers: list[str],
        ground_truths: list[str],
    ) -> tuple[float, float, float]:
        """使用 RAGAs 计算检索与生成质量。"""
        try:
            from ragas import evaluate
            from ragas.metrics import context_relevance, faithfulness, answer_relevance
            from datasets import Dataset

            ds = Dataset.from_dict({
                "question": questions,
                "contexts": contexts,
                "answer": answers,
                "ground_truth": ground_truths,
            })
            result = evaluate(ds, metrics=[context_relevance, faithfulness, answer_relevance])
            return (
                float(result["context_relevance"]),
                float(result["faithfulness"]),
                float(result["answer_relevance"]),
            )
        except ImportError:
            return (-1.0, -1.0, -1.0)

    # ---- 报告 ----

    def summary(self) -> str:
        """生成评估摘要。"""
        if not self.results:
            return "No results yet."
        n = len(self.results)
        avg_detection = sum(r.detection_f1 for r in self.results) / n
        avg_bertscore = sum(r.bertscore_f1 for r in self.results if r.bertscore_f1 >= 0) / max(1, n)
        avg_faithfulness = sum(r.faithfulness for r in self.results if r.faithfulness >= 0) / max(1, n)
        cost_errors = [r.total_cost_error_pct for r in self.results]
        return (
            f"AI Baseline — {n} samples\n"
            f"  Detection F1:  {avg_detection:.3f}\n"
            f"  BERTScore F1:  {avg_bertscore:.3f}\n"
            f"  Faithfulness:  {avg_faithfulness:.3f}\n"
            f"  Cost Error:    min={min(cost_errors):.1f}% avg={sum(cost_errors)/n:.1f}% max={max(cost_errors):.1f}%"
        )


# ==================== Pytest Fixtures & Tests ====================


@pytest.fixture(scope="module")
def evaluator():
    """提供预加载的 evaluator 实例。"""
    ev = AIBaselineEvaluator()
    ev.load_samples()
    return ev


@pytest.mark.ai
@pytest.mark.p2
class TestAIGoldenBaseline:
    """Golden Baseline 回归测试。每次 AI 变更时运行。"""

    @pytest.mark.skip(reason="需 Golden Baseline 样本和 API 接入")
    def test_detection_f1_within_go_range(self, evaluator):
        """构件检测 F1 在 GO 范围内（退化 ≤ 2%）。"""
        pass

    @pytest.mark.skip(reason="需 Golden Baseline 样本和 API 接入")
    def test_bertscore_within_go_range(self, evaluator):
        """BERTScore ≥ 0.90。"""
        pass

    @pytest.mark.skip(reason="需 Golden Baseline 样本和 API 接入")
    def test_ragas_faithfulness_within_go_range(self, evaluator):
        """RAGAs Faithfulness ≥ 0.90——估算金额有检索数据支撑。"""
        pass

    @pytest.mark.skip(reason="需 Golden Baseline 样本和 API 接入")
    def test_total_cost_error_within_go_range(self, evaluator):
        """总金额偏差 ≤ 10%。"""
        pass


@pytest.mark.ai
@pytest.mark.p2
class TestAISchema:
    @pytest.mark.skip(reason="需 AI 输出 Schema 定义")
    def test_output_conforms_to_schema(self):
        """AI 输出符合 JSON Schema，100% 合规。"""
        pass
