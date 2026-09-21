"""
Evaluation Data Models for Resume & CV Alignment Framework.
Defines strict schemas for benchmark cases, checkpoint results, and aggregate reports.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Set
from pydantic import BaseModel, Field

from backend.app.models.resume import JobInput, ResumeData


class CheckpointResult(BaseModel):
    """Result of an individual evaluation checkpoint."""
    checkpoint_name: str
    category: Literal[
        "truth_invariance",
        "noise_elimination",
        "competency_alignment",
        "ats_formatting",
        "research_intelligence",
    ]
    passed: bool
    score: float = Field(ge=0.0, le=1.0, description="Normalized score between 0.0 and 1.0")
    threshold: float = Field(ge=0.0, le=1.0, description="Minimum score required to pass")
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class EvalCase(BaseModel):
    """Specification of an evaluation benchmark scenario."""
    id: str
    name: str
    description: str
    job_input: JobInput
    document_type: Literal["resume", "cv"] = "resume"
    template_id: str = "modern"
    expected_invariants: List[str] = Field(
        default_factory=list,
        description="List of ground truth employers/entities that must remain invariant",
    )
    forbidden_terms: List[str] = Field(
        default_factory=list,
        description="Terms that must NOT appear in output (e.g. recruitment noise or fake degrees)",
    )
    required_keywords: List[str] = Field(
        default_factory=list,
        description="Target keywords that should be matched or recognized",
    )
    minimum_match_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Minimum competency match score expected",
    )
    tags: List[str] = Field(default_factory=list)


class EvalCaseResult(BaseModel):
    """Evaluation outcome for a single test case across all checkpoints."""
    case_id: str
    case_name: str
    document_type: str
    passed: bool
    composite_score: float = Field(ge=0.0, le=1.0)
    checkpoints: List[CheckpointResult] = Field(default_factory=list)
    latency_ms: float = 0.0
    generated_role: Optional[str] = None
    match_score: Optional[int] = None
    error: Optional[str] = None


class EvalSuiteReport(BaseModel):
    """Comprehensive aggregated report across an entire evaluation suite."""
    suite_name: str = "Resume & CV Zero-Hallucination Alignment Benchmark"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    pass_rate: float = 0.0
    average_score: float = 0.0
    category_scores: Dict[str, float] = Field(default_factory=dict)
    checkpoint_summary: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    case_results: List[EvalCaseResult] = Field(default_factory=list)
