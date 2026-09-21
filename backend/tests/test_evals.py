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

    def test_preflight_detects_low_match(self):
        """Verifies preflight check identifies severe skill mismatch and returns is_low_match=True."""
        from backend.app.services.generator_chain import generator_chain
        mismatch_input = JobInput(
            target_title="Senior Embedded Firmware Engineer",
            job_description="Requires 5+ years of bare-metal C, FreeRTOS, ARM Cortex-M4, CAN bus, and PCB layout debugging.",
        )
        report = generator_chain.preflight_check(mismatch_input, self.base_resume)
        self.assertTrue(report.is_low_match)
        self.assertLess(report.match_score, 40)
        self.assertIn("FreeRTOS", report.unmatched_skills)
        self.assertTrue(len(report.direct_matches) == 0)

    def test_truth_invariance_catches_fabricated_skills(self):
        """Verifies TruthInvarianceCheckpoint catches unverified synthetic skills."""
        rogue = self.base_resume.model_copy(deep=True)
        rogue.skills["Embedded & Firmware"] = ["FreeRTOS", "ARM Cortex-M4", "CAN bus"]
        result = TruthInvarianceCheckpoint.evaluate(
            self.base_resume, rogue, self.sample_case
        )
        self.assertFalse(result.passed)
        self.assertTrue(any("Fabricated skill(s)" in v for v in result.details["violations"]))

    def test_strict_skills_non_fabrication_gate_purges_rogue_skills(self):
        """Verifies Check 7 in generator_chain._verify_anti_hallucination purges unverified skills."""
        from backend.app.services.generator_chain import generator_chain
        rogue = self.base_resume.model_copy(deep=True)
        rogue.skills["Fabricated"] = ["Swift", "FreeRTOS", "Golang"]
        verified, audit = generator_chain._verify_anti_hallucination(
            self.base_resume, rogue, doc_type="resume"
        )
        check_7 = next(item for item in audit if item.check == "Strict Skills Non-Fabrication Gate")
        self.assertEqual(check_7.status, "WARNING")
        # Ensure rogue skills were purged from verified output
        all_skills = [s.lower() for cat in verified.skills.values() for s in cat]
        self.assertNotIn("freertos", all_skills)
        self.assertNotIn("swift", all_skills)

    def test_asgi_preflight_endpoint(self):
        """Verifies POST /api/generate/preflight returns accurate preflight report via ASGI."""
        async def run():
            rec_pre = []
            async def send_pre(msg):
                rec_pre.append(msg)
            payload = json.dumps({
                "job_input": {
                    "target_title": "Embedded Systems Engineer",
                    "job_description": "C, FreeRTOS, ARM Cortex, CAN bus, logic analyzers",
                }
            }).encode("utf-8")
            async def rec_body():
                return {"type": "http.request", "body": payload, "more_body": False}

            await app({"type": "http", "method": "POST", "path": "/api/generate/preflight", "headers": []}, rec_body, send_pre)
            body_msg = next(m for m in rec_pre if m["type"] == "http.response.body")
            data = json.loads(body_msg["body"].decode("utf-8"))
            self.assertTrue(data["is_low_match"])
            self.assertLess(data["match_score"], 40)
            self.assertIn("unmatched_skills", data)
        asyncio.run(run())

    def test_evaluator_extreme_mismatch_hitl_case(self):
        """Runs evaluator on case_extreme_mismatch_hitl and verifies all checkpoints pass without hallucination."""
        async def run():
            case = next(c for c in BENCHMARK_DATASET if c.id == "case_extreme_mismatch_hitl")
            res = await evaluator.evaluate_case(case, base_resume=self.base_resume, config=LLMConfig(provider="heuristic"))
            self.assertTrue(res.passed)
            # Ensure Truth Invariance and Noise Elimination pass 100%
            ti_cp = next(cp for cp in res.checkpoints if cp.checkpoint_name == "Truth Invariance Checkpoint")
            self.assertTrue(ti_cp.passed, f"Truth Invariance failed: {ti_cp.message}")
            ne_cp = next(cp for cp in res.checkpoints if cp.checkpoint_name == "Noise Elimination Checkpoint")
            self.assertTrue(ne_cp.passed, f"Noise Elimination failed: {ne_cp.message}")
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
