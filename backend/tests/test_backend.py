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
        self.assertGreaterEqual(score_data["overall_score"], 85)
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
            self.assertGreaterEqual(res["overall_score"], 85)

            # ASGI POST /api/resume/score
            rec_post = []
            async def send_post(msg): rec_post.append(msg)
            p_payload = json.dumps({"target_role": "Senior Frontend Engineer"}).encode("utf-8")
            async def rec_post_body(): return {"type": "http.request", "body": p_payload, "more_body": False}
            await app({"type": "http", "method": "POST", "path": "/api/resume/score", "headers": []}, rec_post_body, send_post)
            p_body = next(m for m in rec_post if m["type"] == "http.response.body")["body"]
            p_res = json.loads(p_body.decode("utf-8"))
            self.assertIn("overall_score", p_res)
            self.assertGreaterEqual(p_res["overall_score"], 85)
            self.assertTrue(p_res["passed"])

        asyncio.run(run())

    def test_skills_preservation_and_zero_synthetic_additions(self):
        """Verifies skills are never dropped and empty certifications in base stay empty."""
        # Test 1: Pydantic normalizes list of skills into category dict
        raw_payload = {
            "name": "Vishnu",
            "title": "Senior Frontend Engineer",
            "summary": "Proven track record in frontend systems.",
            "skills": ["Angular", "TypeScript", "Signals", "Nx"],
            "certifications": [],
            "experience": [
                {
                    "role": "Senior Engineer",
                    "company": "Parnasoft Technologies — Client: AVEVA",
                    "period": "2025 - Present",
                    "highlights": ["Built apps"]
                }
            ]
        }
        res_obj = ResumeData.model_validate(raw_payload)
        self.assertIn("Technical Skills", res_obj.skills)
        self.assertEqual(res_obj.skills["Technical Skills"], ["Angular", "TypeScript", "Signals", "Nx"])

        # Test 2: _verify_anti_hallucination restores skills if generated skills are empty
        empty_skills_gen = res_obj.model_copy(deep=True)
        empty_skills_gen.skills = {}
        empty_skills_gen.certifications = [
            {"name": "Fake Azure 204", "issuer": "Microsoft", "year": "2023"}
        ]
        verified, audit = generator_chain._verify_anti_hallucination(self.sample_base, empty_skills_gen)
        # Skills should be restored from self.sample_base
        self.assertTrue(len(verified.skills) > 0)
        self.assertIn("frontend", verified.skills)
        # Fake certifications should be wiped because self.sample_base.certifications is empty
        self.assertEqual(len(verified.certifications), 0)

        # Test 3: Template engine rendering fallback to base_resume when skills empty
        html = template_engine.render(empty_skills_gen, base_resume=self.sample_base)
        self.assertIn("SKILLS", html)
        self.assertIn("Angular", html)
        self.assertNotIn("CERTIFICATIONS", html)

    def test_contact_url_normalization_and_portfolio_support(self):
        """Verifies LinkedIn, GitHub, and Portfolio URLs are normalized, never resolve locally, and render concurrently."""
        # 1. Test helper URL normalization
        href, label = template_engine._format_url("linkedin/vishnu-thankappan", "linkedin")
        self.assertEqual(href, "https://www.linkedin.com/in/vishnu-thankappan")
        self.assertEqual(label, "linkedin.com/in/vishnu-thankappan")

        href, label = template_engine._format_url("https://www.linkedin.com/in/vishnu-thankappan-7bbb0675/", "linkedin")
        self.assertEqual(href, "https://www.linkedin.com/in/vishnu-thankappan-7bbb0675")
        self.assertEqual(label, "linkedin.com/in/vishnu-thankappan-7bbb0675")

        href, label = template_engine._format_url("github/TechieWithBeard", "github")
        self.assertEqual(href, "https://github.com/TechieWithBeard")
        self.assertEqual(label, "github.com/TechieWithBeard")

        href, label = template_engine._format_url("techiewithbeard.dev", "portfolio")
        self.assertEqual(href, "https://techiewithbeard.dev")
        self.assertEqual(label, "techiewithbeard.dev")

        # 2. Test ResumeData model with portfolio
        resume = ResumeData(
            name="Vishnu Thankappan",
            title="Senior Frontend Engineer",
            summary="Experienced engineer.",
            linkedin="linkedin/vishnu-thankappan",
            github="https://github.com/TechieWithBeard",
            portfolio="https://techiewithbeard.dev",
            skills={"Frontend": ["Angular", "TypeScript"]},
        )
        self.assertEqual(resume.portfolio, "https://techiewithbeard.dev")

        # 3. Test modern template rendering has both LinkedIn, GitHub, and Portfolio
        html_modern = template_engine.render(resume, template_id="modern")
        self.assertIn('href="https://www.linkedin.com/in/vishnu-thankappan"', html_modern)
        self.assertIn('href="https://github.com/TechieWithBeard"', html_modern)
        self.assertIn('href="https://techiewithbeard.dev"', html_modern)
        self.assertIn('target="_blank"', html_modern)
        self.assertIn('rel="noopener noreferrer"', html_modern)
        self.assertNotIn('href="linkedin/', html_modern)

        # 4. Test executive template rendering
        html_exec = template_engine.render(resume, template_id="executive")
        self.assertIn('href="https://www.linkedin.com/in/vishnu-thankappan"', html_exec)
        self.assertIn('href="https://github.com/TechieWithBeard"', html_exec)
        self.assertIn('href="https://techiewithbeard.dev"', html_exec)
        self.assertNotIn('href="linkedin/', html_exec)

        # 5. Test CV executive template rendering
        html_cv = template_engine.render(resume, template_id="cv_executive")
        self.assertIn('href="https://www.linkedin.com/in/vishnu-thankappan"', html_cv)
        self.assertIn('href="https://github.com/TechieWithBeard"', html_cv)
        self.assertIn('href="https://techiewithbeard.dev"', html_cv)
        self.assertIn("Portfolio", html_cv)
        self.assertNotIn('href="linkedin/', html_cv)

    def test_company_extraction_clean_name(self):
        """Ensures company extraction extracts concise company names and avoids sentence leakage."""
        lely_jd = """At Lely, we develop software that helps automate dairy farms and supports farmers in their daily work.
Working at Lely means contributing to sustainable progress within one of the most innovative organizations in the Netherlands.
About Lely
Founded in 1948, Lely is committed to a sustainable, profitable, and enjoyable future in agriculture."""
        keywords, role, company, loc = generator_chain._extract_job_keywords(lely_jd, target_title=None)
        self.assertEqual(company, "Lely")

        aligned = generator_chain._align_resume_heuristically(
            self.sample_base,
            generator_chain._perform_competency_audit(self.sample_base, keywords, role),
            target_role="Angular Front-End Developer",
            company=company,
        )
        self.assertEqual(aligned.target_company, "Lely")
        self.assertNotIn("Aligned for", aligned.tagline)
        self.assertIn("Software Engineering Architecture", aligned.tagline)
        self.assertNotIn("means contributing", aligned.tagline)
        self.assertNotIn("means contributing", aligned.summary)

    def test_job_title_formatting_and_subheading_cleanliness(self):
        """Verifies job title formatting (Proper/Title Casing, acronyms) and clean subheadings without 'Aligned for'."""
        from backend.app.models.resume import format_job_title, ResumeData, JobInput

        # 1. format_job_title unit checks
        self.assertEqual(format_job_title("frontend engineer"), "Frontend Engineer")
        self.assertEqual(format_job_title("frontend engineer "), "Frontend Engineer")
        self.assertEqual(format_job_title("senior ui/ux architect"), "Senior UI/UX Architect")
        self.assertEqual(format_job_title("angular front-end developer"), "Angular Front-End Developer")
        self.assertEqual(format_job_title("head of engineering"), "Head of Engineering")
        self.assertEqual(format_job_title("ai & devops engineer"), "AI & DevOps Engineer")
        self.assertEqual(format_job_title(""), "Senior Frontend Engineer")

        # 2. Pydantic validation sanitization
        job_in = JobInput(target_title="frontend engineer")
        self.assertEqual(job_in.target_title, "Frontend Engineer")

        resume = ResumeData(
            name="Vishnu Thankappan",
            title="frontend engineer ",
            tagline="Enterprise Architecture • Angular, TypeScript, JavaScript • Aligned for AVEVA",
            target_company="AVEVA",
            summary="Experienced engineer.",
            skills={"frontendArchitecture": ["Angular", "TypeScript", "JavaScript"]},
        )
        self.assertEqual(resume.title, "Frontend Engineer")
        self.assertEqual(resume.tagline, "Enterprise Architecture • Angular, TypeScript, JavaScript")
        self.assertNotIn("Aligned for AVEVA", resume.tagline)

        # 3. Template rendering clean subheading verification
        for template_id in ["modern", "executive", "compact", "cv_executive"]:
            html = template_engine.render(resume, template_id=template_id)
            # Must NOT have lowercase "frontend engineer" in headers or subheadings
            self.assertNotIn("frontend engineer •", html)
            # Must NOT have "Aligned for AVEVA" in subheadings or summary headline
            self.assertNotIn("• Aligned for AVEVA", html)
            self.assertNotIn("Aligned for AVEVA</div>", html)
            # Must have properly Title Cased "Frontend Engineer"
            self.assertIn("Frontend Engineer", html)


    def test_anti_hallucination_restores_empty_experience_highlights(self):
        """Verifies that _verify_anti_hallucination restores highlights from ground truth when omitted by LLM."""
        from backend.app.models.resume import ExperienceItem

        # Simulate LLM output where highlights are empty
        stripped_exp = [
            ExperienceItem(
                role=exp.role,
                company=exp.company,
                period=exp.period,
                location=exp.location,
                highlights=[],  # Empty!
            )
            for exp in self.sample_base.experience
        ]
        test_resume = self.sample_base.model_copy(deep=True)
        test_resume.experience = stripped_exp

        verified, audit = generator_chain._verify_anti_hallucination(self.sample_base, test_resume)

        # Assert all highlights are restored
        for idx, exp in enumerate(verified.experience):
            self.assertGreater(len(exp.highlights), 0, f"Employer {exp.company} still has 0 highlights!")
            self.assertEqual(len(exp.highlights), len(self.sample_base.experience[idx].highlights))

        # Check audit item
        highlight_audits = [a for a in audit if a.check == "Experience Highlights Completeness"]
        self.assertTrue(len(highlight_audits) > 0)
        self.assertEqual(highlight_audits[0].status, "WARNING")
        self.assertIn("Restored", highlight_audits[0].details)

    def test_anti_hallucination_restores_omitted_employers(self):
        """Verifies that _verify_anti_hallucination restores employers if an LLM drops any."""
        test_resume = self.sample_base.model_copy(deep=True)
        # Drop the last employer
        test_resume.experience = [self.sample_base.experience[0].model_copy(deep=True)]

        verified, audit = generator_chain._verify_anti_hallucination(self.sample_base, test_resume)
        self.assertEqual(len(verified.experience), len(self.sample_base.experience))

    def test_template_engine_highlights_fallback_renders_bullets(self):
        """Verifies that template engine safely renders base bullets if highlights are missing."""
        from backend.app.models.resume import ExperienceItem

        resume_no_bullets = self.sample_base.model_copy(deep=True)
        for exp in resume_no_bullets.experience:
            exp.highlights = []

        for template_id in ["modern", "executive", "compact", "cv_executive"]:
            html = template_engine.render(resume_no_bullets, template_id=template_id, base_resume=self.sample_base)
            # Must contain bullet points from base resume
            self.assertIn("<li", html, f"Template {template_id} failed to render bullet points!")
            self.assertIn("Angular", html)

    def test_walmart_job_alignment_experience_preserved(self):
        """Verifies that Walmart JD alignment preserves rich experience highlights across templates."""
        walmart_jd = """About the job
Job Description Summary:
Responsible for coding, unit testing, building high performance and scalable applications that meet the needs of millions of Walmart-International customers, in the areas of supply chain management & Customer experience.
Requirements:
React, Redux, Node.js, JavaScript, Cloud, CI/CD, Agile.
"""
        keywords, target_role, comp, loc = generator_chain._extract_job_keywords(walmart_jd, "Software Engineer")
        audit = generator_chain._perform_competency_audit(self.sample_base, keywords, target_role)
        aligned = generator_chain._align_resume_heuristically(
            self.sample_base, audit, target_role=target_role, company=comp
        )

        # 1. Test with sample_base
        self.assertGreater(len(aligned.experience), 0)
        for exp in aligned.experience:
            self.assertGreater(len(exp.highlights), 0, f"Employer {exp.company} has 0 highlights for Walmart JD!")

        html_sample = template_engine.render(aligned, template_id="modern", base_resume=self.sample_base)
        self.assertIn("Alpha Corp", html_sample)
        self.assertIn("Beta LLC", html_sample)
        self.assertIn("class=\"exp-highlights\"", html_sample)
        self.assertIn("<li", html_sample)

        # 2. Test with real ground truth resume from resume_store
        real_base = resume_store.get_base_resume()
        audit_real = generator_chain._perform_competency_audit(real_base, keywords, target_role)
        aligned_real = generator_chain._align_resume_heuristically(
            real_base, audit_real, target_role=target_role, company=comp
        )
        self.assertGreater(len(aligned_real.experience), 0)
        for exp in aligned_real.experience:
            self.assertGreater(len(exp.highlights), 0, f"Employer {exp.company} has 0 highlights!")

        html_real = template_engine.render(aligned_real, template_id="modern", base_resume=real_base)
        self.assertIn("Parnasoft Technologies", html_real)
        self.assertIn("ACI Logistix", html_real)
        self.assertIn("Maistering B.V", html_real)
        self.assertIn("class=\"exp-highlights\"", html_real)
        self.assertIn("<li", html_real)

    def test_generate_hiring_note(self):
        """Verifies generate_hiring_note generates authentic, concise notes for hiring team / LinkedIn Easy Apply."""
        import asyncio
        from backend.app.models.resume import JobInput

        job_input = JobInput(
            job_description="We are looking for a Senior Frontend Architect at Lely to lead automated farm robotics software.",
            target_title="Senior Frontend Architect",
        )

        async def run_test():
            res = await generator_chain.generate_hiring_note(job_input, self.sample_base)
            self.assertTrue(res["success"])
            self.assertIn("Lely", res["note"])
            self.assertIn("Senior Frontend Architect", res["note"])
            self.assertIn(self.sample_base.name, res["note"])
            self.assertGreater(res["word_count"], 60)
            self.assertLess(res["word_count"], 300)

        asyncio.run(run_test())

    def test_asgi_generate_hiring_note_endpoint(self):
        """Verifies ASGI route POST /api/generate/hiring-note returns 200 with valid note."""
        import asyncio
        import json
        from backend.app.main import app

        async def run_asgi():
            body = json.dumps({
                "job_input": {
                    "job_description": "Software Engineer at Walmart International. Requirements: JavaScript, cloud, architecture.",
                    "target_title": "Software Engineer",
                },
                "base_resume": self.sample_base.model_dump(),
            }).encode("utf-8")

            scope = {
                "type": "http",
                "method": "POST",
                "path": "/api/generate/hiring-note",
                "headers": [(b"content-type", b"application/json")],
            }

            response_status = None
            response_body = b""

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            async def send(message):
                nonlocal response_status, response_body
                if message["type"] == "http.response.start":
                    response_status = message["status"]
                elif message["type"] == "http.response.body":
                    response_body += message.get("body", b"")

            await app(scope, receive, send)

            self.assertEqual(response_status, 200)
            data = json.loads(response_body.decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("note", data)
            self.assertIn("Walmart", data["note"])
            self.assertGreater(data["word_count"], 50)

    def test_dynamic_experience_years_extraction(self):
        """Verifies _extract_experience_years correctly parses explicit text or calculates from experience dates."""
        from datetime import datetime

        # Case 1: Explicit 10+ years in summary
        r1 = ResumeData(
            name="Alice",
            title="Senior Architect",
            summary="Principal engineer with 10+ years of scalable systems design.",
            experience=[]
        )
        self.assertEqual(generator_chain._extract_experience_years(r1), "10+ years")

        # Case 2: Explicit 4 years in summary (normalizes to 4+ years)
        r2 = ResumeData(
            name="Bob",
            title="Engineer",
            summary="Software engineer with 4 years experience.",
            experience=[]
        )
        self.assertEqual(generator_chain._extract_experience_years(r2), "4+ years")

        # Case 3: No years in summary, calculated from period (2020 to Present)
        current_year = datetime.now().year
        expected_diff = current_year - 2020
        r3 = ResumeData(
            name="Charlie",
            title="Developer",
            summary="Passionate backend engineer.",
            experience=[
                ExperienceItem(
                    role="Dev",
                    company="Stripe",
                    period="2020 – Present",
                    highlights=["Built payment routing"]
                )
            ]
        )
        self.assertEqual(generator_chain._extract_experience_years(r3), f"{expected_diff}+ years")

    def test_dynamic_hiring_note_no_hardcoded_leak(self):
        """Verifies candidate with unique profile gets dynamic content without any AVEVA or hardcoded stats."""
        import asyncio
        from backend.app.models.resume import JobInput

        custom_candidate = ResumeData(
            name="Devon Vance",
            title="Distributed Systems Engineer",
            summary="Distributed systems specialist with 4+ years scaling Kubernetes clusters and Rust microservices.",
            email="devon@example.com",
            linkedin="linkedin.com/in/devon-vance",
            experience=[
                ExperienceItem(
                    role="Systems Engineer",
                    company="Cloudflare",
                    period="2022 – Present",
                    highlights=["Optimized edge routing throughput by 45%", "Architected geo-distributed caching mesh"]
                ),
                ExperienceItem(
                    role="Junior Developer",
                    company="Datadog",
                    period="2020 – 2022",
                    highlights=["Maintained telemetry ingest pipelines"]
                )
            ],
            skills={"Infrastructure": ["Rust", "Kubernetes", "gRPC"]}
        )

        job_input = JobInput(
            job_description="Looking for a Distributed Systems Engineer at HashiCorp to work on Consul and Nomad.",
            target_title="Distributed Systems Engineer"
        )

        async def run_check():
            res = await generator_chain.generate_hiring_note(job_input, custom_candidate)
            note = res["note"]
            # Must mention HashiCorp and candidate details
            self.assertIn("HashiCorp", note)
            self.assertIn("Devon Vance", note)
            self.assertIn("4+ years", note)
            self.assertIn("Optimized edge routing throughput by 45%", note)
            # MUST NOT contain hardcoded remnants from other profiles
            self.assertNotIn("AVEVA", note)
            self.assertNotIn("7 years", note)
            self.assertNotIn("7+ years", note)
            self.assertNotIn("Nx monorepo", note)
            self.assertNotIn("25–35%", note)

        asyncio.run(run_check())

    def test_dynamic_why_fit_no_hardcoded_leak(self):
        """Verifies _compose_why_fit dynamically incorporates candidate companies and highlights."""
        from backend.app.models.resume import AlignmentReport
        audit = AlignmentReport(
            target_role="Platform Engineer",
            match_score=85,
            direct_matches=["Rust", "Kubernetes"],
            missing_keywords=[]
        )
        custom_candidate = ResumeData(
            name="Devon Vance",
            title="Distributed Systems Engineer",
            summary="Distributed systems specialist with 4+ years scaling Kubernetes clusters.",
            experience=[
                ExperienceItem(
                    role="Systems Engineer",
                    company="Cloudflare",
                    period="2022 – Present",
                    highlights=["Optimized edge routing throughput by 45%"]
                )
            ],
            skills={"Infrastructure": ["Rust", "Kubernetes"]}
        )

        fit_text = generator_chain._compose_why_fit("HashiCorp", "Platform Engineer", custom_candidate, audit)
        self.assertIn("4+ years", fit_text)
        self.assertIn("Cloudflare", fit_text)
        self.assertIn("Optimized edge routing throughput by 45%", fit_text)
        self.assertNotIn("AVEVA", fit_text)
        self.assertNotIn("ACI Logistix", fit_text)
        self.assertNotIn("7 years", fit_text)


if __name__ == "__main__":
    unittest.main()



