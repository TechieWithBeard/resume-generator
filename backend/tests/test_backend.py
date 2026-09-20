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

    def test_cv_executive_template_rendering(self):
        """Verifies cv_executive template renders projects, certs, publications, and page break rules."""
        from backend.app.models.resume import ProjectItem, CertificationItem
        cv_resume = self.sample_base.model_copy(deep=True)
        cv_resume.document_type = "cv"
        cv_resume.projects = [
            ProjectItem(
                name="Enterprise Monorepo Modernization",
                role="Lead Architect",
                period="2023 – 2024",
                description="Engineered microfrontend architecture for global logistics.",
                technologies=["Angular", "Nx", "RxJS"],
                url="https://example.com/project",
            )
        ]
        cv_resume.certifications = [
            CertificationItem(
                name="AWS Certified Solutions Architect",
                issuer="Amazon Web Services",
                year="2023",
                credential_id="AWS-12345",
            )
        ]
        cv_resume.publications = ["High-Scale UI Architecture in Modern Enterprise Web (2024)"]

        html = template_engine.render(cv_resume, template_id="cv_executive")
        self.assertIn("Curriculum Vitae", html)
        self.assertIn("Enterprise Monorepo Modernization", html)
        self.assertIn("Lead Architect", html)
        self.assertIn("AWS Certified Solutions Architect", html)
        self.assertIn("AWS-12345", html)
        self.assertIn("High-Scale UI Architecture in Modern Enterprise Web", html)
        self.assertIn("avoid-break", html)
        self.assertIn("@media print", html)

    def test_cv_generator_stream_and_alignment(self):
        """Verifies generator stream produces aligned CV with projects, certs, and cv_executive template."""
        from backend.app.models.resume import ProjectItem, CertificationItem
        cv_resume = self.sample_base.model_copy(deep=True)
        cv_resume.projects = [
            ProjectItem(
                name="Mission-Critical Monorepo",
                description="Large scale industrial SaaS platform",
                technologies=["Angular", "TypeScript"],
            )
        ]
        cv_resume.certifications = [
            CertificationItem(
                name="Angular Enterprise Architect",
                issuer="Angular Institute",
                year="2023",
            )
        ]

        async def run_cv_stream():
            job_in = JobInput(
                job_description="Seeking a Principal Frontend Architect to direct engineering and architecture.",
                target_title="Principal Frontend Architect",
                document_type="cv",
            )
            cfg = LLMConfig(provider="heuristic")
            events = []
            async for ev in generator_chain.generate_stream(job_in, cv_resume, cfg):
                events.append(ev)
            return events

        events = asyncio.run(run_cv_stream())
        complete_event = next(e for e in events if e["type"] == "complete")
        gen_data = complete_event["resume"]
        gen_html = complete_event["html"]

        self.assertEqual(gen_data["document_type"], "cv")
        self.assertTrue(len(gen_data["projects"]) > 0)
        self.assertTrue(len(gen_data["certifications"]) > 0)
        self.assertIn("Curriculum Vitae", gen_html)
        self.assertIn("Mission-Critical Monorepo", gen_html)


if __name__ == "__main__":
    unittest.main()

