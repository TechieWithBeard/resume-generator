"""
Data models for the AI-Powered Resume Generator.
Strict Pydantic models for validation, serialization, and typing.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Availability(BaseModel):
    status: Optional[str] = None
    target: Optional[str] = None
    note: Optional[str] = None


class ExperienceItem(BaseModel):
    role: str
    company: str
    period: str
    location: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    scope: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: str
    institution: str
    period: str


class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    period: Optional[str] = None
    url: Optional[str] = None


class CertificationItem(BaseModel):
    name: str
    issuer: str
    year: Optional[str] = None
    date: Optional[str] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None


class ResumeData(BaseModel):
    name: str
    title: str
    tagline: Optional[str] = ""
    location: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    portfolio: Optional[str] = ""
    summary: str
    availability: Optional[Availability] = None
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    skills: Dict[str, List[str]] = Field(default_factory=dict)
    projects: List[ProjectItem] = Field(default_factory=list)

    @field_validator("skills", mode="before")
    @classmethod
    def normalize_skills(cls, v: Any) -> Dict[str, List[str]]:
        if not v:
            return {}
        if isinstance(v, list):
            clean_list = [str(item).strip() for item in v if item]
            return {"Technical Skills": clean_list}
        if isinstance(v, dict):
            normalized = {}
            for cat, items in v.items():
                if isinstance(items, list):
                    normalized[cat] = [str(i).strip() for i in items if i]
                elif isinstance(items, str):
                    normalized[cat] = [i.strip() for i in items.split(",") if i.strip()]
                elif items is not None:
                    normalized[cat] = [str(items).strip()]
            return normalized
        if isinstance(v, str):
            clean_list = [s.strip() for s in v.split(",") if s.strip()]
            return {"Technical Skills": clean_list}
        return {}
    certifications: List[CertificationItem] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)
    document_type: Literal["resume", "cv"] = "resume"
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    why_company: Optional[str] = ""
    why_fit: Optional[str] = ""
    company_research: Optional[Dict[str, Any]] = None
    raw_text: Optional[str] = ""
    additional_sections: Dict[str, Any] = Field(default_factory=dict)



class JobInput(BaseModel):
    job_description: Optional[str] = None
    linkedin_url: Optional[str] = None
    target_title: Optional[str] = None
    document_type: Literal["resume", "cv"] = "resume"
    human_guidance: Optional[Dict[str, Any]] = None


class LLMConfig(BaseModel):
    provider: Literal["auto", "ollama", "openai", "huggingface", "heuristic"] = "auto"
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = "http://localhost:11434"
    temperature: float = 0.2


class AlignmentAuditItem(BaseModel):
    check: str
    status: Literal["PASSED", "WARNING", "FAILED"]
    details: str


class AlignmentReport(BaseModel):
    match_score: int = Field(ge=0, le=100)
    is_low_match: bool = False
    target_role: str
    direct_matches: List[str] = Field(default_factory=list)
    transferable_skills: List[str] = Field(default_factory=list)
    unmatched_skills: List[str] = Field(default_factory=list)
    alignment_strategy: str = "Aligned with target role specifications."
    anti_hallucination_audit: List[AlignmentAuditItem] = Field(default_factory=list)
    overall_status: Literal["PASSED", "REJECTED"] = "PASSED"


class PreflightReport(BaseModel):
    match_score: int = Field(ge=0, le=100)
    is_low_match: bool = False
    target_role: str = ""
    direct_matches: List[str] = Field(default_factory=list)
    unmatched_skills: List[str] = Field(default_factory=list)
    transferable_skills: List[str] = Field(default_factory=list)
    message: str = ""


class TemplateConfig(BaseModel):
    template_id: str = "modern"
    primary_color: str = "#0284c7"
    accent_color: str = "#0284c7"
    text_color: str = "#1e293b"
    font_family: str = "system-ui, -apple-system, sans-serif"
    font_size: str = "11.5px"
    line_height: str = "1.36"
    density: Literal["compact", "normal", "comfortable"] = "normal"
    header_layout: Literal["left", "center", "split"] = "left"
    show_tagline: bool = True
    show_icons: bool = True
    show_projects: bool = True
    show_certifications: bool = True
    show_education: bool = True
    custom_css: Optional[str] = ""


class StreamRequest(BaseModel):
    job_input: JobInput
    llm_config: Optional[LLMConfig] = Field(default_factory=LLMConfig)
    base_resume: Optional[ResumeData] = None
    template_id: Optional[str] = "modern"
    template_config: Optional[TemplateConfig] = None


class RenderRequest(BaseModel):
    resume: ResumeData
    template_id: str = "modern"
    highlight_diff: bool = False
    base_resume: Optional[ResumeData] = None
    template_config: Optional[TemplateConfig] = None
