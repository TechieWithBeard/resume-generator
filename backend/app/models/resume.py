"""
Data models for the AI-Powered Resume Generator.
Strict Pydantic models for validation, serialization, and typing.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


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
    summary: str
    availability: Optional[Availability] = None
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    skills: Dict[str, List[str]] = Field(default_factory=dict)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)
    document_type: Literal["resume", "cv"] = "resume"


class JobInput(BaseModel):
    job_description: Optional[str] = None
    linkedin_url: Optional[str] = None
    target_title: Optional[str] = None
    document_type: Literal["resume", "cv"] = "resume"


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
    target_role: str
    direct_matches: List[str] = Field(default_factory=list)
    transferable_skills: List[str] = Field(default_factory=list)
    unmatched_skills: List[str] = Field(default_factory=list)
    alignment_strategy: str
    anti_hallucination_audit: List[AlignmentAuditItem] = Field(default_factory=list)
    overall_status: Literal["PASSED", "REJECTED"] = "PASSED"


class StreamRequest(BaseModel):
    job_input: JobInput
    llm_config: Optional[LLMConfig] = Field(default_factory=LLMConfig)
    base_resume: Optional[ResumeData] = None
    template_id: Optional[str] = "modern"


class RenderRequest(BaseModel):
    resume: ResumeData
    template_id: str = "modern"
    highlight_diff: bool = False
    base_resume: Optional[ResumeData] = None
