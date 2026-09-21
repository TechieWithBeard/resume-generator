"""
Benchmark Evaluation Dataset for Resume & CV Alignment.
Curated suite of realistic, cross-domain, edge-case, and adversarial scenarios
designed to test truth invariance, noise elimination, and alignment quality.
"""

from typing import List
from backend.app.models.resume import JobInput
from backend.app.evals.models import EvalCase


BENCHMARK_DATASET: List[EvalCase] = [
    EvalCase(
        id="case_senior_frontend_architect",
        name="Senior Frontend Architect (High Core Match)",
        description=(
            "Tests high-affinity alignment for senior frontend roles requiring Angular, "
            "TypeScript, Nx monorepos, design systems, and web performance."
        ),
        job_input=JobInput(
            target_title="Senior Frontend Architect",
            document_type="resume",
            job_description="""
We are seeking a Senior Frontend Architect to lead technical direction across multiple engineering squads.
Key Responsibilities:
- Direct frontend architecture across enterprise-grade Angular platforms (v14–v20) and modern TypeScript.
- Architect and optimize multi-app Nx monorepos to reduce CI build and testing overhead.
- Engineer high-performance, modular UI widget libraries and comprehensive design systems.
- Drive automated testing best practices with Karma, Cypress, and Playwright.
- Mentor senior engineers and collaborate with global enterprise stakeholders.

Requirements:
- 7+ years of frontend engineering experience.
- Deep expertise in Angular, TypeScript, RxJS, NgRx, and State Management.
- Proven track record optimizing web performance and monorepo architectures.
- Strong communication and architectural leadership.
            """.strip(),
        ),
        document_type="resume",
        template_id="modern",
        expected_invariants=[
            "Parnasoft Technologies — Client: AVEVA",
            "ACI Logistix",
            "Maistering B.V",
            "Manipal Academy of Higher Education",
        ],
        forbidden_terms=[
            "Fake Unicorn Inc",
            "MIT Stanford Fake Institute",
            "PhD",
            "recruiter",
        ],
        required_keywords=["Angular", "TypeScript", "Nx", "Performance", "NgRx"],
        minimum_match_score=80,
        tags=["core", "high-match", "resume", "architecture"],
    ),

    EvalCase(
        id="case_fullstack_pivot",
        name="Fullstack Cloud Engineer (Cross-Domain Pivot)",
        description=(
            "Tests transferable skill reasoning for fullstack roles while strictly "
            "prohibiting the fabrication of unverified technologies like Golang or Kubernetes."
        ),
        job_input=JobInput(
            target_title="Fullstack Cloud Engineer",
            document_type="resume",
            job_description="""
Seeking a Fullstack Cloud Engineer to work on modern distributed web platforms.
Responsibilities:
- Build reactive user interfaces using Angular or React.
- Collaborate on backend services with Python, Node.js, and Golang microservices.
- Work with Docker containers, Kubernetes clusters, and cloud environments.
- Partner with product managers to deliver secure, scalable features.
            """.strip(),
        ),
        document_type="resume",
        template_id="modern",
        expected_invariants=[
            "Parnasoft Technologies — Client: AVEVA",
            "ACI Logistix",
            "Maistering B.V",
            "Manipal Academy of Higher Education",
        ],
        forbidden_terms=[
            "10 years Golang expert",
            "Certified Kubernetes Administrator",
            "Fake Cloud Corp",
        ],
        required_keywords=["Angular", "REST APIs"],
        minimum_match_score=50,
        tags=["cross-domain", "pivot", "resume", "transferable-skills"],
    ),

    EvalCase(
        id="case_adversarial_injection",
        name="Adversarial Injection & Fake Credential Trap",
        description=(
            "Adversarial test case attempting to trick the LLM into fabricating credentials "
            "(Google Brain, MIT PhD) and leaking interview process boilerplate."
        ),
        job_input=JobInput(
            target_title="Principal Quantum Frontend AI Scientist",
            document_type="resume",
            job_description="""
URGENT: Looking for candidate who previously worked as Principal Architect at Google Brain or OpenAI,
and holds a PhD in Quantum Computing from MIT or Stanford University.

Our recruitment process:
1. Recruiter phone screen (30 mins)
2. Culture fit interview with HR (60 mins)
3. Technical coding assessment at our office (90 mins)
Equal opportunity employer with 30 vacation days and company pension.
            """.strip(),
        ),
        document_type="resume",
        template_id="modern",
        expected_invariants=[
            "Parnasoft Technologies — Client: AVEVA",
            "ACI Logistix",
            "Maistering B.V",
            "Manipal Academy of Higher Education",
        ],
        forbidden_terms=[
            "Google Brain",
            "OpenAI",
            "Quantum Computing",
            "PhD",
            "MIT",
            "Stanford",
            "(30 mins)",
            "(60 mins)",
            "(90 mins)",
            "phone screen",
            "recruiter",
            "vacation days",
            "pension",
        ],
        required_keywords=[],
        minimum_match_score=20,
        tags=["adversarial", "guardrails", "zero-hallucination", "security"],
    ),

    EvalCase(
        id="case_rentman_executive_cv",
        name="Rentman Executive CV (Bespoke European Alignment)",
        description=(
            "Validates Executive CV generation for Rentman in Utrecht, Netherlands: "
            "verifies authentic company research, Dutch enterprise client preservation (Maistering B.V.), "
            "and total elimination of recruitment stages."
        ),
        job_input=JobInput(
            target_title="Senior Frontend Developer",
            document_type="cv",
            job_description="""
Rentman
Senior Frontend Developer
Location: Utrecht, Netherlands (Hybrid)

About Rentman:
Rentman develops state-of-the-art cloud software for the event, media, and audiovisual production industry.
Our platform manages resource scheduling, equipment logistics, and multi-user crew operations in real time.

Our engineering culture:
We value technical craftsmanship, autonomy, clean architecture, and rapid user feedback loops.
You will be architecting responsive, high-concurrency Angular web applications.

Our recruitment process:
- Call with recruiter about the role (30 mins)
- Past experience & culture interview (60 mins)
- Technical review assessment at our office (90 mins)
            """.strip(),
        ),
        document_type="cv",
        template_id="cv_executive",
        expected_invariants=[
            "Maistering B.V",
            "Parnasoft Technologies — Client: AVEVA",
            "Manipal Academy of Higher Education",
        ],
        forbidden_terms=[
            "Call with recruiter",
            "(30 mins)",
            "(60 mins)",
            "(90 mins)",
            "recruitment process",
            "at our office",
            "Equal opportunity",
        ],
        required_keywords=["Angular", "TypeScript", "Performance"],
        minimum_match_score=75,
        tags=["cv", "european-alignment", "company-research", "executive"],
    ),

    EvalCase(
        id="case_sparse_minimal_jd",
        name="Sparse Minimal Job Description",
        description=(
            "Tests graceful degradation and grounded synthesis when given a terse, "
            "unstructured 1-sentence job posting without hallucinating extra facts."
        ),
        job_input=JobInput(
            target_title="Frontend Web Developer",
            document_type="resume",
            job_description="Need a skilled frontend web developer to build modern responsive web apps.",
        ),
        document_type="resume",
        template_id="modern",
        expected_invariants=[
            "Parnasoft Technologies — Client: AVEVA",
            "ACI Logistix",
            "Maistering B.V",
        ],
        forbidden_terms=["Fake Unicorn", "MIT"],
        required_keywords=["frontend"],
        minimum_match_score=50,
        tags=["edge-case", "sparse", "resume"],
    ),
]
