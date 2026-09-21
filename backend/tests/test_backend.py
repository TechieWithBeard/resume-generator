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
import json
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
        """Verifies cv_executive template renders projects, certs, publications, role scope, target banner, and page break rules."""
        from backend.app.models.resume import ProjectItem, CertificationItem
        cv_resume = self.sample_base.model_copy(deep=True)
        cv_resume.document_type = "cv"
        cv_resume.target_role = "Senior Frontend Developer"
        cv_resume.target_company = "Rentman"
        cv_resume.experience[0].scope = "Lead Frontend Architect directing architecture across European teams."
        cv_resume.experience[0].technologies = ["Angular 20", "Nx", "TypeScript", "Signals"]
        cv_resume.experience.append(
            ExperienceItem(
                role="Senior Frontend Engineer",
                company="Maistering B.V.",
                period="2019 – 2022",
                highlights=["Delivered enterprise platforms for Netherlands client."],
            )
        )
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
        self.assertIn("Senior Frontend Developer", html)
        self.assertIn("Rentman", html)
        self.assertIn("TARGET ROLE ALIGNMENT", html)
        self.assertIn("SCOPE &amp; LEADERSHIP" if "&amp;" in html else "SCOPE & LEADERSHIP", html)
        self.assertIn("Lead Frontend Architect directing architecture across European teams", html)
        self.assertIn("Environment:", html)
        self.assertIn("competency-card", html)
        self.assertIn("Enterprise Monorepo Modernization", html)
        self.assertIn("Lead Architect", html)
        self.assertIn("Architecture Stack:", html)
        self.assertIn("AWS Certified Solutions Architect", html)
        self.assertIn("AWS-12345", html)
        self.assertIn("High-Scale UI Architecture in Modern Enterprise Web", html)
        self.assertIn("European Enterprise", html)
        self.assertIn("Netherlands", html)
        self.assertIn("avoid-break", html)
        self.assertIn("@media print", html)
        self.assertNotIn("DIFF VIEW ACTIVE", html)

        # Verify Diff Highlighting Mode
        diff_html = template_engine.render(cv_resume, template_id="cv_executive", highlight_diff=True)
        self.assertIn("DIFF VIEW ACTIVE", diff_html)
        self.assertIn("Tailored Profile", diff_html)

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
        self.assertEqual(gen_data.get("target_role"), "Principal Frontend Architect")
        self.assertTrue(len(gen_data["projects"]) > 0)
        self.assertTrue(len(gen_data["certifications"]) > 0)
        self.assertTrue(any(exp.get("scope") for exp in gen_data["experience"]))
        self.assertTrue(any(len(exp.get("technologies", [])) > 0 for exp in gen_data["experience"]))
        self.assertIn("Curriculum Vitae", gen_html)
        self.assertIn("Mission-Critical Monorepo", gen_html)
        self.assertIn("Principal Frontend Architect", gen_html)

    def test_resume_score_checker_and_endpoints(self):
        """Verifies 9-dimension Resume Score Checker and /api/resume/score endpoints."""
        from backend.app.services.resume_score_checker import resume_score_checker
        from backend.app.main import app

        # Direct service audit
        base = resume_store.get_base_resume()
        html = template_engine.render(base)
        score_data = resume_score_checker.audit(base, rendered_html=html)
        self.assertGreaterEqual(score_data["overall_score"], 90)
        self.assertTrue(score_data["passed"])
        self.assertEqual(len(score_data["dimensions"]), 9)
        for dim in [
            "customization", "spelling_and_grammar", "summary_statement", "measurable_results",
            "word_choice", "formatting", "optimal_length", "contact_information", "comprehensiveness"
        ]:
            self.assertIn(dim, score_data["dimensions"])

        # ASGI GET /api/resume/score
        async def run():
            rec_get = []
            async def send_get(msg): rec_get.append(msg)
            async def rec_body(): return {"type": "http.request", "body": b"", "more_body": False}
            await app({"type": "http", "method": "GET", "path": "/api/resume/score", "headers": []}, rec_body, send_get)
            body = next(m for m in rec_get if m["type"] == "http.response.body")["body"]
            res = json.loads(body.decode("utf-8"))
            self.assertIn("overall_score", res)
            self.assertGreaterEqual(res["overall_score"], 90)

            # ASGI POST /api/resume/score
            rec_post = []
            async def send_post(msg): rec_post.append(msg)
            p_payload = json.dumps({"target_role": "Senior Frontend Engineer"}).encode("utf-8")
            async def rec_post_body(): return {"type": "http.request", "body": p_payload, "more_body": False}
            await app({"type": "http", "method": "POST", "path": "/api/resume/score", "headers": []}, rec_post_body, send_post)
            p_body = next(m for m in rec_post if m["type"] == "http.response.body")["body"]
            p_res = json.loads(p_body.decode("utf-8"))
            self.assertIn("overall_score", p_res)
            self.assertIn("A+", p_res["grade"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()

