import unittest
from backend.app.models.resume import ResumeData, TemplateConfig
from backend.app.services.template_engine import template_engine
from backend.app.services.resume_store import resume_store


class TestTemplateCustomizer(unittest.TestCase):
    def setUp(self):
        self.resume = resume_store.get_base_resume()

    def test_custom_colors_applied(self):
        cfg = TemplateConfig(
            template_id="modern",
            primary_color="#dc2626",
            accent_color="#059669",
            text_color="#18181b",
        )
        html = template_engine.render(self.resume, template_id="modern", config=cfg)
        self.assertIn("#dc2626", html)
        self.assertIn("#059669", html)
        self.assertIn("#18181b", html)

    def test_custom_typography_applied(self):
        cfg = TemplateConfig(
            template_id="executive",
            font_family="Merriweather, Georgia, serif",
            font_size="14.5px",
            line_height="1.6",
        )
        html = template_engine.render(self.resume, template_id="executive", config=cfg)
        self.assertIn("Merriweather, Georgia, serif", html)
        self.assertIn("14.5px", html)
        self.assertIn("1.6", html)

    def test_density_padding_applied(self):
        cfg_compact = TemplateConfig(
            template_id="compact",
            density="compact",
        )
        html_compact = template_engine.render(self.resume, template_id="compact", config=cfg_compact)
        self.assertIn("28px 36px", html_compact)

        cfg_spacious = TemplateConfig(
            template_id="modern",
            density="comfortable",
        )
        html_spacious = template_engine.render(self.resume, template_id="modern", config=cfg_spacious)
        self.assertIn("54px 58px", html_spacious)

    def test_section_visibility_toggles(self):
        cfg_no_projects = TemplateConfig(
            template_id="modern",
            show_projects=False,
            show_education=False,
            show_tagline=False,
        )
        html = template_engine.render(self.resume, template_id="modern", config=cfg_no_projects)
        self.assertNotIn("Key Projects & Architecture", html)
        self.assertNotIn('<div class="section-title">Education</div>', html)

    def test_header_layout_options(self):
        for layout in ["left", "center", "split"]:
            cfg = TemplateConfig(header_layout=layout)
            html = template_engine.render(self.resume, template_id="modern", config=cfg)
            if layout == "center":
                self.assertIn("text-align: center !important", html)
            elif layout == "split":
                self.assertIn("justify-content: space-between !important", html)
            elif layout == "left":
                self.assertIn("text-align: left !important", html)

    def test_explicit_template_override_in_cv_mode(self):
        cv_resume = self.resume.model_copy()
        cv_resume.document_type = "cv"
        # Explicit modern template request with config
        cfg = TemplateConfig(template_id="modern")
        html = template_engine.render(cv_resume, template_id="modern", config=cfg)
        # Modern tech should be rendered, not CV executive
        self.assertIn("Technical Competencies", html)


if __name__ == "__main__":
    unittest.main()
