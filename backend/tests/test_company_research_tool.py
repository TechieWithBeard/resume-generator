"""
Unit tests for the LangChain CompanyResearchTool and Bespoke CV features.
"""

import asyncio
import unittest
from langchain_core.tools import BaseTool

from backend.app.models.resume import ResumeData
from backend.app.services.company_research import (
    CompanyResearchTool,
    company_research_tool,
)


class TestCompanyResearchTool(unittest.TestCase):
    """Test suite for LangChain-powered Company Research Tool."""

    def test_tool_initialization_and_inheritance(self):
        """Verifies tool is an official LangChain BaseTool with proper metadata."""
        self.assertIsInstance(company_research_tool, BaseTool)
        self.assertEqual(company_research_tool.name, "company_research_tool")
        self.assertIn("mission", company_research_tool.description.lower())
        self.assertIn("company_name", company_research_tool.args)

    def test_clean_company_name(self):
        """Verifies corporate legal suffixes are stripped for clean search query terms."""
        tool = CompanyResearchTool()
        self.assertEqual(tool._clean_company_name("Rentman B.V."), "Rentman")
        self.assertEqual(tool._clean_company_name("Siemens Healthineers GmbH"), "Siemens Healthineers")
        self.assertEqual(tool._clean_company_name("Acme Corp."), "Acme")
        self.assertEqual(tool._clean_company_name("Cloud Systems LLC"), "Cloud Systems")

    def test_job_context_extraction_fallback(self):
        """Verifies extraction of mission, culture, and domain hints from posted job text."""
        tool = CompanyResearchTool()
        sample_jd = (
            "About us: We are Siemens Healthineers, pioneering breakthroughs in healthcare for everyone, everywhere.\n\n"
            "Our Culture: We foster an inclusive, collaborative engineering culture prioritizing architectural autonomy and patient safety.\n\n"
            "Our Tech Stack: Microservices, Angular 20, Signals, TypeScript, and Azure Cloud.\n\n"
            "We are seeking a Senior Frontend Architect."
        )

        result = tool.invoke({
            "company_name": "Siemens Healthineers GmbH",
            "job_context": sample_jd,
        })

        self.assertIsInstance(result, dict)
        self.assertIn("company_name", result)
        self.assertEqual(result["company_name"], "Siemens Healthineers")
        self.assertTrue(len(result["mission"]) > 10)
        self.assertTrue(len(result["culture"]) > 10)
        self.assertTrue(len(result["tech_focus"]) > 10)
        self.assertIn("summary", result)
        self.assertIn("healthcare", result["summary"].lower())

    def test_generic_fallback_when_empty_context(self):
        """Verifies graceful synthetic brief generation when offline and context is empty."""
        tool = CompanyResearchTool()
        result = tool.invoke({"company_name": "Acme Innovations", "job_context": ""})
        self.assertIsInstance(result, dict)
        self.assertEqual(result["company_name"], "Acme Innovations")
        self.assertTrue(len(result["mission"]) > 0)
        self.assertTrue(len(result["culture"]) > 0)
        self.assertTrue(len(result["summary"]) > 0)

    def test_async_ainvoke(self):
        """Verifies async ainvoke works correctly."""
        result = asyncio.run(company_research_tool.ainvoke({
            "company_name": "Rentman",
            "job_context": "About us: Rentman builds resource management software for the event industry.",
        }))
        self.assertIsInstance(result, dict)
        self.assertEqual(result["company_name"], "Rentman")

    def test_resume_data_model_cv_fields(self):
        """Verifies ResumeData supports why_company, why_fit, and company_research."""
        sample_cv = ResumeData(
            name="Jane Doe",
            title="Senior Frontend Architect",
            summary="Experienced architect.",
            document_type="cv",
            target_role="Lead Frontend Architect",
            target_company="Siemens Healthineers",
            why_company="I want to join Siemens Healthineers to drive medical innovations.",
            why_fit="I have 8+ years building enterprise healthcare applications.",
            company_research={"company_name": "Siemens Healthineers", "mission": "Healthcare breakthroughs"},
        )
        self.assertEqual(sample_cv.why_company, "I want to join Siemens Healthineers to drive medical innovations.")
        self.assertEqual(sample_cv.why_fit, "I have 8+ years building enterprise healthcare applications.")
        self.assertEqual(sample_cv.company_research["company_name"], "Siemens Healthineers")


if __name__ == "__main__":
    unittest.main()
