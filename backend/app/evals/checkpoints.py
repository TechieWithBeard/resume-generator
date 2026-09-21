"""
Evaluation Checkpoints for Resume & CV Tailoring Pipeline.
Implements deterministic, zero-hallucination verification rules, noise elimination,
competency alignment, and ATS formatting audits.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.models.resume import AlignmentReport, ResumeData
from backend.app.evals.models import CheckpointResult, EvalCase


RECRUITMENT_NOISE_MARKERS = [
    "recruitment process",
    "our process",
    "hiring process",
    "interview",
    "recruiter",
    "screening",
    "assessment",
    "call with",
    "(30 mins)",
    "(60 mins)",
    "(90 mins)",
    "equal opportunity",
    "affirmative action",
    "eeo",
    "perks",
    "vacation days",
    "holiday",
    "pension",
    "how to apply",
    "submit your application",
    "background check",
    "at our office",
    "breakdown of our",
]


class TruthInvarianceCheckpoint:
    """
    Checkpoint 1: Truth Invariance (Zero-Hallucination Gate).
    Validates that the generated profile does not fabricate employers,
    degrees, academic institutions, dates, or personal identity.
    """

    @classmethod
    def evaluate(
        cls,
        base_resume: ResumeData,
        tailored_resume: ResumeData,
        eval_case: EvalCase,
    ) -> CheckpointResult:
        violations = []
        base_companies = {e.company.strip().lower() for e in base_resume.experience}
        base_degrees = {e.degree.strip().lower() for e in base_resume.education}
        base_institutions = {e.institution.strip().lower() for e in base_resume.education}
        base_periods = {e.period.strip().lower() for e in base_resume.experience}

        # 1. Employer Invariance Check
        for exp in tailored_resume.experience:
            c_norm = exp.company.strip().lower()
            # Allow matching if base company name is contained (e.g. client qualification)
            matched = any(
                c_norm == bc or bc in c_norm or c_norm in bc
                for bc in base_companies
            )
            if not matched:
                violations.append(f"Fabricated employer detected: '{exp.company}'")

        # 2. Education Invariance Check
        for edu in tailored_resume.education:
            d_norm = edu.degree.strip().lower()
            i_norm = edu.institution.strip().lower()
            if not any(d_norm == bd or bd in d_norm for bd in base_degrees):
                violations.append(f"Fabricated degree detected: '{edu.degree}'")
            if not any(i_norm == bi or bi in i_norm for bi in base_institutions):
                violations.append(f"Fabricated educational institution detected: '{edu.institution}'")

        # 3. Timeline / Period Invariance Check
        for exp in tailored_resume.experience:
            p_norm = exp.period.strip().lower()
            if not any(p_norm == bp for bp in base_periods):
                violations.append(f"Altered employment period detected for {exp.company}: '{exp.period}'")

        # 4. Identity Invariance Check
        if tailored_resume.name.strip().lower() != base_resume.name.strip().lower():
            violations.append(f"Candidate name mismatch: '{tailored_resume.name}' vs '{base_resume.name}'")

        # 5. Skills Non-Fabrication Check (Zero Hallucinated Technologies)
        base_verified_corpus = set()
        for cat_skills in (base_resume.skills or {}).values():
            for s in cat_skills:
                base_verified_corpus.add(s.strip().lower())
                for sub in re.split(r"[/,()&|•]+", s):
                    sub_clean = sub.strip().lower()
                    if sub_clean:
                        base_verified_corpus.add(sub_clean)

        for exp in base_resume.experience:
            for h in exp.highlights:
                base_verified_corpus.add(h.strip().lower())
            for t in getattr(exp, "technologies", []) or []:
                base_verified_corpus.add(t.strip().lower())
        for p in (base_resume.projects or []):
            base_verified_corpus.add(p.name.strip().lower())
            for t in (p.technologies or []):
                base_verified_corpus.add(t.strip().lower())
        for c in (base_resume.certifications or []):
            base_verified_corpus.add(c.name.strip().lower())

        base_raw_low = (
            (base_resume.raw_text or "") + " " +
            (base_resume.summary or "") + " " +
            " ".join(base_verified_corpus)
        ).lower()

        fabricated_skills = []
        for cat, s_list in (tailored_resume.skills or {}).items():
            for s in s_list:
                s_low = s.strip().lower()
                is_grounded = (
                    s_low in base_verified_corpus or
                    bool(re.search(rf"\b{re.escape(s_low)}\b", base_raw_low))
                )
                if not is_grounded:
                    fabricated_skills.append(s)

        if fabricated_skills:
            violations.append(f"Fabricated skill(s) detected not present in base resume: {fabricated_skills}")

        passed = len(violations) == 0
        score = 1.0 if passed else max(0.0, 1.0 - (0.35 * len(violations)))
        msg = "All ground-truth employers, degrees, timelines, skills, and identity verified 100% invariant." if passed else f"Truth Invariance violated with {len(violations)} defect(s)."

        return CheckpointResult(
            checkpoint_name="Truth Invariance Checkpoint",
            category="truth_invariance",
            passed=passed,
            score=round(score, 3),
            threshold=1.0,
            message=msg,
            details={
                "violations": violations,
                "verified_companies": list(base_companies),
                "fabricated_skills": fabricated_skills,
            },
        )


class NoiseEliminationCheckpoint:
    """
    Checkpoint 2: Recruitment & Administrative Noise Elimination Gate.
    Verifies that zero internal hiring stages, interview lengths, perks,
    or administrative boilerplate leak into candidate-facing text.
    """

    @classmethod
    def evaluate(
        cls,
        tailored_resume: ResumeData,
        rendered_html: str,
        eval_case: EvalCase,
    ) -> CheckpointResult:
        leaks = []

        # Texts to scan
        text_corpus = [
            tailored_resume.summary or "",
            tailored_resume.why_company or "",
            tailored_resume.why_fit or "",
        ]
        for exp in tailored_resume.experience:
            text_corpus.extend(exp.highlights)
        for proj in tailored_resume.projects:
            text_corpus.append(proj.description)

        combined_text = " ".join(text_corpus).lower()

        # Check standard recruitment noise markers
        for marker in RECRUITMENT_NOISE_MARKERS:
            if marker in combined_text:
                leaks.append(f"Recruitment noise marker found in text: '{marker}'")

        # Check case-specific forbidden terms
        for forbidden in eval_case.forbidden_terms:
            if forbidden.lower() in combined_text or forbidden.lower() in rendered_html.lower():
                leaks.append(f"Forbidden term detected: '{forbidden}'")

        passed = len(leaks) == 0
        score = 1.0 if passed else max(0.0, 1.0 - (0.30 * len(leaks)))
        msg = "Zero recruitment process leakage or forbidden terms detected." if passed else f"Noise elimination failed: {len(leaks)} leaked term(s)."

        return CheckpointResult(
            checkpoint_name="Noise Elimination Checkpoint",
            category="noise_elimination",
            passed=passed,
            score=round(score, 3),
            threshold=1.0,
            message=msg,
            details={"leaks": leaks},
        )


class CompetencyAlignmentCheckpoint:
    """
    Checkpoint 3: Competency & Target Role Alignment Gate.
    Audits keyword matching, alignment score, and role-specific relevance.
    """

    @classmethod
    def evaluate(
        cls,
        tailored_resume: ResumeData,
        audit_report: Optional[AlignmentReport],
        eval_case: EvalCase,
    ) -> CheckpointResult:
        score_details = {}
        target_role = getattr(tailored_resume, "target_role", None) or eval_case.job_input.target_title or ""

        # 1. Match score check
        calc_score = audit_report.match_score if audit_report else 70
        score_details["audit_match_score"] = calc_score
        score_details["minimum_required"] = eval_case.minimum_match_score
        match_passed = calc_score >= eval_case.minimum_match_score

        # 2. Required keywords presence check
        matched_kws = []
        missing_kws = []
        proj_text = " ".join([
            (p.name or "") + " " + (p.description or "") + " " + " ".join(p.technologies)
            for p in getattr(tailored_resume, "projects", [])
        ])
        all_text = (
            (tailored_resume.summary or "") + " " +
            (tailored_resume.why_company or "") + " " +
            (tailored_resume.why_fit or "") + " " +
            " ".join(sum(tailored_resume.skills.values(), [])) + " " +
            " ".join([h for e in tailored_resume.experience for h in e.highlights]) + " " +
            proj_text
        ).lower()

        for kw in eval_case.required_keywords:
            if kw.lower() in all_text:
                matched_kws.append(kw)
            else:
                missing_kws.append(kw)

        kw_coverage = len(matched_kws) / len(eval_case.required_keywords) if eval_case.required_keywords else 1.0
        score_details["keyword_coverage"] = round(kw_coverage, 2)
        score_details["matched_keywords"] = matched_kws
        score_details["missing_keywords"] = missing_kws

        # 3. Composite alignment calculation
        normalized_match = min(1.0, calc_score / 100.0)
        composite = (0.55 * normalized_match) + (0.45 * kw_coverage)
        min_normalized = min(1.0, eval_case.minimum_match_score / 100.0)
        threshold = max(0.40, min(0.70, (0.55 * min_normalized) + 0.30))

        passed = match_passed and (composite >= threshold or len(eval_case.required_keywords) == 0)
        msg = (
            f"Competency alignment passed: {calc_score}% match score, "
            f"{len(matched_kws)}/{len(eval_case.required_keywords)} key terms covered."
            if passed
            else f"Competency alignment deficient: {calc_score}% score (min {eval_case.minimum_match_score}%), kw coverage {round(kw_coverage*100)}%."
        )

        return CheckpointResult(
            checkpoint_name="Competency Alignment Checkpoint",
            category="competency_alignment",
            passed=passed,
            score=round(composite, 3),
            threshold=threshold,
            message=msg,
            details=score_details,
        )


class AtsFormattingCheckpoint:
    """
    Checkpoint 4: ATS & Template Formatting Gate.
    Verifies semantic structure, divider architecture, scannable inline categorized skills,
    left-aligned prose, and print CSS compliance.
    """

    @classmethod
    def evaluate(
        cls,
        tailored_resume: ResumeData,
        rendered_html: str,
        eval_case: EvalCase,
    ) -> CheckpointResult:
        defects = []

        # 1. Document Structure & Required Sections
        if eval_case.document_type == "cv":
            required_checks = [
                ("Strategic Motivation", ["strategic motivation"]),
                ("Executive Value Proposition", ["executive value proposition"]),
                ("Architectural Wins", ["architectural wins"]),
            ]
        else:
            required_checks = [
                ("Professional Experience", ["professional experience", "experience"]),
                ("Education", ["education"]),
            ]

        for sec_name, keywords in required_checks:
            if not any(kw in rendered_html.lower() for kw in keywords):
                defects.append(f"Missing required section: '{sec_name}'")

        # 2. ATS Inline Skills Architecture Check
        # Ensures skills are rendered in clean categorized rows or high-density skill pills
        has_skill_row = (
            'class="skill-row"' in rendered_html or
            'class="skill-group"' in rendered_html or
            'class="skill-pill"' in rendered_html or
            'class="skills-pill-grid"' in rendered_html or
            '<strong>' in rendered_html
        )
        if not has_skill_row and tailored_resume.skills:
            defects.append("Skills section missing semantic categorized row layout")

        # 3. Divider Architecture Check
        has_section_divider = (
            "border-bottom:" in rendered_html or
            "border-bottom-color:" in rendered_html or
            "sec-heading" in rendered_html
        )
        if not has_section_divider:
            defects.append("Missing crisp horizontal section dividers in CSS")

        has_entry_divider = (
            "experience-entry" in rendered_html or
            "padding-bottom:" in rendered_html
        )
        if not has_entry_divider:
            defects.append("Missing experience entry structure in template HTML")

        # 4. Typography & Readability Check (no text-align: justify)
        # Note: Summary in modern template should be left-aligned
        if 'summary-text" style="text-align: justify;' in rendered_html:
            defects.append("Summary uses disruptive 'text-align: justify' rather than scannable left-aligned typography")

        # 5. Print & PDF Compliance Check
        if "@media print" not in rendered_html:
            defects.append("Missing '@media print' stylesheet for clean PDF generation")
        if "@page" not in rendered_html and "cv_executive" not in eval_case.template_id:
            defects.append("Missing '@page' print margin definition")

        # 6. Integrate 9-Dimension Quality Score Audit
        quality_audit = {}
        try:
            from backend.app.services.resume_score_checker import resume_score_checker
            quality_audit = resume_score_checker.audit(
                tailored_resume,
                rendered_html=rendered_html,
                target_role=eval_case.job_input.target_title,
                job_description=eval_case.job_input.job_description,
            )
        except Exception as e:
            quality_audit = {"error": str(e)}

        passed = len(defects) == 0
        score = 1.0 if passed else max(0.0, 1.0 - (0.25 * len(defects)))
        msg = "ATS formatting and visual divider architecture 100% compliant." if passed else f"ATS formatting defects found: {len(defects)} issue(s)."

        return CheckpointResult(
            checkpoint_name="ATS & Template Formatting Checkpoint",
            category="ats_formatting",
            passed=passed,
            score=round(score, 3),
            threshold=1.0,
            message=msg,
            details={"defects": defects, "quality_audit": quality_audit},
        )


class CompanyResearchCheckpoint:
    """
    Checkpoint 5: Company Intelligence & Research Quality Gate.
    Verifies that company mission, domain focus, and culture are authentically
    retrieved without HR boilerplate.
    """

    @classmethod
    def evaluate(
        cls,
        tailored_resume: ResumeData,
        eval_case: EvalCase,
    ) -> CheckpointResult:
        research = getattr(tailored_resume, "company_research", None) or {}
        issues = []

        if eval_case.document_type == "cv":
            # For CV mode, company research is expected
            c_name = research.get("company_name", "") or getattr(tailored_resume, "target_company", "")
            mission = research.get("mission", "")
            culture = research.get("culture", "")
            why_company = getattr(tailored_resume, "why_company", "")
            why_fit = getattr(tailored_resume, "why_fit", "")

            if not c_name:
                issues.append("Target company name missing from research dossier")
            if not mission or len(mission) < 15:
                issues.append("Strategic company mission empty or insufficient")
            if not culture or len(culture) < 10:
                issues.append("Engineering culture empty or insufficient")
            if not why_company or len(why_company) < 40:
                issues.append("Strategic motivation ('Why Company') paragraph empty or insufficient")
            if not why_fit or len(why_fit) < 40:
                issues.append("Executive value proposition ('Why Fit') paragraph empty or insufficient")

            # Check noise in research
            for marker in RECRUITMENT_NOISE_MARKERS:
                if marker in mission.lower() or marker in culture.lower():
                    issues.append(f"Company research contains recruitment noise: '{marker}'")

            passed = len(issues) == 0
            score = 1.0 if passed else max(0.0, 1.0 - (0.20 * len(issues)))
            msg = "Company intelligence & executive alignment verified authentic." if passed else f"Research quality issues: {len(issues)} defect(s)."
        else:
            # For regular resume mode, research is optional/non-blocking
            passed = True
            score = 1.0
            msg = "Standard resume mode: Company research checkpoint satisfied."

        return CheckpointResult(
            checkpoint_name="Company Research Intelligence Checkpoint",
            category="research_intelligence",
            passed=passed,
            score=round(score, 3),
            threshold=0.85,
            message=msg,
            details={"issues": issues, "research_summary": {k: str(v)[:100] for k, v in research.items()}},
        )
