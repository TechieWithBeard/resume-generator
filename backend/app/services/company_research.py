"""
LangChain-Powered Company Web Research Tool.
Researches target companies via Wikipedia REST API and DuckDuckGo Instant Answer API,
with intelligent fallback to job specification extraction and domain heuristics.
Subclasses langchain_core.tools.BaseTool.
"""

import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class CompanyResearchInput(BaseModel):
    company_name: str = Field(
        description="The name of the target company to research, e.g. 'Siemens Healthineers' or 'Rentman'."
    )
    job_context: Optional[str] = Field(
        default=None,
        description="Optional job description text to extract company insights from if offline or web lookup is blocked.",
    )


class CompanyResearchTool(BaseTool):
    """LangChain BaseTool that retrieves company background, mission, culture, and technical focus."""

    name: str = "company_research_tool"
    description: str = (
        "Researches a company's mission, engineering culture, core products, and technological focus "
        "using web search APIs with intelligent fallback to job specification deconstruction. "
        "Returns a structured intelligence briefing."
    )
    args_schema: Type[BaseModel] = CompanyResearchInput

    def _clean_company_name(self, name: str) -> str:
        """Strips legal entity suffixes to produce clean query search terms."""
        if not name:
            return ""
        # Handle dotted and compound suffixes
        cleaned = re.sub(r"(?i)\b(b\.v\.|pvt\.?\s*ltd\.?)", "", name)
        cleaned = re.sub(
            r"(?i)\b(inc|llc|ltd|bv|gmbh|co|corp|corporation|technologies|solutions|group|holdings|pvt|plc)\b\.?",
            "",
            cleaned,
        )
        cleaned = re.sub(r"[\s,\-\.]+", " ", cleaned).strip()
        return cleaned or name.strip()

    def _fetch_wikipedia(self, company_name: str) -> Optional[Dict[str, str]]:
        """Queries the Wikipedia REST summary API."""
        try:
            clean_name = self._clean_company_name(company_name)
            encoded = urllib.parse.quote(clean_name.replace(" ", "_"))
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ResumeGeneratorAgent/1.0 (company-research-tool)"},
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                extract = data.get("extract", "").strip()
                description = data.get("description", "").strip()
                if extract and len(extract) > 40:
                    return {
                        "extract": extract,
                        "description": description,
                        "source": "web_wikipedia",
                    }
        except Exception:
            pass
        return None

    def _fetch_duckduckgo(self, company_name: str) -> Optional[Dict[str, str]]:
        """Queries DuckDuckGo Instant Answer API."""
        try:
            clean_name = self._clean_company_name(company_name)
            encoded = urllib.parse.quote_plus(clean_name)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ResumeGeneratorAgent/1.0 (company-research-tool)"},
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                abstract = data.get("AbstractText", "").strip()
                heading = data.get("Heading", "").strip()
                if abstract and len(abstract) > 40:
                    return {
                        "extract": abstract,
                        "description": heading,
                        "source": "web_duckduckgo",
                    }
        except Exception:
            pass
        return None

    def _extract_from_job_context(self, company_name: str, job_context: str) -> Dict[str, Any]:
        """
        Parses the posted job description for company background, mission,
        team culture, and technical stack when web search is inaccessible or offline.
        """
        if not job_context:
            return {}

        about_snippets: List[str] = []
        culture_snippets: List[str] = []
        tech_snippets: List[str] = []

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", job_context) if p.strip()]

        for p in paragraphs:
            lower_p = p.lower()
            # Look for "About Us", "Who We Are", "Our Mission", company intro
            if any(marker in lower_p for marker in [
                "about us", "who we are", "our mission", "what we do", "about ",
                "company overview", "at our core", "we are building", "we are a"
            ]):
                clean_p = " ".join(p.split())
                if len(clean_p) > 30 and len(clean_p) < 400:
                    about_snippets.append(clean_p)

            # Look for culture and values
            if any(marker in lower_p for marker in [
                "culture", "values", "collaborative", "diversity", "innovation",
                "ownership", "agile", "our team", "we believe"
            ]):
                clean_p = " ".join(p.split())
                if len(clean_p) > 30 and len(clean_p) < 300:
                    culture_snippets.append(clean_p)

            # Look for technical stack / architectural challenges
            if any(marker in lower_p for marker in [
                "tech stack", "our stack", "technologies", "architecture", "microservices",
                "scalable", "cloud", "you will work with", "our platform"
            ]):
                clean_p = " ".join(p.split())
                if len(clean_p) > 30 and len(clean_p) < 300:
                    tech_snippets.append(clean_p)

        # Extract domain hints
        domain_hints = []
        lower_all = job_context.lower()
        if any(w in lower_all for w in ["health", "medtech", "clinical", "hospital", "patient"]):
            domain_hints.append("digital healthcare & medical technology")
        if any(w in lower_all for w in ["fintech", "payment", "banking", "trading", "financial"]):
            domain_hints.append("financial technology & transaction systems")
        if any(w in lower_all for w in ["saas", "b2b", "enterprise", "cloud platform"]):
            domain_hints.append("enterprise B2B cloud SaaS")
        if any(w in lower_all for w in ["event", "rental", "logistics", "supply chain"]):
            domain_hints.append("resource management & operational workflow software")
        if any(w in lower_all for w in ["ai", "machine learning", "neural", "deep learning"]):
            domain_hints.append("AI-driven intelligent automation")

        return {
            "about": about_snippets[0] if about_snippets else "",
            "culture": culture_snippets[0] if culture_snippets else "",
            "tech": tech_snippets[0] if tech_snippets else "",
            "domain_hint": ", ".join(domain_hints) if domain_hints else "modern high-impact software solutions",
        }

    def _synthesize(
        self,
        company_name: str,
        web_info: Optional[Dict[str, str]],
        context_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Synthesizes web research and contextual signals into a cohesive intelligence brief."""
        name = self._clean_company_name(company_name) or (company_name.strip() if company_name else "the Organization")
        source = web_info.get("source") if web_info else "job_specification_extraction"

        if web_info and web_info.get("extract"):
            extract = web_info["extract"]
            # Extract first 1-2 sentences for mission
            sentences = re.split(r"(?<=[.!?])\s+", extract)
            mission = " ".join(sentences[:2]).strip()
            summary = extract[:350] + ("..." if len(extract) > 350 else "")
            culture = (
                f"Engineering culture recognized for driving scalable innovation, high product quality, "
                f"and technical rigor within {context_info.get('domain_hint', 'the industry')}."
            )
            tech_focus = (
                f"Architectural focus on high-reliability distributed systems, modern reactive architectures, "
                f"and domain excellence in {context_info.get('domain_hint', 'enterprise software')}."
            )
        elif context_info.get("about"):
            about = context_info["about"]
            mission = about
            summary = f"{name} is dedicated to {context_info.get('domain_hint', 'delivering innovative products')}. {about}"
            culture = (
                context_info.get("culture")
                or f"Collaborative engineering culture valuing architectural autonomy, high quality, and proactive ownership."
            )
            tech_focus = (
                context_info.get("tech")
                or f"Modern scalable systems, resilient frontend architectures, and data-driven solutions."
            )
        else:
            domain = context_info.get("domain_hint", "enterprise modern software")
            mission = f"Delivering mission-critical, high-impact innovations in {domain}."
            culture = "Fast-paced, product-minded engineering culture emphasizing architectural clarity, clean code, and continuous learning."
            tech_focus = "Modern cloud architectures, component-driven reactive web platforms, and scalable engineering practices."
            summary = (
                f"{name} is recognized for building impactful products in {domain}. "
                f"The organization champions forward-thinking engineering, operational excellence, and high customer impact."
            )

        return {
            "company_name": name,
            "mission": mission,
            "culture": culture,
            "tech_focus": tech_focus,
            "summary": summary,
            "source": source,
        }

    def _run(self, company_name: str, job_context: Optional[str] = None) -> Dict[str, Any]:
        """Executes company research using web endpoints with fallback to job context analysis."""
        company_name = company_name or ""
        job_context = job_context or ""

        # Step 1: Attempt web lookup if company name is available
        web_info = None
        if company_name and len(company_name.strip()) > 1:
            web_info = self._fetch_wikipedia(company_name)
            if not web_info:
                web_info = self._fetch_duckduckgo(company_name)

        # Step 2: Contextual analysis of job description
        context_info = self._extract_from_job_context(company_name, job_context)

        # Step 3: Synthesize intelligence
        return self._synthesize(company_name, web_info, context_info)

    async def _arun(self, company_name: str, job_context: Optional[str] = None) -> Dict[str, Any]:
        """Asynchronous execution of the research tool."""
        return self._run(company_name, job_context)


# Global reusable instance
company_research_tool = CompanyResearchTool()
