"""
Unit test suite for the Resume Generator backend.
Tests:
- Base Resume loading & persistence
- HTML template rendering & print styling
- Deterministic anti-hallucination verification
- Stream event generation
"""

import unittest
import asyncio
from backend.app.models.resume import (
    ResumeData,
    ExperienceItem,
    EducationItem,
    JobInput,
    LLMConfig,
)
from backend.app.services.resume_store import resume_store
from backend.app.services.template_engine import template_engine
from backend.app.services.generator_chain import generator_chain
from backend.app.services.linkedin_extractor import linkedin_extractor


class TestResumeGenerator(unittest.TestCase):

    def setUp(self):
        self.sample_base = ResumeData(
            name="Test Engineer",
            title="Senior Frontend Architect",
            summary="Proven experience building enterprise web systems.",
            experience=[
                ExperienceItem(
                    role="Senior Engineer",
                    company="Alpha Corp",
                    period="2022 – Present",
                    highlights=["Architected Angular monorepo", "Reduced build times by 30%"]
                ),
                ExperienceItem(
                    role="Frontend Developer",
                    company="Beta LLC",
                    period="2019 – 2022",
                    highlights=["Built design system components"]
                )
            ],
            education=[
                EducationItem(
                    degree="B.S. in Computer Science",
                    institution="State University",
                    period="2015 – 2019"
                )
            ],
            skills={
                "frontend": ["Angular", "TypeScript", "Signals"],
                "tooling": ["Git", "Nx"]
            }
        )

    def test_resume_store_loading(self):
        """Verifies base resume can be retrieved and validated."""
        res = resume_store.get_base_resume()
        self.assertIsNotNone(res.name)
        self.assertTrue(len(res.experience) > 0)
        self.assertIn("frontendArchitecture", res.skills)

    def test_template_rendering(self):
        """Verifies HTML templates render valid HTML with required sections."""
        for tmpl in ["modern", "executive", "compact"]:
            html = template_engine.render(self.sample_base, template_id=tmpl)
            self.assertIn("Test Engineer", html)
            self.assertIn("Senior Frontend Architect", html)
            self.assertIn("Alpha Corp", html)
            self.assertIn("State University", html)
            self.assertIn("@media print", html)

    def test_anti_hallucination_guardrails(self):
        """Verifies deterministic anti-hallucination engine catches unauthorized companies and degrees."""
        rogue_resume = self.sample_base.model_copy(deep=True)
        # Attempt to insert a fake company
        rogue_resume.experience.append(
            ExperienceItem(
                role="CTO",
                company="Fake Unicorn Inc.",
                period="2024 – Present",
                highlights=["Fabricated experience"]
            )
        )
        # Attempt to insert a fake degree
        rogue_resume.education[0].institution = "MIT Stanford Fake Institute"

        verified, audit = generator_chain._verify_anti_hallucination(self.sample_base, rogue_resume)

        # Confirm rogue company was reverted or warning logged
        checks = {item.check: item.status for item in audit}
        self.assertIn("Employer Invariance", checks)
        self.assertIn("Education Invariance", checks)
        self.assertEqual(checks["Employer Invariance"], "WARNING")
        self.assertEqual(checks["Education Invariance"], "WARNING")
        # Ensure fake education was reverted
        self.assertEqual(verified.education[0].institution, "State University")

    def test_generator_stream(self):
        """Verifies streaming generator yields all required event types."""
        async def run_stream():
            job_in = JobInput(
                job_description="Seeking a Senior Angular Architect skilled in TypeScript, Signals, and Nx monorepos."
            )
            cfg = LLMConfig(provider="heuristic")
            events = []
            async for ev in generator_chain.generate_stream(job_in, self.sample_base, cfg):
                events.append(ev)
            return events

        events = asyncio.run(run_stream())
        types = [e["type"] for e in events]
        self.assertIn("step", types)
        self.assertIn("thought", types)
        self.assertIn("audit", types)
        self.assertIn("complete", types)

        # Check complete event payload
        complete_event = next(e for e in events if e["type"] == "complete")
        self.assertIn("resume", complete_event)
        self.assertIn("html", complete_event)
        self.assertIn("audit", complete_event)

    def test_linkedin_url_parser(self):
        """Verifies LinkedIn job ID extraction from standard URL formats."""
        url1 = "https://www.linkedin.com/jobs/view/senior-angular-developer-at-tech-corp-4123891045"
        self.assertEqual(linkedin_extractor.extract_job_id(url1), "4123891045")
        url2 = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=3981726354"
        self.assertEqual(linkedin_extractor.extract_job_id(url2), "3981726354")


if __name__ == "__main__":
    unittest.main()
