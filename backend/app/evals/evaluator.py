"""
Evaluation Orchestrator & Scoring Engine.
Executes test scenarios through the generation pipeline, evaluates checkpoints,
and compiles quantitative benchmark reports.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional

from backend.app.models.resume import AlignmentReport, LLMConfig, ResumeData
from backend.app.services.generator_chain import generator_chain
from backend.app.services.resume_store import resume_store
from backend.app.services.template_engine import template_engine
from backend.app.evals.checkpoints import (
    AtsFormattingCheckpoint,
    CompanyResearchCheckpoint,
    CompetencyAlignmentCheckpoint,
    NoiseEliminationCheckpoint,
    TruthInvarianceCheckpoint,
)
from backend.app.evals.dataset import BENCHMARK_DATASET
from backend.app.evals.models import (
    CheckpointResult,
    EvalCase,
    EvalCaseResult,
    EvalSuiteReport,
)


class ResumeEvaluator:
    """Orchestrates benchmark evaluation runs and compiles checkpoint reports."""

    def __init__(self):
        self._latest_report: Optional[EvalSuiteReport] = None

    @property
    def latest_report(self) -> Optional[EvalSuiteReport]:
        return self._latest_report

    async def evaluate_case(
        self,
        eval_case: EvalCase,
        base_resume: Optional[ResumeData] = None,
        config: Optional[LLMConfig] = None,
    ) -> EvalCaseResult:
        """Runs a single test case through the generator and audits all checkpoints."""
        if base_resume is None:
            base_resume = resume_store.get_base_resume()
        if config is None:
            config = LLMConfig(provider="heuristic")

        start_time = time.perf_counter()
        tailored_resume = None
        rendered_html = ""
        audit_report = None
        error_msg = None

        try:
            async for ev in generator_chain.generate_stream(
                job_input=eval_case.job_input,
                base_resume=base_resume,
                config=config,
                template_id=eval_case.template_id,
            ):
                ev_type = ev.get("type")
                if ev_type == "audit":
                    data = ev.get("data", {})
                    audit_report = AlignmentReport.model_validate(data)
                elif ev_type == "complete":
                    res_data = ev.get("resume", {})
                    tailored_resume = ResumeData.model_validate(res_data)
                    rendered_html = ev.get("html", "")
        except Exception as e:
            error_msg = f"Generation error: {str(e)}"

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if not tailored_resume:
            return EvalCaseResult(
                case_id=eval_case.id,
                case_name=eval_case.name,
                document_type=eval_case.document_type,
                passed=False,
                composite_score=0.0,
                checkpoints=[
                    CheckpointResult(
                        checkpoint_name="Pipeline Execution Checkpoint",
                        category="truth_invariance",
                        passed=False,
                        score=0.0,
                        threshold=1.0,
                        message=error_msg or "Failed to produce tailored resume.",
                    )
                ],
                latency_ms=round(latency_ms, 2),
                error=error_msg,
            )

        # Audit Checkpoints
        checkpoints: List[CheckpointResult] = []

        # 1. Truth Invariance Gate
        cp_truth = TruthInvarianceCheckpoint.evaluate(base_resume, tailored_resume, eval_case)
        checkpoints.append(cp_truth)

        # 2. Noise Elimination Gate
        cp_noise = NoiseEliminationCheckpoint.evaluate(tailored_resume, rendered_html, eval_case)
        checkpoints.append(cp_noise)

        # 3. Competency Alignment Gate
        cp_alignment = CompetencyAlignmentCheckpoint.evaluate(tailored_resume, audit_report, eval_case)
        checkpoints.append(cp_alignment)

        # 4. ATS & Formatting Gate
        cp_ats = AtsFormattingCheckpoint.evaluate(tailored_resume, rendered_html, eval_case)
        checkpoints.append(cp_ats)

        # 5. Company Research Gate
        cp_research = CompanyResearchCheckpoint.evaluate(tailored_resume, eval_case)
        checkpoints.append(cp_research)

        # All checkpoints must pass for the case to pass
        all_passed = all(cp.passed for cp in checkpoints)
        # Weighted composite score:
        # Truth (30%), Noise (20%), Alignment (25%), ATS (15%), Research (10%)
        weights = {
            "truth_invariance": 0.30,
            "noise_elimination": 0.20,
            "competency_alignment": 0.25,
            "ats_formatting": 0.15,
            "research_intelligence": 0.10,
        }
        composite_score = sum(cp.score * weights.get(cp.category, 0.2) for cp in checkpoints)

        return EvalCaseResult(
            case_id=eval_case.id,
            case_name=eval_case.name,
            document_type=eval_case.document_type,
            passed=all_passed,
            composite_score=round(composite_score, 3),
            checkpoints=checkpoints,
            latency_ms=round(latency_ms, 2),
            generated_role=getattr(tailored_resume, "target_role", None) or eval_case.job_input.target_title,
            match_score=audit_report.match_score if audit_report else None,
        )

    async def evaluate_suite(
        self,
        cases: Optional[List[EvalCase]] = None,
        base_resume: Optional[ResumeData] = None,
        config: Optional[LLMConfig] = None,
        suite_name: str = "Resume & CV Zero-Hallucination Alignment Benchmark",
    ) -> EvalSuiteReport:
        """Runs an entire evaluation suite across all benchmark cases."""
        if cases is None:
            cases = BENCHMARK_DATASET
        if base_resume is None:
            base_resume = resume_store.get_base_resume()
        if config is None:
            config = LLMConfig(provider="heuristic")

        results: List[EvalCaseResult] = []
        for case in cases:
            res = await self.evaluate_case(case, base_resume=base_resume, config=config)
            results.append(res)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        pass_rate = round((passed / total) * 100.0, 1) if total > 0 else 0.0
        avg_score = round(sum(r.composite_score for r in results) / total, 3) if total > 0 else 0.0

        # Category aggregate scores
        category_sums: Dict[str, float] = {}
        category_counts: Dict[str, int] = {}
        checkpoint_summary: Dict[str, Dict[str, Any]] = {}

        for r in results:
            for cp in r.checkpoints:
                category_sums[cp.category] = category_sums.get(cp.category, 0.0) + cp.score
                category_counts[cp.category] = category_counts.get(cp.category, 0) + 1

                cp_stat = checkpoint_summary.setdefault(cp.checkpoint_name, {"passed": 0, "failed": 0, "scores": []})
                if cp.passed:
                    cp_stat["passed"] += 1
                else:
                    cp_stat["failed"] += 1
                cp_stat["scores"].append(cp.score)

        category_scores = {
            cat: round(category_sums[cat] / category_counts[cat], 3)
            for cat in category_sums
        }

        report = EvalSuiteReport(
            suite_name=suite_name,
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            pass_rate=pass_rate,
            average_score=avg_score,
            category_scores=category_scores,
            checkpoint_summary=checkpoint_summary,
            case_results=results,
        )

        self._latest_report = report
        return report

    def format_terminal(self, report: EvalSuiteReport) -> str:
        """Formats the report into clean terminal output with tables."""
        lines = []
        lines.append("=" * 78)
        lines.append(f"  EVALUATION SUITE: {report.suite_name}")
        lines.append("=" * 78)
        lines.append(
            f"  Total Cases: {report.total_cases} | "
            f"Passed: {report.passed_cases} | "
            f"Failed: {report.failed_cases} | "
            f"Pass Rate: {report.pass_rate}% | "
            f"Average Score: {round(report.average_score * 100, 1)}%"
        )
        lines.append("-" * 78)
        lines.append("  CATEGORY BENCHMARK SCORES:")
        for cat, score in report.category_scores.items():
            bar_len = int(score * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  • {cat.replace('_', ' ').title():<28} [{bar}] {round(score * 100, 1)}%")
        lines.append("-" * 78)
        lines.append("  CASE-BY-CASE BREAKDOWN:")
        for c in report.case_results:
            status_icon = "✓ PASS" if c.passed else "✗ FAIL"
            lines.append(f"\n  [{status_icon}] {c.case_name} ({c.document_type.upper()}) — Score: {round(c.composite_score * 100, 1)}% ({c.latency_ms}ms)")
            for cp in c.checkpoints:
                cp_icon = "✓" if cp.passed else "✗"
                lines.append(f"      {cp_icon} {cp.checkpoint_name:<42} [{round(cp.score * 100)}%] {cp.message}")
        lines.append("=" * 78)
        return "\n".join(lines)

    def format_markdown(self, report: EvalSuiteReport) -> str:
        """Formats the report into a GitHub-flavored Markdown document."""
        lines = []
        lines.append(f"# {report.suite_name}")
        lines.append(f"*Evaluated at: `{report.timestamp}`*\n")
        lines.append("## Executive Summary")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| **Total Cases** | {report.total_cases} |")
        lines.append(f"| **Passed** | {report.passed_cases} |")
        lines.append(f"| **Failed** | {report.failed_cases} |")
        lines.append(f"| **Pass Rate** | **{report.pass_rate}%** |")
        lines.append(f"| **Average Score** | **{round(report.average_score * 100, 1)}%** |\n")

        lines.append("## Category Benchmark Scores")
        lines.append("| Category | Average Score | Status |")
        lines.append("|---|---|---|")
        for cat, score in report.category_scores.items():
            status = "🟢 Excellent" if score >= 0.90 else ("🟡 Acceptable" if score >= 0.70 else "🔴 Deficient")
            lines.append(f"| {cat.replace('_', ' ').title()} | {round(score * 100, 1)}% | {status} |")
        lines.append("")

        lines.append("## Detailed Checkpoint Results by Case")
        for c in report.case_results:
            badge = "🟢 **PASSED**" if c.passed else "🔴 **FAILED**"
            lines.append(f"### {c.case_name} ({c.document_type.upper()}) — {badge}")
            lines.append(f"- **Composite Score**: `{round(c.composite_score * 100, 1)}%`")
            lines.append(f"- **Execution Latency**: `{c.latency_ms} ms`")
            if c.match_score is not None:
                lines.append(f"- **Competency Match Score**: `{c.match_score}%`")
            lines.append("\n| Checkpoint | Status | Score | Message |")
            lines.append("|---|---|---|---|")
            for cp in c.checkpoints:
                cp_badge = "✅ Pass" if cp.passed else "❌ Fail"
                lines.append(f"| {cp.checkpoint_name} | {cp_badge} | {round(cp.score * 100)}% | {cp.message} |")
            lines.append("")

        return "\n".join(lines)


evaluator = ResumeEvaluator()
