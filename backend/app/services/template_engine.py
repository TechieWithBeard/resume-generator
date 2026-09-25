"""
Predefined ATS-Optimized HTML Resume Templates & Renderer.
Includes:
- Modern Tech Template
- Executive Minimalist Template
- Compact Classic Template
Embedded print styles ensure pixel-perfect PDF export via browser print engine.
"""

import difflib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.app.models.resume import ResumeData, TemplateConfig, format_job_title


class TemplateEngine:
    TEMPLATES = [
        {
            "id": "modern",
            "name": "Modern Tech",
            "description": "Clean, contemporary design with accent styling, skill badges, and balanced typography.",
            "is_default": True,
        },
        {
            "id": "executive",
            "name": "Executive Minimalist",
            "description": "High-contrast, conservative layout engineered for maximum ATS parser compliance.",
            "is_default": False,
        },
        {
            "id": "compact",
            "name": "Compact Classic",
            "description": "Space-efficient single/two-page dense layout ideal for engineering depth.",
            "is_default": False,
        },
        {
            "id": "cv_executive",
            "name": "Executive Curriculum Vitae (CV)",
            "description": "Comprehensive multi-page CV layout featuring architectural project case studies, leadership highlights, and certifications.",
            "is_default": False,
        },
    ]

    def list_templates(self) -> List[Dict[str, Any]]:
        return self.TEMPLATES

    GOOGLE_FONTS_TAG = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400..800;1,400..800&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&family=Open+Sans:ital,wght@0,300..800;1,300..800&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">'
    )

    def _build_dynamic_styles(self, config: Optional[TemplateConfig]) -> str:
        if not config:
            return ""
        
        density = config.density or "normal"
        if density == "compact":
            padding = "28px 36px"
            section_margin = "8px"
            item_margin = "5px"
            bullet_margin = "1px"
            default_lh = "1.25"
            default_fs = "10.5px"
        elif density == "comfortable":
            padding = "54px 58px"
            section_margin = "20px"
            item_margin = "14px"
            bullet_margin = "5px"
            default_lh = "1.50"
            default_fs = "12.5px"
        else: # normal
            padding = "34px 40px"
            section_margin = "13px"
            item_margin = "9px"
            bullet_margin = "2.5px"
            default_lh = "1.36"
            default_fs = "11.5px"

        # Explicit user selection overrides density preset
        if config.line_height and config.line_height not in ("1.36", ""):
            line_height = config.line_height
        else:
            line_height = default_lh

        if config.font_size and config.font_size not in ("11.5px", ""):
            font_size = config.font_size
        else:
            font_size = default_fs

        header_layout = config.header_layout or "left"
        if header_layout == "center":
            header_css = """
            .header {
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                text-align: center !important;
                margin-bottom: 14px !important;
                width: 100% !important;
            }
            .header-info, .header-top-row {
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                text-align: center !important;
                width: 100% !important;
                margin-left: auto !important;
                margin-right: auto !important;
            }
            .name, h1, .title-tagline {
                text-align: center !important;
                width: 100% !important;
                margin-left: auto !important;
                margin-right: auto !important;
            }
            .header-doc-type {
                margin-top: 4px !important;
                display: inline-block !important;
            }
            .contacts {
                display: flex !important;
                flex-wrap: wrap !important;
                justify-content: center !important;
                align-items: center !important;
                text-align: center !important;
                gap: 8px 14px !important;
                margin-top: 6px !important;
                width: 100% !important;
                margin-left: auto !important;
                margin-right: auto !important;
            }
            .contact-item {
                justify-content: center !important;
                text-align: center !important;
            }
            """
        elif header_layout == "split":
            header_css = """
            .header {
                display: flex !important;
                flex-direction: row !important;
                justify-content: space-between !important;
                align-items: flex-start !important;
                flex-wrap: nowrap !important;
                gap: 16px !important;
                margin-bottom: 14px !important;
                text-align: left !important;
                width: 100% !important;
            }
            .header-info {
                flex: 1 1 auto !important;
                text-align: left !important;
                min-width: 0 !important;
            }
            .header-top-row {
                display: flex !important;
                justify-content: flex-start !important;
                align-items: baseline !important;
                gap: 10px !important;
                flex-wrap: wrap !important;
            }
            .name, h1, .title-tagline {
                text-align: left !important;
                margin-left: 0 !important;
            }
            .contacts {
                flex: 0 1 auto !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: flex-end !important;
                justify-content: flex-start !important;
                text-align: right !important;
                gap: 3px !important;
                min-width: 220px !important;
                max-width: 50% !important;
                margin-top: 2px !important;
                border-bottom: none !important;
                padding-bottom: 0 !important;
                margin-bottom: 0 !important;
            }
            .contact-item {
                justify-content: flex-end !important;
                text-align: right !important;
            }
            """
        else: # left
            header_css = """
            .header {
                display: flex !important;
                flex-direction: column !important;
                align-items: flex-start !important;
                text-align: left !important;
                margin-bottom: 14px !important;
                width: 100% !important;
            }
            .header-info {
                text-align: left !important;
                width: 100% !important;
            }
            .header-top-row {
                display: flex !important;
                justify-content: flex-start !important;
                align-items: baseline !important;
                gap: 10px !important;
                flex-wrap: wrap !important;
            }
            .name, h1, .title-tagline {
                text-align: left !important;
                margin-left: 0 !important;
            }
            .contacts {
                display: flex !important;
                flex-wrap: wrap !important;
                justify-content: flex-start !important;
                align-items: center !important;
                text-align: left !important;
                gap: 8px 14px !important;
                margin-top: 6px !important;
                width: 100% !important;
            }
            .contact-item {
                justify-content: flex-start !important;
                text-align: left !important;
            }
            """

        return f"""
        /* User Configured Dynamic Overrides */
        :root {{
            --primary-color: {config.primary_color} !important;
            --accent-color: {config.accent_color} !important;
            --accent-light: {config.accent_color} !important;
            --text-primary: {config.text_color} !important;
            --font-family: {config.font_family} !important;
            --font-size: {font_size} !important;
            --line-height: {line_height} !important;
        }}
        body, body * {{
            font-family: var(--font-family) !important;
        }}
        pre, code, .diff-sign, .font-mono, [class*="mono"] {{
            font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
        }}
        body {{
            color: var(--text-primary) !important;
            line-height: var(--line-height) !important;
            font-size: var(--font-size) !important;
        }}
        p, li, .summary-text, .exp-highlights, .project-highlights, .contacts, .side-entry-sub, .side-entry-meta, .letter-text, .entry-bullets li {{
            font-size: var(--font-size) !important;
            line-height: var(--line-height) !important;
        }}
        .name, h1 {{
            color: var(--primary-color) !important;
            font-size: calc(var(--font-size) * 2.1) !important;
            line-height: 1.15 !important;
        }}
        .sec-heading, .section-title, .cv-section-title, .cv-section-title-alt {{
            color: var(--primary-color) !important;
            border-bottom-color: var(--primary-color) !important;
            font-size: calc(var(--font-size) * 1.18) !important;
        }}
        .exp-role, .project-name, .cv-project-title, .scope-title, .addressee-to, .subject-line, .signoff-name, .competency-title, .side-entry-title {{
            color: var(--primary-color) !important;
        }}
        .title-tagline, .title, .exp-company, .cv-project-role, .scope-company, .edu-degree, .target-company, .skill-label, .addressee-company, .subject-role, .signoff-title, .case-study-role {{
            color: var(--accent-color) !important;
        }}
        a, .contacts a, .proj-link, .entry-link {{
            color: var(--accent-color) !important;
        }}
        .target-badge, .badge, .tag-primary {{
            background-color: var(--primary-color) !important;
            color: #ffffff !important;
        }}
        .cv-target-banner, .cv-letter-box {{
            border-left-color: var(--primary-color) !important;
        }}
        .role-scope-box {{
            border-left-color: var(--accent-color) !important;
        }}
        .paper, .resume-paper {{
            border-top-color: var(--primary-color) !important;
        }}
        @media screen {{
            body {{
                background-color: transparent !important;
                padding: 0 !important;
                margin: 0 !important;
            }}
            .resume-paper, .paper {{
                padding: {padding} !important;
                background: #ffffff !important;
                max-width: 840px !important;
                width: 100% !important;
                margin: 0 auto !important;
                box-shadow: 0 4px 24px -2px rgba(15, 23, 42, 0.12) !important;
                border-radius: 6px !important;
                border: 1px solid #e2e8f0 !important;
            }}
        }}
        @media print {{
            body {{
                background: #ffffff !important;
                padding: 0 !important;
                margin: 0 !important;
            }}
            .resume-paper, .paper {{
                padding: 0 !important;
                margin: 0 !important;
                box-shadow: none !important;
                border: none !important;
                max-width: 100% !important;
                width: 100% !important;
            }}
        }}
        .section, .cv-section, .cv-addressee-block, .cv-target-banner, .cv-intel-box, .cv-signoff-block {{
            margin-bottom: {section_margin} !important;
        }}
        .experience-entry, .project-card, .project-entry, .cv-project-card, .education-entry, .edu-item, .cv-entry, .cert-entry, .side-entry, .cv-scope-item, .cv-letter-box {{
            margin-bottom: {item_margin} !important;
        }}
        .exp-highlights li, .project-highlights li, .entry-bullets li {{
            margin-bottom: {bullet_margin} !important;
        }}
        {header_css}
        {config.custom_css or ""}
        """

    def _is_valid_url(self, url: Optional[str]) -> bool:
        """Checks if a URL has a genuine protocol and valid domain structure."""
        if not url:
            return False
        u = str(url).strip()
        if u.lower() in ("https:", "https://", "http:", "http://", "https", "http", "#"):
            return False
        return bool(re.match(r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", u, re.IGNORECASE))

    def _format_url(self, url: Optional[str], platform: str = "") -> Tuple[str, str]:
        """
        Returns (href, display_label).
        Ensures href is always an absolute URL with scheme (http:// or https://)
        so browsers never resolve it as a relative path against localhost.
        """
        if not url:
            return ("", "")
        raw = str(url).strip()
        if not raw:
            return ("", "")

        platform_lower = platform.lower()
        raw_lower = raw.lower()

        # Normalization for LinkedIn
        if platform_lower == "linkedin" or "linkedin.com" in raw_lower or raw_lower.startswith("linkedin/"):
            clean = raw
            clean = re.sub(r"^https?://(www\.)?linkedin\.com/in/", "", clean, flags=re.IGNORECASE)
            clean = re.sub(r"^https?://(www\.)?linkedin\.com/", "", clean, flags=re.IGNORECASE)
            clean = re.sub(r"^linkedin/in/", "", clean, flags=re.IGNORECASE)
            clean = re.sub(r"^linkedin/", "", clean, flags=re.IGNORECASE)
            clean = clean.strip("/")
            href = f"https://www.linkedin.com/in/{clean}" if clean else "https://www.linkedin.com"
            label = f"linkedin.com/in/{clean}" if clean else "LinkedIn"
            return (href, label)

        # Normalization for GitHub
        if platform_lower == "github" or "github.com" in raw_lower or raw_lower.startswith("github/"):
            clean = raw
            clean = re.sub(r"^https?://(www\.)?github\.com/", "", clean, flags=re.IGNORECASE)
            clean = re.sub(r"^github/", "", clean, flags=re.IGNORECASE)
            clean = clean.strip("/")
            href = f"https://github.com/{clean}" if clean else "https://github.com"
            label = f"github.com/{clean}" if clean else "GitHub"
            return (href, label)

        # General / Portfolio URL
        href = raw
        if not (href.startswith("http://") or href.startswith("https://")):
            href = f"https://{href}"

        # Clean display label
        label = raw
        label = re.sub(r"^https?://", "", label, flags=re.IGNORECASE)
        label = re.sub(r"^www\.", "", label, flags=re.IGNORECASE)
        label = label.rstrip("/")
        if not label:
            label = "Portfolio"
        return (href, label)

    def highlight_target_terms(self, text: str, target_terms: Set[str]) -> str:
        """Highlights matching target keywords cleanly without strikethroughs."""
        if not text or not target_terms:
            return text
        words = text.split()
        out = []
        for w in words:
            w_clean = re.sub(r"[^\w\+\#]", "", w.lower())
            if w_clean in target_terms or any(t in w_clean for t in target_terms if len(t) > 3):
                out.append(f'<mark class="diff-kw-term">{w}</mark>')
            else:
                out.append(w)
        return " ".join(out)

    def diff_text(
        self,
        new_text: str,
        base_text: Optional[str] = None,
        target_terms: Optional[Set[str]] = None,
    ) -> str:
        """
        Subtly highlights customized keywords in new_text.
        Never outputs strikethrough (<del>) text or plus/minus signs.
        """
        if not new_text:
            return ""
        target_terms = target_terms or set()
        return self.highlight_target_terms(new_text, target_terms)

    def diff_bullet(
        self,
        bullet: str,
        base_bullets: List[str],
        target_terms: Set[str],
    ) -> Tuple[str, bool, bool]:
        """
        Compares a tailored bullet against base bullets.
        Returns: (highlighted_html, is_modified, has_target_kw)
        Never outputs strikethrough (<del>) or plus/minus signs.
        """
        b_clean = bullet.strip().lower()
        base_clean_set = {b.strip().lower() for b in base_bullets}
        has_target_kw = any(kw in b_clean for kw in target_terms if len(kw) > 3)
        is_modified = b_clean not in base_clean_set

        highlighted = self.highlight_target_terms(bullet, target_terms)
        return highlighted, is_modified, has_target_kw

    def render(
        self,
        resume: ResumeData,
        template_id: str = "modern",
        highlight_diff: bool = False,
        base_resume: Optional[ResumeData] = None,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        """Renders the resume or CV data into a standalone, printable HTML document."""
        config_passed = config is not None
        if config is None:
            try:
                from .resume_store import resume_store
                config = resume_store.get_template_config()
            except Exception:
                config = TemplateConfig()

        if base_resume is None:
            try:
                from .resume_store import resume_store
                base_resume = resume_store.get_base_resume()
            except Exception:
                pass

        doc_type = getattr(resume, "document_type", "resume")
        if config_passed and config and config.template_id:
            effective_tmpl = config.template_id
        elif template_id:
            effective_tmpl = template_id
        elif doc_type == "cv":
            effective_tmpl = "cv_executive"
        elif config and config.template_id:
            effective_tmpl = config.template_id
        else:
            effective_tmpl = "modern"

        if effective_tmpl == "cv_executive":
            return self._render_cv_executive(resume, highlight_diff, base_resume, config=config)
        elif effective_tmpl == "executive":
            return self._render_executive(resume, highlight_diff, base_resume, config=config)
        elif effective_tmpl == "compact":
            return self._render_compact(resume, highlight_diff, base_resume, config=config)
        elif effective_tmpl == "modern":
            return self._render_modern(resume, highlight_diff, base_resume, config=config)
        elif doc_type == "cv":
            return self._render_cv_executive(resume, highlight_diff, base_resume, config=config)
        else:
            return self._render_modern(resume, highlight_diff, base_resume, config=config)

    def _render_modern(
        self,
        resume: ResumeData,
        highlight_diff: bool = False,
        base_resume: Optional[ResumeData] = None,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        if base_resume is None:
            try:
                from .resume_store import resume_store
                base_resume = resume_store.get_base_resume()
            except Exception:
                pass

        base_bullets_by_company = {}
        all_base_bullets = []
        base_projects_by_name = {}
        if base_resume:
            for b_exp in base_resume.experience:
                c_key = b_exp.company.strip().lower()
                base_bullets_by_company.setdefault(c_key, []).extend(b_exp.highlights)
                all_base_bullets.extend(b_exp.highlights)
            for b_proj in (getattr(base_resume, "projects", None) or []):
                base_projects_by_name[b_proj.name.strip().lower()] = b_proj.description

        target_role = getattr(resume, "target_role", None)
        target_company = getattr(resume, "target_company", None)

        target_terms = set()
        if target_role:
            for w in re.findall(r"\b[A-Za-z0-9#\+\.]+\b", target_role.lower()):
                if len(w) > 2 and w not in ("and", "for", "the", "developer", "engineer"):
                    target_terms.add(w)
        for cat, slist in (resume.skills or {}).items():
            for s in slist[:4]:
                target_terms.add(s.lower())

        diff_legend_html = ""
        if highlight_diff:
            diff_legend_html = f"""
            <div class="cv-diff-banner avoid-break" style="background:#f8fafc; border:1px solid #e2e8f0; border-left:4px solid var(--primary-color); border-radius:4px; padding:6px 12px; margin-bottom:12px; font-size:8pt; color:var(--text-primary);">
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:6px;">
                    <span style="font-weight:700; color:var(--primary-color);">DIFF VIEW ACTIVE &bull; Showing customized keyword alignment for {target_role or "target role"}</span>
                    <span style="font-size:7.5pt; color:var(--text-muted);">Tailored Profile</span>
                </div>
            </div>
            """

        base_summary = base_resume.summary if base_resume else ""
        is_summary_modified = False
        if highlight_diff and base_resume:
            is_summary_modified = (resume.summary.strip().lower() != base_summary.strip().lower())
        elif highlight_diff:
            is_summary_modified = True

        rendered_summary = (
            self.diff_text(resume.summary, base_summary, target_terms)
            if highlight_diff
            else resume.summary
        )

        use_icons = config.show_icons if config is not None else True
        icon_email = "✉ " if use_icons else ""
        icon_phone = "📞 " if use_icons else ""
        icon_loc = "📍 " if use_icons else ""
        icon_linkedin = "🔗 " if use_icons else ""
        icon_github = "💻 " if use_icons else ""
        icon_portfolio = "🌐 " if use_icons else ""

        # Contact items
        contacts = []
        if resume.phone:
            contacts.append(f'<span class="contact-item"><span class="contact-icon">{icon_phone}</span>{resume.phone}</span>')
        if resume.email:
            contacts.append(f'<span class="contact-item"><span class="contact-icon">{icon_email}</span>{resume.email}</span>')
        if resume.linkedin:
            l_href, l_label = self._format_url(resume.linkedin, "linkedin")
            contacts.append(f'<a href="{l_href}" target="_blank" rel="noopener noreferrer" class="contact-item"><span class="contact-icon">{icon_linkedin}</span>{l_label}</a>')
        if resume.github:
            g_href, g_label = self._format_url(resume.github, "github")
            contacts.append(f'<a href="{g_href}" target="_blank" rel="noopener noreferrer" class="contact-item"><span class="contact-icon">{icon_github}</span>{g_label}</a>')
        if getattr(resume, "portfolio", None):
            p_href, p_label = self._format_url(resume.portfolio, "portfolio")
            contacts.append(f'<a href="{p_href}" target="_blank" rel="noopener noreferrer" class="contact-item"><span class="contact-icon">{icon_portfolio}</span>{p_label}</a>')
        if resume.location:
            contacts.append(f'<span class="contact-item"><span class="contact-icon">{icon_loc}</span>{resume.location}</span>')
        contact_html = "".join(contacts)

        # Experience items (Left Column)
        exp_html = ""
        for exp in resume.experience:
            bullets = ""
            c_key = exp.company.strip().lower()
            relevant_base_bullets = base_bullets_by_company.get(c_key, all_base_bullets)

            # Check if company string contains client annotation (e.g. "Parnasoft Technologies — Client: AVEVA")
            comp_display = exp.company
            client_bullet = ""
            if " — Client: " in exp.company:
                parts = exp.company.split(" — Client: ", 1)
                comp_display = parts[0]
                loc_client = f" - {exp.location}" if exp.location else ""
                client_bullet = f'<li style="font-weight:600; color:#334155;">Client: {parts[1]}{loc_client}</li>\n'
            elif " - Client: " in exp.company:
                parts = exp.company.split(" - Client: ", 1)
                comp_display = parts[0]
                loc_client = f" - {exp.location}" if exp.location else ""
                client_bullet = f'<li style="font-weight:600; color:#334155;">Client: {parts[1]}{loc_client}</li>\n'

            for h in exp.highlights:
                if highlight_diff:
                    h_rendered, is_modified, has_target_kw = self.diff_bullet(h, relevant_base_bullets, target_terms)
                    highlight_cls = "highlighted-bullet" if is_modified or has_target_kw else ""
                else:
                    h_rendered = h
                    highlight_cls = ""
                bullets += f'<li class="{highlight_cls}">{h_rendered}</li>\n'
            
            loc_str = f'&nbsp;&nbsp; <span class="meta-icon">📍</span> {exp.location}' if exp.location else ''
            exp_html += f"""
            <div class="experience-entry">
                <div class="exp-role">{exp.role}</div>
                <div class="exp-company">{comp_display}</div>
                <div class="exp-meta"><span class="meta-icon">📅</span> {exp.period}{loc_str}</div>
                <ul class="exp-highlights">
                    {client_bullet}{bullets}
                </ul>
            </div>
            """

        # Projects (Left Column, below Experience) - only rendered if legitimate projects exist
        projects_html = ""
        show_proj = config.show_projects if config is not None else True
        valid_projects = [p for p in (getattr(resume, "projects", None) or []) if p.name and (p.description or p.role)]
        if show_proj and valid_projects:
            p_entries = []
            for proj in valid_projects:
                period_str = f'<div class="exp-meta"><span class="meta-icon">📅</span> {proj.period}</div>' if proj.period else ''
                base_p_desc = base_projects_by_name.get(proj.name.strip().lower(), "")
                rendered_p_desc = (
                    self.diff_text(proj.description, base_p_desc, target_terms)
                    if highlight_diff and proj.description
                    else (proj.description or "")
                )
                
                # Split description into bullet points if multi-sentence
                sentences = [s.strip() for s in re.split(r'\.\s+(?=[A-Z])', rendered_p_desc) if s.strip()]
                if len(sentences) > 1:
                    p_bullets = "".join([f'<li>{s if s.endswith(".") else s + "."}</li>\n' for s in sentences])
                elif sentences:
                    p_bullets = f'<li>{sentences[0]}</li>\n'
                else:
                    p_bullets = ""
                
                tech_or_role = ", ".join(proj.technologies[:4]) if proj.technologies else (proj.role or "")
                tech_sub = f'<div class="exp-company">{tech_or_role}</div>' if tech_or_role else ''

                p_entries.append(f"""
                <div class="project-entry">
                    <div class="exp-role">{proj.name}</div>
                    {tech_sub}
                    {period_str}
                    {f'<ul class="exp-highlights">{p_bullets}</ul>' if p_bullets else ''}
                </div>
                """)

            projects_html = f"""
            <div class="section">
                <hr class="dotted-sep">
                <div class="section-title">KEY PROJECTS & ARCHITECTURE</div>
                {"".join(p_entries)}
            </div>
            """

        # Right Column Sections:
        # 1. Summary
        summary_headline_parts = []
        if resume.title:
            summary_headline_parts.append(format_job_title(resume.title))
        if getattr(resume, "skills", None) and "frontendArchitecture" in resume.skills:
            summary_headline_parts.append(", ".join(resume.skills["frontendArchitecture"][:3]))
        summary_headline_str = " &bull; ".join(summary_headline_parts) if summary_headline_parts else ""
        summary_headline_html = f'<div class="summary-headline">{summary_headline_str}</div>' if summary_headline_str else ''

        summary_diff_style = "background:#f0fdf4; border-left:3px solid #16a34a; padding:6px 8px; border-radius:0 4px 4px 0;" if is_summary_modified else ""
        summary_html = f"""
        <div class="section">
            <div class="section-title">SUMMARY</div>
            {summary_headline_html}
            <div class="summary-text" style="{summary_diff_style}">{rendered_summary}</div>
        </div>
        """

        # 2. Training / Courses
        courses_items = []
        if getattr(resume, "additional_sections", None):
            courses_items = resume.additional_sections.get("training") or resume.additional_sections.get("courses") or []
        
        courses_html = ""
        if courses_items:
            c_html = "".join([f'<div class="side-entry"><div class="side-entry-title">{item}</div></div>' for item in courses_items])
            courses_html = f"""
            <div class="section">
                <div class="section-title">TRAINING / COURSES</div>
                {c_html}
            </div>
            """

        # 3. Skills Pills
        seen_skills = set()
        skills_pills = []
        source_skills = resume.skills
        if (not source_skills or not any(source_skills.values())) and base_resume and base_resume.skills:
            source_skills = base_resume.skills

        for cat_name, skill_list in (source_skills or {}).items():
            for s in skill_list:
                s_clean = s.strip()
                if s_clean and s_clean.lower() not in seen_skills:
                    seen_skills.add(s_clean.lower())
                    is_matched = highlight_diff and (
                        s_clean.lower() in target_terms or any(t in s_clean.lower() for t in target_terms if len(t) > 3)
                    )
                    if is_matched:
                        skills_pills.append(f'<span class="skill-pill matched">✓ {s_clean}</span>')
                    else:
                        skills_pills.append(f'<span class="skill-pill">{s_clean}</span>')

        skills_html = ""
        if skills_pills:
            skills_html = f"""
            <div class="section">
                <div class="section-title" title="Technical Competencies">SKILLS <!-- Technical Competencies --></div>
                <div class="skills-pill-grid">
                    {''.join(skills_pills)}
                </div>
            </div>
            """

        # 4. Certifications
        cert_html = ""
        show_cert = config.show_certifications if config is not None else True
        if show_cert and getattr(resume, "certifications", None):
            cert_entries = ""
            for cert in resume.certifications:
                yr = f" ({cert.year})" if cert.year else ""
                url_str = f' <a href="{cert.url}" target="_blank" style="color:var(--accent-color); text-decoration:none;">🔗</a>' if self._is_valid_url(cert.url) else ""
                cert_entries += f"""
                <div class="side-entry">
                    <div class="side-entry-title">{cert.name}</div>
                    <div class="side-entry-sub">{cert.issuer}{yr}{url_str}</div>
                </div>
                """
            cert_html = f"""
            <div class="section">
                <div class="section-title">CERTIFICATIONS</div>
                {cert_entries}
            </div>
            """

        # 5. Education
        edu_html = ""
        show_edu = config.show_education if config is not None else True
        if show_edu and resume.education:
            edu_entries = ""
            for edu in resume.education:
                edu_entries += f"""
                <div class="side-entry">
                    <div class="side-entry-title">{edu.degree}</div>
                    <div class="side-entry-sub">{edu.institution}</div>
                    <div class="side-entry-meta"><span class="meta-icon">📅</span> {edu.period}</div>
                </div>
                """
            edu_html = f"""
            <div class="section">
                <div class="section-title">Education</div>
                {edu_entries}
            </div>
            """

        display_name = resume.name.title() if (resume.name and (resume.name.isupper() or resume.name.islower())) else resume.name
        display_title = format_job_title(resume.title)
        display_tagline = re.sub(r"\s*•?\s*Aligned for\s+[^•]+", "", resume.tagline or "", flags=re.IGNORECASE).strip(" •")
        tagline_html = f" • {display_tagline}" if (config is None or config.show_tagline) and display_tagline else ""
        header_title_tagline_html = f'<div class="title-tagline">{display_title}{tagline_html}</div>' if display_title else ''

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{resume.name} - Resume</title>
{self.GOOGLE_FONTS_TAG}
<style>
  :root {{
    --primary-color: #0f172a;
    --accent-color: #0284c7;
    --accent-light: #f0f9ff;
    --text-primary: #1e293b;
    --text-muted: #475569;
    --border-color: #cbd5e1;
    --divider-subtle: #f1f5f9;
    --diff-bg: #f0fdf4;
    --diff-border: #16a34a;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: var(--text-primary);
    background-color: transparent;
    line-height: 1.36;
    padding: 0;
    margin: 0;
    font-size: 8.5pt;
  }}
  .resume-paper {{
    max-width: 840px;
    margin: 0 auto;
    background: #ffffff;
    padding: 34px 40px;
    box-shadow: 0 4px 24px -2px rgba(15, 23, 42, 0.12);
    border-radius: 6px;
    border: 1px solid #e2e8f0;
    height: auto !important;
  }}
  .ats-banner {{
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 6px;
    padding: 8px 14px;
    margin-bottom: 16px;
    text-align: center;
    font-size: 9.5pt;
    font-weight: 700;
    color: #065f46;
    letter-spacing: 0.2px;
  }}
  .ats-banner-check {{
    color: #059669;
    font-weight: 900;
    margin-right: 4px;
  }}
  .header {{
    margin-bottom: 14px;
    padding-bottom: 0;
  }}
  .name {{
    font-size: 22pt;
    font-weight: 800;
    color: var(--primary-color);
    letter-spacing: -0.3px;
    margin-bottom: 2px;
    line-height: 1.15;
  }}
  .title-tagline {{
    font-size: 11pt;
    font-weight: 700;
    color: var(--accent-color);
    margin-bottom: 8px;
    letter-spacing: 0.2px;
  }}
  .contacts {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    font-size: 8.5pt;
    color: var(--text-primary);
    font-weight: 500;
    line-height: 1.4;
  }}
  .contact-item {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--text-primary);
    text-decoration: none;
  }}
  .contact-item a {{
    color: var(--text-primary);
    text-decoration: none;
  }}
  .contact-item a:hover {{
    color: var(--accent-color);
    text-decoration: underline;
  }}
  .contact-icon {{
    font-size: 9pt;
  }}

  /* Two Column Grid */
  .resume-columns {{
    display: grid;
    grid-template-columns: 1.62fr 1fr;
    column-gap: 22px;
    align-items: start;
  }}
  .col-main {{
    min-width: 0;
  }}
  .col-side {{
    min-width: 0;
  }}

  .section {{
    margin-bottom: 13px;
  }}
  .section-title {{
    font-size: 10.5pt;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--primary-color);
    border-bottom: 2px solid var(--primary-color);
    padding-bottom: 3px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }}
  .dotted-sep {{
    border: none;
    border-top: 1px dotted #cbd5e1;
    margin: 12px 0 10px 0;
  }}

  /* Experience / Main column items */
  .experience-entry {{
    margin-bottom: 10px;
    padding-bottom: 9px;
    border-bottom: 1px solid var(--divider-subtle);
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .experience-entry:last-child {{
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 0;
  }}
  .exp-role {{
    font-size: 9.5pt;
    font-weight: 700;
    color: var(--primary-color);
    line-height: 1.25;
  }}
  .exp-company {{
    font-size: 9pt;
    font-weight: 700;
    color: var(--accent-color);
    margin-top: 1px;
    line-height: 1.25;
  }}
  .exp-meta {{
    font-size: 8pt;
    color: var(--text-muted);
    margin: 2px 0 4px 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .exp-highlights {{
    list-style-type: disc;
    padding-left: 15px;
    font-size: 8.5pt;
    color: var(--text-primary);
    line-height: 1.36;
  }}
  .exp-highlights li {{
    margin-bottom: 2px;
  }}

  /* Projects */
  .project-entry {{
    margin-bottom: 9px;
    padding-bottom: 8px;
    border-bottom: 1px dotted #e2e8f0;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .project-entry:last-child {{
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 0;
  }}
  .proj-link {{
    color: var(--accent-color);
    text-decoration: none;
    font-size: 8pt;
    margin-left: 4px;
  }}

  /* Right column / Side items */
  .summary-text {{
    font-size: 8.5pt;
    color: var(--text-primary);
    line-height: 1.4;
    text-align: left;
  }}
  .summary-headline {{
    font-size: 8.5pt;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 4px;
    line-height: 1.35;
  }}
  .side-entry {{
    margin-bottom: 8px;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .side-entry:last-child {{
    margin-bottom: 0;
  }}
  .side-entry-title {{
    font-size: 8.5pt;
    font-weight: 700;
    color: var(--primary-color);
    line-height: 1.25;
  }}
  .side-entry-sub {{
    font-size: 8pt;
    color: var(--text-muted);
    line-height: 1.25;
    margin-top: 1px;
  }}
  .side-entry-meta {{
    font-size: 7.5pt;
    color: var(--text-muted);
    margin-top: 1px;
  }}

  /* Skill Pills */
  .skills-pill-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 2px;
  }}
  .skill-pill {{
    display: inline-block;
    border: 1px solid #cbd5e1;
    background: #ffffff;
    color: #1e293b;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 7.8pt;
    font-weight: 600;
    line-height: 1.25;
  }}
  .skill-pill.matched {{
    background: #dcfce7 !important;
    border-color: #86efac !important;
    color: #166534 !important;
    font-weight: 700 !important;
  }}

  /* Diff styles */
  .highlighted-bullet {{
    background-color: var(--diff-bg);
    border-left: 3px solid var(--diff-border);
    padding-left: 6px;
    border-radius: 2px;
  }}
  del.git-diff-del {{
    background-color: #ffebe9 !important;
    color: #cf222e !important;
    text-decoration: line-through !important;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #ffc1ba;
    font-size: 0.95em;
    margin-right: 3px;
    display: inline;
  }}
  ins.git-diff-ins, mark.diff-text-added, mark.diff-text-adapted {{
    background-color: #dafbe1 !important;
    color: #116329 !important;
    text-decoration: none !important;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #86efac;
    font-weight: 600;
    display: inline;
  }}
  mark.diff-text-adapted {{
    background-color: #fef08a !important;
    color: #713f12 !important;
    border-color: #fde047;
  }}
  .diff-sign {{
    user-select: none;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 800;
    margin-right: 2px;
  }}
  del.git-diff-del .diff-sign {{ color: #cf222e; }}
  ins.git-diff-ins .diff-sign {{ color: #116329; }}
  mark.diff-kw-term {{
    background-color: #bae6fd !important;
    color: #0369a1 !important;
    font-weight: 600;
    border-radius: 3px;
    padding: 1px 4px;
    box-shadow: 0 0 0 1px #7dd3fc;
    text-decoration: none;
  }}
  strong.diff-kw-match {{
    color: #0369a1 !important;
    font-weight: 800 !important;
    text-decoration: underline;
  }}

  /* Print Stylesheet strictly enforcing 1-2 pages maximum */
  @page {{
    size: letter portrait;
    margin: 8mm 10mm;
  }}
  @media print {{
    html, body {{
      background: #ffffff !important;
      padding: 0 !important;
      margin: 0 !important;
      height: auto !important;
      min-height: 0 !important;
      font-size: 8pt !important;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}
    .resume-paper {{
      box-shadow: none !important;
      padding: 0 !important;
      margin: 0 !important;
      max-width: 100% !important;
      width: 100% !important;
      border: none !important;
      height: auto !important;
      min-height: 0 !important;
    }}
    .ats-banner {{
      display: none !important;
    }}
    .cv-diff-banner {{
      display: none !important;
    }}
    .resume-columns {{
      display: grid !important;
      grid-template-columns: 1.62fr 1fr !important;
      column-gap: 18px !important;
    }}
    .experience-entry, .project-entry, .side-entry {{
      break-inside: avoid !important;
      page-break-inside: avoid !important;
    }}
    del.git-diff-del {{
      display: none !important;
    }}
    ins.git-diff-ins, mark.diff-text-added, mark.diff-text-adapted, mark.diff-kw-term {{
      background-color: transparent !important;
      color: inherit !important;
      font-weight: inherit !important;
      box-shadow: none !important;
      border: none !important;
      padding: 0 !important;
    }}
    .diff-sign {{ display: none !important; }}
    strong.diff-kw-match {{
      color: inherit !important;
      font-weight: inherit !important;
      text-decoration: none !important;
    }}
  }}
  {self._build_dynamic_styles(config)}
</style>
</head>
<body>
<div class="resume-paper">
  {diff_legend_html}
  <div class="ats-banner">
    <span class="ats-banner-check">✓</span> ATS-tested template • built to parse more cleanly
  </div>
  <div class="header">
    <div class="header-info">
      <div class="name">{display_name}</div>
      {header_title_tagline_html}
    </div>
    <div class="contacts">{contact_html}</div>
  </div>

  <div class="resume-columns">
    <div class="col-main">
      <div class="section">
        <div class="section-title">EXPERIENCE</div>
        {exp_html}
      </div>
      {projects_html}
    </div>

    <div class="col-side">
      {summary_html}
      {courses_html}
      {skills_html}
      {cert_html}
      {edu_html}
    </div>
  </div>
</div>
</body>
</html>
"""

    def _render_executive(
        self,
        resume: ResumeData,
        highlight_diff: bool = False,
        base_resume: Optional[ResumeData] = None,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        if base_resume is None:
            try:
                from .resume_store import resume_store
                base_resume = resume_store.get_base_resume()
            except Exception:
                pass

        base_bullets_by_company = {}
        all_base_bullets = []
        base_projects_by_name = {}
        if base_resume:
            for b_exp in base_resume.experience:
                c_key = b_exp.company.strip().lower()
                base_bullets_by_company.setdefault(c_key, []).extend(b_exp.highlights)
                all_base_bullets.extend(b_exp.highlights)
            for b_proj in (getattr(base_resume, "projects", None) or []):
                base_projects_by_name[b_proj.name.strip().lower()] = b_proj.description

        target_role = getattr(resume, "target_role", None)
        target_terms = set()
        if target_role:
            for w in re.findall(r"\b[A-Za-z0-9#\+\.]+\b", target_role.lower()):
                if len(w) > 2 and w not in ("and", "for", "the", "developer", "engineer"):
                    target_terms.add(w)
        for cat, slist in (resume.skills or {}).items():
            for s in slist[:4]:
                target_terms.add(s.lower())

        diff_legend_html = ""
        if highlight_diff:
            diff_legend_html = f"""
            <div class="cv-diff-banner avoid-break" style="background:#f8fafc; border:1px solid #e2e8f0; border-left:4px solid var(--primary-color); border-radius:4px; padding:6px 12px; margin-bottom:12px; font-size:8pt; color:var(--text-primary);">
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:6px;">
                    <span style="font-weight:700; color:var(--primary-color);">DIFF VIEW ACTIVE &bull; Showing customized keyword alignment for {target_role or "target role"}</span>
                    <span style="font-size:7.5pt; color:var(--text-muted);">Tailored Profile</span>
                </div>
            </div>
            """

        # High contrast, ATS compliant contacts
        use_icons = config.show_icons if config is not None else True
        icon_email = "✉ " if use_icons else ""
        icon_phone = "📞 " if use_icons else ""
        icon_loc = "📍 " if use_icons else ""
        icon_linkedin = "🔗 " if use_icons else ""
        icon_github = "💻 " if use_icons else ""
        icon_portfolio = "🌐 " if use_icons else ""

        contacts = []
        if resume.phone:
            contacts.append(f'<span class="contact-item"><span class="contact-icon">{icon_phone}</span>{resume.phone}</span>')
        if resume.email:
            contacts.append(f'<span class="contact-item"><span class="contact-icon">{icon_email}</span>{resume.email}</span>')
        if resume.linkedin:
            l_href, l_label = self._format_url(resume.linkedin, "linkedin")
            contacts.append(f'<a href="{l_href}" target="_blank" rel="noopener noreferrer" class="contact-item"><span class="contact-icon">{icon_linkedin}</span>{l_label}</a>')
        if resume.github:
            g_href, g_label = self._format_url(resume.github, "github")
            contacts.append(f'<a href="{g_href}" target="_blank" rel="noopener noreferrer" class="contact-item"><span class="contact-icon">{icon_github}</span>{g_label}</a>')
        if getattr(resume, "portfolio", None):
            p_href, p_label = self._format_url(resume.portfolio, "portfolio")
            contacts.append(f'<a href="{p_href}" target="_blank" rel="noopener noreferrer" class="contact-item"><span class="contact-icon">{icon_portfolio}</span>{p_label}</a>')
        if resume.location:
            contacts.append(f'<span class="contact-item"><span class="contact-icon">{icon_loc}</span>{resume.location}</span>')
        contact_html = "".join(contacts)

        exp_html = ""
        for exp in resume.experience:
            bullets = ""
            c_key = exp.company.strip().lower()
            relevant_base_bullets = base_bullets_by_company.get(c_key, all_base_bullets)
            for h in exp.highlights:
                if highlight_diff:
                    h_rendered, is_modified, has_target_kw = self.diff_bullet(h, relevant_base_bullets, target_terms)
                    highlight_cls = "highlighted-bullet" if is_modified or has_target_kw else ""
                else:
                    h_rendered = h
                    highlight_cls = ""
                bullets += f'<li class="{highlight_cls}">{h_rendered}</li>\n'

            loc = f" — {exp.location}" if exp.location else ""
            exp_html += f"""
            <div class="experience-entry" style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb; break-inside: avoid;">
              <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 2px;">
                <span class="exp-role" style="font-size: 10.5pt;">{exp.role}</span>
                <span style="font-size: 9pt; font-weight: 600; color: #4b5563;">{exp.period}</span>
              </div>
              <div class="exp-company" style="font-style: italic; font-size: 10pt; margin-bottom: 5px;">{exp.company}{loc}</div>
              <ul class="exp-highlights" style="padding-left: 20px; line-height: 1.5;">{bullets}</ul>
            </div>
            """

        source_skills = resume.skills
        if (not source_skills or not any(source_skills.values())) and base_resume and base_resume.skills:
            source_skills = base_resume.skills

        skills_lines = []
        for cat, items in (source_skills or {}).items():
            cat_label = cat.replace("_", " ").title()
            pills = []
            for item in items:
                if highlight_diff and (item.lower() in target_terms or any(t in item.lower() for t in target_terms if len(t) > 3)):
                    pills.append(f'<mark class="diff-kw-term">{item}</mark>')
                else:
                    pills.append(item)
            if pills:
                skills_lines.append(f"<strong>{cat_label}:</strong> " + ", ".join(pills))
        skills_html = "<br>".join(skills_lines)

        base_summary = base_resume.summary if base_resume else ""
        rendered_summary = (
            self.diff_text(resume.summary, base_summary, target_terms)
            if highlight_diff
            else resume.summary
        )

        summary_style = "line-height: 1.55; text-align: left;"
        summary_badge = ""

        projects_html = ""
        show_proj = config.show_projects if config is not None else True
        valid_projects = [
            p for p in (getattr(resume, "projects", None) or [])
            if p.name and p.name.strip() and p.description and p.description.strip()
        ]
        if show_proj and valid_projects:
            for proj in valid_projects:
                techs = f" — <em>{', '.join(proj.technologies)}</em>" if proj.technologies else ""
                period_s = f" ({proj.period})" if proj.period else ""
                base_p_desc = base_projects_by_name.get(proj.name.strip().lower(), "")
                rendered_p_desc = (
                    self.diff_text(proj.description, base_p_desc, target_terms)
                    if highlight_diff and proj.description
                    else proj.description
                )
                projects_html += f"""
                <div class="project-card" style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e5e7eb;">
                  <div><strong class="project-name">{proj.name}</strong>{period_s}{techs}</div>
                  <p class="project-highlights" style="margin: 2px 0 6px 0;">{rendered_p_desc}</p>
                </div>
                """

        edu_html = ""
        show_edu = config.show_education if config is not None else True
        if show_edu and resume.education:
            for edu in resume.education:
                edu_html += f"""
                <div class="education-entry" style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 9.5pt;">
                  <span><strong>{edu.degree}</strong>, {edu.institution}</span>
                  <span style="color: #666; font-size: 9pt;">{edu.period}</span>
                </div>
                """

        cert_html = ""
        show_cert = config.show_certifications if config is not None else True
        if show_cert and getattr(resume, "certifications", None):
            for cert in resume.certifications:
                yr = f" ({cert.year})" if cert.year else ""
                url_str = f' <a href="{cert.url}" target="_blank">🔗</a>' if self._is_valid_url(cert.url) else ""
                cert_html += f'<div style="font-size: 9.5pt; margin-bottom: 4px;"><strong>{cert.name}</strong> — {cert.issuer}{yr}{url_str}</div>'

        display_name = resume.name.title() if (resume.name and (resume.name.isupper() or resume.name.islower())) else resume.name
        display_title = format_job_title(resume.title)
        display_tagline = re.sub(r"\s*•?\s*Aligned for\s+[^•]+", "", resume.tagline or "", flags=re.IGNORECASE).strip(" •")
        tagline_html = f" • {display_tagline}" if (config is None or config.show_tagline) and display_tagline else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{resume.name} - Executive Resume</title>
{self.GOOGLE_FONTS_TAG}
<style>
  body {{ font-family: "Georgia", Times, serif; color: #111; line-height: 1.4; padding: 0; margin: 0; background: transparent; }}
  .paper, .resume-paper {{ max-width: 840px; margin: 0 auto; background: #fff; padding: 36px 44px; box-shadow: 0 4px 24px -2px rgba(15, 23, 42, 0.12); border-radius: 6px; border: 1px solid #e2e8f0; }}
  h1, .name {{ font-size: 24pt; margin-bottom: 2px; letter-spacing: 0.5px; }}
  .title, .title-tagline {{ font-size: 11pt; font-style: italic; margin-bottom: 4px; }}
  .contacts {{ font-size: 9.5pt; border-bottom: 2px solid var(--primary-color); padding-bottom: 12px; margin-bottom: 18px; }}
  .sec-heading, .section-title {{ font-size: 11pt; font-weight: bold; text-transform: uppercase; border-bottom: 1.5px solid var(--primary-color); padding-bottom: 3px; margin: 18px 0 10px 0; letter-spacing: 0.8px; }}
  .experience-entry:last-child, .project-card:last-child {{ border-bottom: none !important; padding-bottom: 0 !important; }}
  @media print {{ body {{ background: #fff; padding: 0; }} .paper, .resume-paper {{ box-shadow: none; padding: 0; }} .experience-entry, .project-card {{ border-bottom-color: #ccc !important; }} }}
  del.git-diff-del {{
    background-color: #ffebe9 !important;
    color: #cf222e !important;
    text-decoration: line-through !important;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #ffc1ba;
    font-size: 0.95em;
    margin-right: 3px;
    display: inline;
  }}
  ins.git-diff-ins, mark.diff-text-added, mark.diff-text-adapted {{
    background-color: #dafbe1 !important;
    color: #116329 !important;
    text-decoration: none !important;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #86efac;
    font-weight: 600;
    display: inline;
  }}
  mark.diff-text-adapted {{
    background-color: #fef08a !important;
    color: #713f12 !important;
    border-color: #fde047;
  }}
  .diff-sign {{
    user-select: none;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 800;
    margin-right: 2px;
  }}
  del.git-diff-del .diff-sign {{ color: #cf222e; }}
  ins.git-diff-ins .diff-sign {{ color: #116329; }}
  mark.diff-kw-term {{
    background-color: #bae6fd !important;
    color: #0369a1 !important;
    font-weight: 600;
    border-radius: 3px;
    padding: 1px 4px;
    box-shadow: 0 0 0 1px #7dd3fc;
    text-decoration: none;
  }}
  strong.diff-kw-match {{
    color: #0369a1 !important;
    font-weight: 800 !important;
    text-decoration: underline;
  }}
  @media print {{
    del.git-diff-del {{ display: none !important; }}
    ins.git-diff-ins, mark.diff-text-added, mark.diff-text-adapted, mark.diff-kw-term {{
      background-color: transparent !important;
      color: inherit !important;
      border: none !important;
      font-weight: inherit !important;
      box-shadow: none !important;
      padding: 0 !important;
      text-decoration: none !important;
    }}
    .diff-sign {{ display: none !important; }}
    strong.diff-kw-match {{
      color: inherit !important;
      font-weight: inherit !important;
      text-decoration: none !important;
    }}
  }}
  {self._build_dynamic_styles(config)}
</style>
</head>
<body>
<div class="resume-paper">
  {diff_legend_html}
  <div class="header">
    <div class="header-info">
      <h1 class="name">{display_name}</h1>
      <div class="title-tagline">{display_title}{tagline_html}</div>
    </div>
    <div class="contacts">{contact_html}</div>
  </div>

  <div class="section">
    <div class="sec-heading">Summary{summary_badge}</div>
    <p style="{summary_style}">{rendered_summary}</p>
  </div>

  <div class="section">
    <div class="sec-heading">Core Competencies</div>
    <div style="font-size: 10pt;">{skills_html}</div>
  </div>

  <div class="section">
    <div class="sec-heading">Professional Experience</div>
    {exp_html}
  </div>

  {f'<div class="section"><div class="sec-heading">Key Projects & Architecture</div>{projects_html}</div>' if projects_html else ''}

  {f'<div class="section"><div class="sec-heading">Education</div>{edu_html}</div>' if edu_html else ''}

  {f'<div class="section"><div class="sec-heading">Certifications & Credentials</div>{cert_html}</div>' if cert_html else ''}
</div>
</body>
</html>
"""

    def _render_cv_executive(
        self,
        resume: ResumeData,
        highlight_diff: bool = False,
        base_resume: Optional[ResumeData] = None,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        if base_resume is None:
            try:
                from .resume_store import resume_store
                base_resume = resume_store.get_base_resume()
            except Exception:
                pass

        base_bullets_by_company = {}
        all_base_bullets = []
        base_scopes_by_company = {}
        base_projects_by_name = {}
        if base_resume:
            for b_exp in base_resume.experience:
                c_key = b_exp.company.strip().lower()
                base_bullets_by_company.setdefault(c_key, []).extend(b_exp.highlights)
                all_base_bullets.extend(b_exp.highlights)
                if getattr(b_exp, "scope", None):
                    base_scopes_by_company[c_key] = b_exp.scope
            for b_proj in (getattr(base_resume, "projects", None) or []):
                p_key = b_proj.name.strip().lower()
                base_projects_by_name[p_key] = b_proj.description

        use_icons = config.show_icons if config is not None else True
        contacts = []
        if resume.email:
            icon = "✉ " if use_icons else ""
            contacts.append(f'<span class="contact-item">{icon}{resume.email}</span>')
        if resume.phone:
            icon = "☎ " if use_icons else ""
            contacts.append(f'<span class="contact-item">{icon}{resume.phone}</span>')
        if resume.location:
            icon = "📍 " if use_icons else ""
            contacts.append(f'<span class="contact-item">{icon}{resume.location}</span>')
        if resume.linkedin:
            icon = "🔗 " if use_icons else ""
            l_href, _ = self._format_url(resume.linkedin, "linkedin")
            contacts.append(f'<a href="{l_href}" target="_blank" rel="noopener noreferrer" class="contact-item">{icon}LinkedIn</a>')
        if resume.github:
            icon = "💻 " if use_icons else ""
            g_href, _ = self._format_url(resume.github, "github")
            contacts.append(f'<a href="{g_href}" target="_blank" rel="noopener noreferrer" class="contact-item">{icon}GitHub</a>')
        if getattr(resume, "portfolio", None):
            icon = "🌐 " if use_icons else ""
            p_href, _ = self._format_url(resume.portfolio, "portfolio")
            contacts.append(f'<a href="{p_href}" target="_blank" rel="noopener noreferrer" class="contact-item">{icon}Portfolio</a>')
        contact_html = " &bull; ".join(contacts)

        target_role = format_job_title(getattr(resume, "target_role", None) or resume.title or "Target Role")
        target_company = getattr(resume, "target_company", None) or "Target Organization"

        # Key target keywords for diff highlighting
        target_terms = set()
        if target_role:
            for w in re.findall(r"\b[A-Za-z0-9#\+\.]+\b", target_role.lower()):
                if len(w) > 2 and w not in ("and", "for", "the", "developer", "engineer"):
                    target_terms.add(w)
        for cat, slist in (resume.skills or {}).items():
            for s in slist[:4]:
                target_terms.add(s.lower())

        # Top Diff Legend Bar
        diff_legend_html = ""
        if highlight_diff:
            diff_legend_html = f"""
            <div class="cv-diff-banner avoid-break" style="background:#f8fafc; border:1px solid #e2e8f0; border-left:4px solid var(--primary-color); border-radius:4px; padding:6px 12px; margin-bottom:12px; font-size:8pt; color:var(--text-primary);">
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:6px;">
                    <span style="font-weight:700; color:var(--primary-color);">DIFF VIEW ACTIVE &bull; Showing customized keyword alignment for {target_role or "target role"}</span>
                    <span style="font-size:7.5pt; color:var(--text-muted);">Tailored Profile</span>
                </div>
            </div>
            """

        # Target Alignment Callout Banner
        target_str = f"<strong>{target_role}</strong>"
        if target_company:
            target_str += f" &bull; <span class='target-company'>{target_company}</span>"
        target_banner_html = f"""
        <div class="cv-target-banner avoid-break">
            <span class="target-badge">TARGET ROLE ALIGNMENT</span>
            <span class="target-details">{target_str}</span>
        </div>
        """

        # Section 1: Why Company? (1-2 cohesive, inspiring paragraphs)
        why_company_raw = getattr(resume, "why_company", None)
        if not why_company_raw:
            why_company_raw = (
                f"{target_company}'s mission to transform scalable software solutions and your culture of "
                f"engineering excellence and architectural autonomy resonate strongly with my professional philosophy. "
                f"As a Senior Frontend Architect who thrives on solving complex challenges at scale, I am energized by {target_company}'s "
                f"focus on building high-reliability platforms. Joining your organization represents an exceptional opportunity to contribute "
                f"to transformative products while collaborating with a world-class engineering team."
            )
        base_why_comp = ""
        rendered_why_company = (
            self.diff_text(why_company_raw, base_why_comp, target_terms)
            if highlight_diff
            else why_company_raw
        )
        why_comp_badge = ""
        why_comp_paras = [p.strip() for p in rendered_why_company.split("\n\n") if p.strip()]
        why_comp_html = "".join([f'<p class="letter-text">{p}</p>' for p in why_comp_paras])

        # Section 2: Why I am the Ideal Fit for Role? (1-2 impactful paragraphs)
        why_fit_raw = getattr(resume, "why_fit", None)
        if not why_fit_raw:
            why_fit_raw = (
                f"With over 7 years of engineering depth leading frontend architecture and high-performance web applications, "
                f"I bring a verified track record directly aligned with the technical demands of the {target_role} position. "
                f"Having architected enterprise Nx monorepos, spearheaded zero-downtime migrations to modern reactive paradigms "
                f"(Signals, standalone components, and Angular 20), and cut build cycles by 25–35%, I understand how to deliver resilient, "
                f"maintainable systems at scale. Furthermore, my substantial experience collaborating with distributed European engineering "
                f"teams—including Dutch enterprise clients like Maistering B.V. and AVEVA—ensures I will hit the ground running, elevate code "
                f"quality, and drive velocity across your engineering organization."
            )
        base_summary = base_resume.summary if base_resume else ""
        rendered_why_fit = (
            self.diff_text(why_fit_raw, base_summary, target_terms)
            if highlight_diff
            else why_fit_raw
        )
        why_fit_badge = ""
        why_fit_paras = [p.strip() for p in rendered_why_fit.split("\n\n") if p.strip()]
        why_fit_html = "".join([f'<p class="letter-text">{p}</p>' for p in why_fit_paras])

        # Section 3: Scope & Leadership Highlights from Experience
        scope_callouts = []
        for exp in resume.experience:
            c_key = exp.company.strip().lower()
            scope_text = getattr(exp, "scope", None)
            if scope_text:
                base_scope = base_scopes_by_company.get(c_key, "")
                rendered_scope = (
                    self.diff_text(scope_text, base_scope, target_terms)
                    if highlight_diff
                    else scope_text
                )
                scope_tag = '<span class="scope-tag">SCOPE &amp; LEADERSHIP:</span>'

                env_pills = ""
                if getattr(exp, "technologies", None):
                    pills = "".join([f'<span class="tech-badge sm">{t}</span>' for t in exp.technologies])
                    env_pills = f'<div class="role-env-box"><span class="env-label">Environment:</span><div class="env-pills">{pills}</div></div>'

                # Bullet points
                b_html = ""
                relevant_base_bullets = base_bullets_by_company.get(c_key, all_base_bullets)
                for h in exp.highlights[:2]:
                    if highlight_diff:
                        h_rendered, is_mod, has_kw = self.diff_bullet(h, relevant_base_bullets, target_terms)
                        cls = "highlighted-bullet" if is_mod or has_kw else ""
                        b_html += f'<li class="{cls}">{h_rendered}</li>\n'
                    else:
                        b_html += f'<li>{h}</li>\n'

                scope_callouts.append(f"""
                <div class="cv-scope-item avoid-break">
                    <div class="scope-hdr">
                        <span class="scope-title">{exp.role}</span>
                        <span class="entry-sep">|</span>
                        <span class="scope-company">{exp.company}</span>
                        <span class="scope-period">({exp.period})</span>
                    </div>
                    <div class="role-scope-box">
                        {scope_tag}
                        <span class="scope-text">{rendered_scope}</span>
                    </div>
                    <ul class="entry-bullets">
                        {b_html}
                    </ul>
                    {env_pills}
                </div>
                """)

        # Flagship Architectural Projects / Case Studies
        valid_cv_projects = [
            p for p in (getattr(resume, "projects", None) or [])
            if p.name and p.name.strip() and p.description and p.description.strip()
        ]
        project_callouts = []
        for p in valid_cv_projects:
            p_role = f'<span class="case-study-role">{p.role}</span>' if p.role else ""
            p_period = f'<span class="entry-period">{p.period}</span>' if p.period else ""
            tech_badges = ""
            if p.technologies:
                badges = "".join([f'<span class="tech-badge">{t}</span>' for t in p.technologies])
                tech_badges = f"""
                <div class="case-study-stack">
                    <span class="stack-label">Architecture Stack:</span>
                    <div class="tech-stack-list">{badges}</div>
                </div>
                """
            base_p_desc = base_projects_by_name.get(p.name.strip().lower(), "")
            rendered_p_desc = (
                self.diff_text(p.description, base_p_desc, target_terms)
                if highlight_diff and p.description
                else p.description
            )
            project_callouts.append(f"""
            <div class="cv-project-card avoid-break">
                <div class="entry-header">
                    <div class="case-study-title-group">
                        <span class="entry-title">{p.name}</span>
                        {f'<span class="entry-sep">|</span> {p_role}' if p_role else ''}
                    </div>
                    {p_period}
                </div>
                <p class="project-desc">{rendered_p_desc}</p>
                {tech_badges}
            </div>
            """)

        # Certifications
        certifications = getattr(resume, "certifications", None) or []
        cert_items = []
        for c in certifications:
            c_issuer = f'<span class="entry-subtitle">{c.issuer}</span>' if c.issuer else ""
            c_period_val = c.date or c.year
            c_date = f'<span class="entry-period">{c_period_val}</span>' if c_period_val else ""
            c_cred = f'<span class="cred-id">Credential ID: {c.credential_id}</span>' if c.credential_id else ""
            cert_items.append(f"""
            <div class="cv-cert-item avoid-break">
                <div class="entry-header">
                    <div>
                        <span class="entry-title">{c.name}</span>
                        {f'<span class="entry-sep">|</span> {c_issuer}' if c_issuer else ''}
                        {f'<span class="entry-sep">|</span> {c_cred}' if c_cred else ''}
                    </div>
                    {c_date}
                </div>
            </div>
            """)

        # Education
        edu_items = []
        for edu in resume.education:
            edu_items.append(f"""
            <div class="cv-edu-item avoid-break">
                <div class="entry-header">
                    <div>
                        <span class="entry-title">{edu.degree}</span>
                        <span class="entry-sep">|</span>
                        <span class="entry-subtitle">{edu.institution}</span>
                    </div>
                    <span class="entry-period">{edu.period}</span>
                </div>
            </div>
            """)

        # Publications
        publications = getattr(resume, "publications", None) or []
        pub_items = "".join([f'<li class="avoid-break">{pub}</li>' for pub in publications])

        # Technical Taxonomy Cards
        skill_cards = ""
        source_skills = resume.skills
        if (not source_skills or not any(source_skills.values())) and base_resume and base_resume.skills:
            source_skills = base_resume.skills

        for cat_name, skill_list in (source_skills or {}).items():
            formatted_cat = cat_name.replace("_", " ").title()
            pills = []
            for s in skill_list:
                is_matched = highlight_diff and (s.lower() in target_terms or any(t in s.lower() for t in target_terms if len(t) > 3))
                matched_cls = " matched" if is_matched else ""
                pills.append(f'<span class="competency-pill{matched_cls}">{s}</span>')
            skill_cards += f"""
            <div class="competency-card avoid-break">
                <div class="competency-title">{formatted_cat}</div>
                <div class="competency-pills">{''.join(pills)}</div>
            </div>
            """

        # European Enterprise Spotlight Banner
        has_european_exp = any(
            "maistering" in exp.company.lower() or "aveva" in exp.company.lower() or "europe" in exp.company.lower()
            for exp in resume.experience
        ) or "netherlands" in (resume.summary or "").lower() or "netherlands" in why_fit_raw.lower() or "netherlands" in (resume.raw_text or "").lower()

        european_spotlight_html = ""
        if has_european_exp:
            european_spotlight_html = """
            <div class="cv-european-banner avoid-break">
                <div class="eu-content">
                    <strong>European Enterprise &amp; International Delivery:</strong>
                    Proven engineering track record delivering scalable web platforms for European clients, including Dutch enterprise organization Maistering B.V. (Netherlands) and AVEVA.
                </div>
            </div>
            """

        current_date_str = datetime.now().strftime("%B %d, %Y")

        display_name = resume.name.title() if (resume.name and (resume.name.isupper() or resume.name.islower())) else resume.name
        display_title = format_job_title(resume.title)
        display_tagline = re.sub(r"\s*•?\s*Aligned for\s+[^•]+", "", resume.tagline or "", flags=re.IGNORECASE).strip(" •")
        tagline_html = f" • {display_tagline}" if (config is None or config.show_tagline) and display_tagline else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{resume.name} - Curriculum Vitae &amp; Statement of Strategic Alignment</title>
{self.GOOGLE_FONTS_TAG}
<style>
  :root {{
    --primary-color: #0f172a;
    --accent-color: #1e3a8a;
    --accent-light: #2563eb;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    --border-color: #cbd5e1;
    --border-subtle: #e2e8f0;
    --bg-page: #f8fafc;
    --bg-card: #ffffff;
    --highlight-bg: #fef08a;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: var(--text-primary);
    background: transparent;
    line-height: 1.5;
    padding: 0;
    margin: 0;
  }}
  .paper, .resume-paper {{
    max-width: 860px;
    margin: 0 auto;
    background: var(--bg-card);
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 40px 48px;
    box-shadow: 0 4px 24px -2px rgba(15, 23, 42, 0.12);
    border-top: 4px solid var(--accent-color);
  }}
  .header-top-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4px;
  }}
  .header-doc-type {{
    font-size: 8pt;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    background: var(--primary-color);
    padding: 3px 8px;
    border-radius: 3px;
  }}
  .header {{
    margin-bottom: 14px;
  }}
  .name {{
    font-size: 24pt;
    font-weight: 800;
    color: var(--primary-color);
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin-bottom: 2px;
  }}
  .title-tagline {{
    font-size: 11pt;
    font-weight: 600;
    color: #475569;
    margin-bottom: 8px;
  }}
  .contacts {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px 16px;
    font-size: 8.5pt;
    color: var(--text-muted);
    padding-top: 4px;
  }}
  .contact-item {{
    display: inline-flex;
    align-items: center;
  }}
  .contacts a {{
    color: var(--accent-light);
    text-decoration: none;
    font-weight: 500;
  }}
  .cv-addressee-block {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
    background: #f8fafc;
    border: 1px solid var(--border-subtle);
    border-left: 4px solid var(--accent-color);
    border-radius: 0 4px 4px 0;
    padding: 12px 16px;
    margin: 14px 0 16px 0;
  }}
  .addressee-left {{
    font-size: 9pt;
    color: var(--text-primary);
  }}
  .meta-date {{
    font-size: 8pt;
    color: var(--text-muted);
    font-weight: 600;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .addressee-to {{
    font-size: 9.5pt;
    color: var(--primary-color);
  }}
  .addressee-company {{
    font-size: 11pt;
    font-weight: 700;
    color: var(--accent-color);
  }}
  .addressee-right {{
    text-align: right;
  }}
  .subject-line {{
    font-size: 10pt;
    color: var(--primary-color);
  }}
  .subject-role {{
    color: var(--accent-color);
    font-weight: 700;
  }}
  .subject-sub {{
    font-size: 8pt;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
  }}
  .cv-target-banner {{
    display: flex;
    align-items: center;
    gap: 10px;
    background: #f8fafc;
    border: 1px solid var(--border-subtle);
    border-left: 4px solid var(--accent-color);
    padding: 8px 14px;
    border-radius: 0 4px 4px 0;
    margin: 10px 0 14px 0;
  }}
  .target-badge {{
    font-size: 7.5pt;
    font-weight: 800;
    color: #ffffff;
    background: var(--primary-color);
    padding: 2px 7px;
    border-radius: 3px;
    letter-spacing: 0.8px;
    white-space: nowrap;
  }}
  .target-details {{
    font-size: 9.5pt;
    color: var(--text-primary);
  }}
  .target-company {{
    color: var(--accent-color);
    font-weight: 600;
  }}
  .cv-intel-box {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #16a34a;
    border-radius: 0 4px 4px 0;
    padding: 10px 14px;
    margin-bottom: 18px;
  }}
  .intel-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }}
  .intel-badge {{
    font-size: 7.5pt;
    font-weight: 800;
    color: #15803d;
    background: #dcfce7;
    padding: 2px 7px;
    border-radius: 3px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
  }}
  .intel-source {{
    font-size: 7.5pt;
    color: #166534;
    font-weight: 600;
  }}
  .intel-body {{
    font-size: 8.5pt;
    color: var(--text-primary);
    line-height: 1.45;
  }}
  .intel-item {{
    margin-bottom: 3px;
  }}
  .cv-section {{
    margin-bottom: 22px;
  }}
  .section-title {{
    font-size: 10.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--accent-color);
    border-bottom: 1.5px solid var(--border-color);
    padding-bottom: 4px;
    margin-bottom: 10px;
  }}
  .cv-letter-box {{
    background: #f8fafc;
    border-left: 4px solid var(--accent-color);
    padding: 14px 18px;
    border-radius: 0 4px 4px 0;
    margin-bottom: 14px;
  }}
  .letter-text {{
    font-size: 9.5pt;
    color: var(--text-primary);
    line-height: 1.65;
    text-align: justify;
  }}
  .cv-scope-item {{
    margin-bottom: 14px;
    background: #ffffff;
    border: 1px solid var(--border-subtle);
    border-radius: 4px;
    padding: 10px 14px;
  }}
  .scope-hdr {{
    font-size: 9.5pt;
    color: var(--primary-color);
    margin-bottom: 4px;
  }}
  .scope-title {{
    font-weight: 700;
  }}
  .scope-company {{
    color: var(--accent-color);
    font-weight: 600;
  }}
  .scope-period {{
    font-size: 8pt;
    color: var(--text-muted);
    margin-left: 4px;
  }}
  .role-scope-box {{
    background: #f8fafc;
    border-left: 3px solid var(--accent-color);
    padding: 6px 10px;
    margin: 6px 0 8px 0;
    border-radius: 0 3px 3px 0;
    font-size: 8.5pt;
    line-height: 1.45;
  }}
  .scope-tag {{
    font-weight: 700;
    color: var(--accent-color);
    font-size: 7.5pt;
    letter-spacing: 0.5px;
    margin-right: 4px;
  }}
  .scope-text {{
    color: #1e293b;
  }}
  .entry-bullets {{
    margin-left: 18px;
    font-size: 9pt;
    color: var(--text-primary);
    line-height: 1.5;
  }}
  .entry-bullets li {{
    margin-bottom: 3px;
  }}
  .role-env-box {{
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
    padding-left: 2px;
  }}
  .env-label {{
    font-size: 7.5pt;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }}
  .env-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .tech-badge {{
    background: #e2e8f0;
    color: #334155;
    font-size: 7.5pt;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 3px;
  }}
  .tech-badge.sm {{
    font-size: 7pt;
    padding: 1px 5px;
  }}
  .cv-project-card {{
    background: #f8fafc;
    border: 1px solid var(--border-subtle);
    border-left: 4px solid var(--accent-color);
    padding: 10px 14px;
    border-radius: 0 4px 4px 0;
    margin-bottom: 10px;
  }}
  .entry-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4px;
  }}
  .case-study-title-group {{
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .entry-title {{
    font-size: 10pt;
    font-weight: 700;
    color: var(--primary-color);
  }}
  .entry-sep {{
    color: var(--border-color);
    margin: 0 3px;
  }}
  .entry-subtitle {{
    font-size: 9.5pt;
    font-weight: 600;
    color: var(--accent-color);
  }}
  .case-study-role {{
    font-size: 8.5pt;
    font-weight: 600;
    color: var(--accent-light);
  }}
  .entry-period {{
    font-size: 8pt;
    font-weight: 600;
    color: var(--text-muted);
  }}
  .entry-link {{
    font-size: 8pt;
    color: var(--accent-light);
    text-decoration: none;
    font-weight: 600;
  }}
  .project-desc {{
    font-size: 8.5pt;
    color: var(--text-primary);
    margin: 4px 0 6px 0;
    line-height: 1.45;
  }}
  .case-study-stack {{
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 4px;
  }}
  .stack-label {{
    font-size: 7.5pt;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
  }}
  .tech-stack-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .competency-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 8px;
    margin-bottom: 12px;
  }}
  .competency-card {{
    background: #f8fafc;
    border: 1px solid var(--border-subtle);
    border-radius: 4px;
    padding: 8px 10px;
  }}
  .competency-title {{
    font-size: 8pt;
    font-weight: 700;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 2px;
  }}
  .competency-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .competency-pill {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #334155;
    font-size: 7.5pt;
    font-weight: 600;
    padding: 1px 5px;
    border-radius: 3px;
  }}
  .competency-pill.matched {{
    background: #f0fdf4 !important;
    border: 1px solid #86efac !important;
    color: #166534 !important;
    font-weight: 700 !important;
  }}
  .cv-cert-item, .cv-edu-item {{
    padding: 4px 0;
    border-bottom: 1px dashed var(--border-subtle);
  }}
  .cred-id {{
    font-size: 7.5pt;
    color: var(--text-muted);
    font-family: ui-monospace, monospace;
  }}
  .cv-european-banner {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 4px solid #1e3a8a;
    border-radius: 0 4px 4px 0;
    padding: 8px 12px;
    margin: 12px 0;
  }}
  .eu-flag-box {{
    font-size: 16pt;
    line-height: 1;
  }}
  .eu-content {{
    font-size: 8.5pt;
    color: #1e3a8a;
    line-height: 1.4;
  }}
  .cv-signoff-block {{
    margin-top: 24px;
    padding-top: 14px;
    border-top: 1px solid var(--border-subtle);
  }}
  .signoff-salutation {{
    font-size: 9.5pt;
    color: var(--text-muted);
    font-style: italic;
    margin-bottom: 8px;
  }}
  .signoff-name {{
    font-size: 13pt;
    font-weight: 800;
    color: var(--primary-color);
  }}
  .signoff-title {{
    font-size: 9.5pt;
    font-weight: 600;
    color: var(--accent-color);
    margin-bottom: 6px;
  }}
  .cv-footer {{
    margin-top: 24px;
    padding-top: 10px;
    border-top: 1px solid var(--border-subtle);
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: var(--text-muted);
  }}
  /* Diff Highlighting */
  .cv-diff-banner {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 8px 12px;
    margin-bottom: 14px;
  }}
  .diff-banner-header {{
    font-size: 8pt;
    color: #0f172a;
    margin-bottom: 4px;
  }}
  .diff-legend-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 7.5pt;
  }}
  .legend-pill {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #ffffff;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
  }}
  .pill-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }}
  .pill-dot.bg-emerald {{ background: #10b981; }}
  .pill-dot.bg-amber {{ background: #f59e0b; }}
  .pill-dot.bg-sky {{ background: #0ea5e9; }}
  .pill-dot.bg-slate {{ background: #64748b; }}
  .diff-box-badge {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }}
  .diff-chip {{
    font-size: 7.5pt;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 3px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .diff-chip.added {{
    background: #dcfce7;
    color: #15803d;
    border: 1px solid #bbf7d0;
  }}
  .highlighted-bullet.mod {{
    background-color: #fef3c7;
    border-left: 3px solid #f59e0b;
    padding: 2px 6px;
    margin-bottom: 4px;
    border-radius: 0 3px 3px 0;
  }}
  .highlighted-bullet.kw {{
    background-color: #f0f9ff;
    border-left: 3px solid #0284c7;
    padding: 2px 6px;
    margin-bottom: 4px;
    border-radius: 0 3px 3px 0;
  }}
  .diff-bullet-badge {{
    font-size: 7pt;
    font-weight: 800;
    padding: 1px 4px;
    border-radius: 2px;
    text-transform: uppercase;
    margin-right: 4px;
    letter-spacing: 0.4px;
  }}
  .diff-bullet-badge.mod {{
    background: #fde68a;
    color: #92400e;
  }}
  .diff-bullet-badge.kw {{
    background: #bae6fd;
    color: #0369a1;
  }}
  .diff-pill {{
    font-size: 7pt;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    margin-left: 6px;
    text-transform: uppercase;
  }}
  .diff-pill.target {{
    background: #dbeafe;
    color: #1e40af;
  }}
  .diff-pill.scope {{
    background: #dcfce7;
    color: #15803d;
  }}
  del.git-diff-del {{
    background-color: #ffebe9 !important;
    color: #cf222e !important;
    text-decoration: line-through !important;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #ffc1ba;
    font-size: 0.95em;
    margin-right: 3px;
    display: inline;
  }}
  ins.git-diff-ins, mark.diff-text-added, mark.diff-text-adapted {{
    background-color: #dafbe1 !important;
    color: #116329 !important;
    text-decoration: none !important;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #86efac;
    font-weight: 600;
    display: inline;
  }}
  mark.diff-text-adapted {{
    background-color: #fef08a !important;
    color: #713f12 !important;
    border-color: #fde047;
  }}
  .diff-sign {{
    user-select: none;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 800;
    margin-right: 2px;
  }}
  del.git-diff-del .diff-sign {{ color: #cf222e; }}
  ins.git-diff-ins .diff-sign {{ color: #116329; }}
  mark.diff-kw-term {{
    background-color: #bae6fd !important;
    color: #0369a1 !important;
    font-weight: 600;
    border-radius: 3px;
    padding: 1px 4px;
    box-shadow: 0 0 0 1px #7dd3fc;
    text-decoration: none;
  }}
  strong.diff-kw-match {{
    color: #0369a1 !important;
    font-weight: 800 !important;
    text-decoration: underline;
  }}
  .avoid-break {{
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  @media print {{
    body {{
      background: #ffffff;
      padding: 0;
    }}
    .paper {{
      box-shadow: none;
      padding: 0;
      max-width: 100%;
      border-top: none;
    }}
    .cv-diff-banner {{ display: none !important; }}
    .diff-bullet-badge {{ display: none !important; }}
    .diff-pill {{ display: none !important; }}
    .diff-box-badge {{ display: none !important; }}
    .cv-project-card {{
      background: #f8fafc;
      border-left: 3px solid #1e3a8a;
    }}
    .highlighted-bullet.mod, .highlighted-bullet.kw, .highlighted-bullet {{
      background-color: transparent !important;
      border-left: none !important;
      padding: 0 !important;
      font-weight: 600;
    }}
    del.git-diff-del {{ display: none !important; }}
    ins.git-diff-ins, mark.diff-text-added, mark.diff-text-adapted, mark.diff-kw-term {{
      background-color: transparent !important;
      color: inherit !important;
      font-weight: inherit !important;
      box-shadow: none !important;
      border: none !important;
      padding: 0 !important;
      text-decoration: none !important;
    }}
    .diff-sign {{ display: none !important; }}
    strong.diff-kw-match {{
      color: inherit !important;
      font-weight: inherit !important;
      text-decoration: none !important;
    }}
    @page {{
      margin: 14mm 14mm 14mm 14mm;
      size: A4 portrait;
    }}
  }}
  {self._build_dynamic_styles(config)}
</style>
</head>
<body>
<div class="resume-paper paper">
  {diff_legend_html}
  <header class="header">
    <div class="header-info">
      <div class="header-top-row">
        <h1 class="name">{display_name}</h1>
        <span class="header-doc-type">Curriculum Vitae</span>
      </div>
      <div class="title-tagline">{display_title}{tagline_html}</div>
    </div>
    <div class="contacts">{contact_html}</div>
  </header>

  <div class="cv-addressee-block avoid-break">
    <div class="addressee-left">
      <div class="meta-date">{current_date_str}</div>
      <div class="addressee-to"><strong>To:</strong> Hiring Leadership &amp; Selection Committee</div>
      <div class="addressee-company">{target_company}</div>
    </div>
    <div class="addressee-right">
      <div class="subject-line"><strong>RE:</strong> Application for <span class="subject-role">{target_role}</span></div>
      <div class="subject-sub">Statement of Strategic Alignment</div>
    </div>
  </div>

  {target_banner_html}

  <div class="cv-section section avoid-break">
    <div class="section-title">Strategic Motivation &amp; Alignment — Why {target_company}?</div>
    <div class="cv-letter-box">
      {why_comp_badge}
      {why_comp_html}
    </div>
  </div>

  <div class="cv-section section avoid-break">
    <div class="section-title">Executive Value Proposition — Fit for {target_role}</div>
    <div class="cv-letter-box">
      {why_fit_badge}
      {why_fit_html}
    </div>
  </div>

  <div class="cv-section section">
    <div class="section-title">Key Strategic Competencies &amp; Architectural Wins</div>
    {''.join(scope_callouts)}
    {''.join(project_callouts) if (config is None or config.show_projects) else ''}
  </div>

  <div class="cv-section section avoid-break">
    <div class="section-title">Verified Credentials &amp; Academic Foundation</div>
    {f'<div class="competency-grid">{skill_cards}</div>' if skill_cards else ''}
    {''.join(cert_items) if (config is None or config.show_certifications) and cert_items else ''}
    {''.join(edu_items) if (config is None or config.show_education) and edu_items else ''}
    {f'<ul class="entry-bullets" style="margin-top:8px;">{pub_items}</ul>' if pub_items else ''}
    {european_spotlight_html}
  </div>

  <div class="cv-signoff-block avoid-break">
    <div class="signoff-salutation">Respectfully submitted,</div>
    <div class="signoff-name">{display_name}</div>
    <div class="signoff-title">{display_title or target_role}</div>
  </div>

  <footer class="cv-footer avoid-break">
    <span>Curriculum Vitae &bull; {display_name}</span>
    <span>Tailored Application &bull; {target_company}</span>
  </footer>
</div>
</body>
</html>
"""

    def _render_compact(
        self,
        resume: ResumeData,
        highlight_diff: bool = False,
        base_resume: Optional[ResumeData] = None,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        # Compact single/two page layout
        cfg = config.model_copy() if config else TemplateConfig(template_id="compact", density="compact")
        cfg.density = "compact"
        return self._render_modern(resume, highlight_diff, base_resume, config=cfg)


template_engine = TemplateEngine()
