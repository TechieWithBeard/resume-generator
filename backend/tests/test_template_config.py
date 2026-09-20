"""
Unit tests for Template Customization Studio & Dynamic Theming Engine.
Tests:
- TemplateConfig model validation and defaults
- ResumeStore template config persistence (save/get/reset)
- TemplateEngine dynamic styling injection (colors, fonts, density, layout)
- ASGI GET and PUT /api/template/config endpoints
"""

import asyncio
import json
import unittest
from backend.app.models.resume import (
    ResumeData,
    TemplateConfig,
)
from backend.app.services.resume_store import resume_store
from backend.app.services.template_engine import template_engine
from backend.app.main import app


class TestTemplateConfig(unittest.TestCase):

    def setUp(self):
        self.sample_resume = ResumeData(
            name="Alex Morgan",
            title="Principal Enterprise Architect",
            tagline="Enterprise Architecture • Cloud Systems",
            summary="Strategic architecture leader with 10+ years scaling mission-critical platforms.",
            experience=[],
            education=[],
            skills={"cloud": ["AWS", "Kubernetes", "Terraform"]},
        )

    def tearDown(self):
        # Reset template config to avoid side effects
        resume_store.reset_template_config()

    def test_default_template_config(self):
        """Verifies default template configuration attributes."""
        cfg = TemplateConfig()
        self.assertEqual(cfg.template_id, "modern")
        self.assertEqual(cfg.primary_color, "#0284c7")
        self.assertEqual(cfg.density, "normal")
        self.assertEqual(cfg.header_layout, "left")
        self.assertTrue(cfg.show_tagline)
        self.assertTrue(cfg.show_projects)

    def test_template_config_persistence(self):
        """Verifies saving, retrieving, and resetting template config."""
        custom_cfg = TemplateConfig(
            template_id="cv_executive",
            primary_color="#059669",
            accent_color="#10b981",
            font_family="Merriweather, serif",
            density="compact",
            header_layout="center",
            show_tagline=False,
        )
        saved = resume_store.save_template_config(custom_cfg)
        self.assertEqual(saved.primary_color, "#059669")

        loaded = resume_store.get_template_config()
        self.assertEqual(loaded.template_id, "cv_executive")
        self.assertEqual(loaded.primary_color, "#059669")
        self.assertEqual(loaded.density, "compact")
        self.assertEqual(loaded.header_layout, "center")
        self.assertFalse(loaded.show_tagline)

        # Reset
        reset_cfg = resume_store.reset_template_config()
        self.assertEqual(reset_cfg.primary_color, "#0284c7")

    def test_dynamic_style_injection_in_renderer(self):
        """Verifies template_engine.render applies custom styles dynamically."""
        cfg = TemplateConfig(
            template_id="modern",
            primary_color="#dc2626",
            accent_color="#ef4444",
            text_color="#18181b",
            font_family="'JetBrains Mono', monospace",
            density="compact",
            header_layout="center",
            show_tagline=False,
        )
        html = template_engine.render(self.sample_resume, config=cfg)
        self.assertIn("--primary-color: #dc2626", html)
        self.assertIn("--font-family: 'JetBrains Mono', monospace", html)
        self.assertIn("padding: 28px 36px", html)
        self.assertIn("text-align: center", html)
        self.assertNotIn("• Enterprise Architecture • Cloud Systems", html)

    def test_asgi_template_config_endpoints(self):
        """Verifies GET and PUT /api/template/config via ASGI."""
        async def run():
            # 1. GET initial config
            received = []
            async def send(msg):
                received.append(msg)
            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            scope_get = {
                "type": "http",
                "method": "GET",
                "path": "/api/template/config",
                "headers": [],
            }
            await app(scope_get, receive, send)
            start_msg = next(m for m in received if m["type"] == "http.response.start")
            body_msg = next(m for m in received if m["type"] == "http.response.body")
            self.assertEqual(start_msg["status"], 200)
            initial_data = json.loads(body_msg["body"].decode("utf-8"))
            self.assertIn("primary_color", initial_data)

            # 2. PUT updated config
            received.clear()
            put_payload = json.dumps({
                "template_id": "executive",
                "primary_color": "#7c3aed",
                "density": "comfortable",
                "header_layout": "split",
            }).encode("utf-8")
            async def receive_put():
                return {"type": "http.request", "body": put_payload, "more_body": False}

            scope_put = {
                "type": "http",
                "method": "PUT",
                "path": "/api/template/config",
                "headers": [(b"content-type", b"application/json")],
            }
            await app(scope_put, receive_put, send)
            start_msg_put = next(m for m in received if m["type"] == "http.response.start")
            body_msg_put = next(m for m in received if m["type"] == "http.response.body")
            self.assertEqual(start_msg_put["status"], 200)
            updated_data = json.loads(body_msg_put["body"].decode("utf-8"))
            self.assertEqual(updated_data["primary_color"], "#7c3aed")
            self.assertEqual(updated_data["density"], "comfortable")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
