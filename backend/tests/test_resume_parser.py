"""
Unit test suite for the ResumeParserService and resume upload endpoint.
Tests:
- In-memory text, markdown, docx, and json extraction
- Deterministic heuristic information extraction
- ASGI POST /api/resume/upload endpoint integration
"""

import asyncio
import base64
import io
import json
import unittest
import zipfile
from backend.app.services.resume_parser import resume_parser
from backend.app.main import app


class TestResumeParser(unittest.TestCase):

    def setUp(self):
        self.sample_text = (
            "Marcus Vance\n"
            "Principal UI Architect\n"
            "Seattle, WA | marcus.vance@tech.io | +1-206-555-0144\n"
            "https://linkedin.com/in/marcusvance | https://github.com/marcusvance\n\n"
            "SUMMARY\n"
            "Accomplished Principal UI Architect with 8+ years specializing in enterprise Angular, TypeScript, and microfrontends.\n\n"
            "EXPERIENCE\n"
            "Principal Architect — CloudScale Systems | 2021 – Present\n"
            "• Restructured Nx monorepo serving 6 applications, cutting build times by 35%.\n"
            "• Spearheaded design system migration across 12 product squads.\n\n"
            "Senior Frontend Engineer — Alpha Labs | 2017 – 2021\n"
            "• Built real-time analytics streaming dashboard using RxJS and WebSockets.\n"
            "• Standardized testing with Cypress and Karma.\n\n"
            "EDUCATION\n"
            "Bachelor of Science in Computer Science — University of Washington | 2013 – 2017\n\n"
            "SKILLS\n"
            "Angular, TypeScript, Signals, RxJS, Nx, Python, Docker, CI/CD, Git, Cypress\n"
        )

    def test_text_and_heuristic_extraction(self):
        """Verifies text extraction and heuristic NLP parser extracts candidate fields."""
        async def run():
            resume, meta = await resume_parser.parse_resume(
                self.sample_text.encode("utf-8"), "marcus_resume.txt"
            )
            self.assertEqual(resume.name, "Marcus Vance")
            self.assertEqual(resume.title, "Principal UI Architect")
            self.assertEqual(resume.email, "marcus.vance@tech.io")
            self.assertEqual(resume.phone, "+1-206-555-0144")
            self.assertEqual(resume.linkedin, "https://linkedin.com/in/marcusvance")
            self.assertEqual(resume.github, "https://github.com/marcusvance")
            self.assertTrue(len(resume.experience) >= 2)
            self.assertEqual(resume.experience[0].company, "CloudScale Systems")
            self.assertEqual(resume.experience[0].period, "2021 – Present")
            self.assertTrue(len(resume.experience[0].highlights) >= 1)
            self.assertTrue(len(resume.education) >= 1)
            self.assertIn("Angular", resume.skills["frontendArchitecture"])
            self.assertEqual(meta["format"], "txt")
            self.assertTrue(meta["word_count"] > 50)

        asyncio.run(run())

    def test_json_schema_direct_ingestion(self):
        """Verifies valid JSON resume is parsed directly with schema fidelity."""
        async def run():
            json_payload = json.dumps({
                "name": "Jane Doe",
                "title": "Lead Software Architect",
                "summary": "Proven track record in distributed cloud architectures.",
                "experience": [],
                "education": [],
                "skills": {"cloud": ["AWS", "Docker"]}
            }).encode("utf-8")

            resume, meta = await resume_parser.parse_resume(json_payload, "resume.json")
            self.assertEqual(resume.name, "Jane Doe")
            self.assertEqual(resume.title, "Lead Software Architect")
            self.assertEqual(meta["extraction_method"], "direct_json_schema")

        asyncio.run(run())

    def test_docx_in_memory_extraction(self):
        """Verifies in-memory docx XML parsing."""
        # Create minimal valid docx ZIP in memory
        xml_doc = (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            b'<w:body>'
            b'<w:p><w:r><w:t>Elena Rostova</w:t></w:r></w:p>'
            b'<w:p><w:r><w:t>elena@example.com</w:t></w:r></w:p>'
            b'<w:p><w:r><w:t>Senior Cloud Architect</w:t></w:r></w:p>'
            b'</w:body>'
            b'</w:document>'
        )
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w") as zf:
            zf.writestr("word/document.xml", xml_doc)
        docx_bytes = bio.getvalue()

        async def run():
            resume, meta = await resume_parser.parse_resume(docx_bytes, "elena_resume.docx")
            self.assertEqual(resume.name, "Elena Rostova")
            self.assertEqual(resume.email, "elena@example.com")
            self.assertEqual(meta["format"], "docx")

        asyncio.run(run())

    def test_asgi_upload_endpoint(self):
        """Verifies POST /api/resume/upload endpoint with base64 payload via ASGI."""
        async def run():
            received_messages = []
            async def send(msg):
                received_messages.append(msg)

            b64_content = base64.b64encode(self.sample_text.encode("utf-8")).decode("ascii")
            payload = json.dumps({
                "filename": "marcus_resume.txt",
                "file_data": b64_content,
                "save": False
            }).encode("utf-8")

            async def receive():
                return {"type": "http.request", "body": payload, "more_body": False}

            scope = {
                "type": "http",
                "method": "POST",
                "path": "/api/resume/upload",
                "headers": [(b"content-type", b"application/json")],
            }

            await app(scope, receive, send)

            start_msg = next(m for m in received_messages if m["type"] == "http.response.start")
            body_msg = next(m for m in received_messages if m["type"] == "http.response.body")
            self.assertEqual(start_msg["status"], 200)

            data = json.loads(body_msg["body"].decode("utf-8"))
            self.assertTrue(data["success"])
            self.assertEqual(data["resume"]["name"], "Marcus Vance")
            self.assertEqual(data["metadata"]["filename"], "marcus_resume.txt")

        asyncio.run(run())

    def test_normalize_letter_spaced_text_and_zero_loss(self):
        """Verifies text normalization eliminates letter-spacing and preserves candidate data."""
        from backend.app.services.resume_parser import normalize_extracted_text
        import os

        # Test synthetic tracked/spaced text (Canva/Figma/LaTeX pattern)
        raw_spaced = "V I S H N U   T H A N K A P P A N\nS e n i o r   F r o n t e n d   E n g i n e e r\nv i s h n u t 0 7 1 @ g m a i l . c o m"
        normalized = normalize_extracted_text(raw_spaced)
        self.assertIn("VISHNU THANKAPPAN", normalized)
        self.assertIn("Senior Frontend Engineer", normalized)
        self.assertIn("vishnut071@gmail.com", normalized)

        # Test real artifact PDF if available
        pdf_path = "/Users/techiewithbeard/Downloads/vishnu-portfolio/RAG-Apps/ml/artifacts/VishnuThankappan_resume_2026.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            async def run_pdf():
                resume, meta = await resume_parser.parse_resume(pdf_bytes, "VishnuThankappan_resume_2026.pdf")
                self.assertEqual(resume.name, "Vishnu Thankappan")
                self.assertEqual(resume.email, "vishnut071@gmail.com")
                self.assertTrue(len(resume.experience) >= 3)
                self.assertTrue(len(resume.education) >= 2)
                self.assertTrue(len(resume.raw_text) > 2000)

            asyncio.run(run_pdf())


if __name__ == "__main__":
    unittest.main()
