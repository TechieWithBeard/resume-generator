"""
Unit & Integration Tests for Resume & CV Evaluation Framework.
Tests individual checkpoint gates, failure detection, dataset schema, and ASGI endpoints.
"""

import asyncio
import json
import unittest

from backend.app.evals import (
    AtsFormattingCheckpoint,
    BENCHMARK_DATASET,
    CompanyResearchCheckpoint,
    CompetencyAlignmentCheckpoint,
    NoiseEliminationCheckpoint,
    TruthInvarianceCheckpoint,
    evaluator,
)
from backend.app.evals.models import EvalCase
from backend.app.main import app
from backend.app.models.resume import EducationItem, ExperienceItem, JobInput, LLMConfig, ResumeData
from backend.app.services.resume_store import resume_store


class TestEvaluationFramework(unittest.TestCase):
    def setUp(self):
        self.base_resume = resume_store.get_base_resume()
        self.sample_case = BENCHMARK_DATASET[0]

    def test_truth_invariance_passes_clean_resume(self):
        """Verifies clean resume matching ground truth passes truth invariance checkpoint."""
        result = TruthInvarianceCheckpoint.evaluate(
            self.base_resume, self.base_resume, self.sample_case
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.score, 1.0)
        self.assertEqual(len(result.details["violations"]), 0)

    def test_truth_invariance_catches_fabricated_employer(self):
        """Verifies checkpoint flags fabricated employer not present in ground truth."""
        rogue = self.base_resume.model_copy(deep=True)
        rogue.experience.append(
            ExperienceItem(
                role="VP of Engineering",
                company="Unicorn Fictional Labs",
                period="2024 – Present",
                highlights=["Fabricated architecture accomplishments"],
            )
        )
        result = TruthInvarianceCheckpoint.evaluate(
            self.base_resume, rogue, self.sample_case
        )
        self.assertFalse(result.passed)
        self.assertLess(result.score, 1.0)
        self.assertTrue(any("Unicorn Fictional Labs" in v for v in result.details["violations"]))

    def test_truth_invariance_catches_fabricated_degree(self):
        """Verifies checkpoint flags fabricated degree or institution."""
        rogue = self.base_resume.model_copy(deep=True)
        rogue.education.append(
            EducationItem(
                degree="PhD in AI Systems",
                institution="Massachusetts Institute of Technology",
                period="2018 – 2022",
            )
        )
        result = TruthInvarianceCheckpoint.evaluate(
            self.base_resume, rogue, self.sample_case
        )
        self.assertFalse(result.passed)
        self.assertLess(result.score, 1.0)
        self.assertTrue(any("PhD in AI Systems" in v for v in result.details["violations"]))

    def test_noise_elimination_catches_recruitment_leak(self):
        """Verifies checkpoint catches internal hiring rounds and recruiter screening text."""
        leaky_resume = self.base_resume.model_copy(deep=True)
        leaky_resume.summary += " Our hiring process starts with a call with recruiter (30 mins)."
        result = NoiseEliminationCheckpoint.evaluate(
            leaky_resume, "<html><body>Clean HTML</body></html>", self.sample_case
        )
        self.assertFalse(result.passed)
        self.assertLess(result.score, 1.0)
        self.assertTrue(any("call with" in leak or "30 mins" in leak for leak in result.details["leaks"]))

    def test_noise_elimination_catches_forbidden_terms(self):
        """Verifies case-specific forbidden terms are caught by checkpoint."""
        adv_case = next(c for c in BENCHMARK_DATASET if c.id == "case_adversarial_injection")
        leaky_resume = self.base_resume.model_copy(deep=True)
        leaky_resume.summary += " Worked as Lead at Google Brain."
        result = NoiseEliminationCheckpoint.evaluate(
            leaky_resume, "<html>Google Brain</html>", adv_case
        )
        self.assertFalse(result.passed)
        self.assertTrue(any("Google Brain" in leak for leak in result.details["leaks"]))

    def test_ats_formatting_catches_missing_experience_section(self):
        """Verifies checkpoint flags missing required experience section."""
        html_without_exp = "<html><body><h1>John Doe</h1><div class='section-title'>Education</div></body></html>"
        result = AtsFormattingCheckpoint.evaluate(
            self.base_resume, html_without_exp, self.sample_case
        )
        self.assertFalse(result.passed)
        self.assertTrue(any("Professional Experience" in d for d in result.details["defects"]))

    def test_benchmark_dataset_integrity(self):
        """Verifies all cases in benchmark dataset have valid configurations."""
        self.assertGreaterEqual(len(BENCHMARK_DATASET), 5)
        case_ids = [c.id for c in BENCHMARK_DATASET]
        self.assertEqual(len(case_ids), len(set(case_ids)), "Duplicate case IDs detected in benchmark dataset")
        for case in BENCHMARK_DATASET:
            self.assertTrue(case.name)
            self.assertTrue(case.job_input.job_description)
            self.assertIn(case.document_type, ["resume", "cv"])

    def test_evaluator_single_case_execution(self):
        """Runs evaluate_case on Senior Frontend Architect case and asserts all checkpoints pass."""
        async def run():
            case = next(c for c in BENCHMARK_DATASET if c.id == "case_senior_frontend_architect")
            res = await evaluator.evaluate_case(case, base_resume=self.base_resume, config=LLMConfig(provider="heuristic"))
            self.assertTrue(res.passed)
            self.assertGreaterEqual(res.composite_score, 0.90)
            self.assertEqual(len(res.checkpoints), 5)
            # Ensure every checkpoint passed
            for cp in res.checkpoints:
                self.assertTrue(cp.passed, f"Checkpoint failed: {cp.checkpoint_name} - {cp.message}")
        asyncio.run(run())

    def test_asgi_evals_endpoints(self):
        """Verifies ASGI routes /api/evals/cases, /api/evals/run, and /api/evals/latest."""
        async def run():
            # 1. GET /api/evals/cases
            rec_cases = []
            async def send_cases(msg):
                rec_cases.append(msg)
            async def rec_body():
                return {"type": "http.request", "body": b"", "more_body": False}

            await app({"type": "http", "method": "GET", "path": "/api/evals/cases", "headers": []}, rec_body, send_cases)
            body_msg = next(m for m in rec_cases if m["type"] == "http.response.body")
            cases_data = json.loads(body_msg["body"].decode("utf-8"))
            self.assertIn("cases", cases_data)
            self.assertGreaterEqual(cases_data["total"], 5)

            # 2. POST /api/evals/run (single case for speed)
            rec_run = []
            async def send_run(msg):
                rec_run.append(msg)
            run_payload = json.dumps({"case_id": "case_sparse_minimal_jd"}).encode("utf-8")
            async def rec_run_body():
                return {"type": "http.request", "body": run_payload, "more_body": False}

            await app({"type": "http", "method": "POST", "path": "/api/evals/run", "headers": []}, rec_run_body, send_run)
            run_body_msg = next(m for m in rec_run if m["type"] == "http.response.body")
            report_data = json.loads(run_body_msg["body"].decode("utf-8"))
            self.assertEqual(report_data["total_cases"], 1)
            self.assertEqual(report_data["passed_cases"], 1)

            # 3. GET /api/evals/latest
            rec_latest = []
            async def send_latest(msg):
                rec_latest.append(msg)
            await app({"type": "http", "method": "GET", "path": "/api/evals/latest", "headers": []}, rec_body, send_latest)
            latest_body = next(m for m in rec_latest if m["type"] == "http.response.body")
            latest_data = json.loads(latest_body["body"].decode("utf-8"))
            self.assertEqual(latest_data["passed_cases"], 1)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
