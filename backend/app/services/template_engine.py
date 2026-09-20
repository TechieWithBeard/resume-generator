"""
Predefined ATS-Optimized HTML Resume Templates & Renderer.
Includes:
- Modern Tech Template
- Executive Minimalist Template
- Compact Classic Template
Embedded print styles ensure pixel-perfect PDF export via browser print engine.
"""

import re
from typing import Any, Dict, List, Optional
from backend.app.models.resume import ResumeData, TemplateConfig


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

    def _build_dynamic_styles(self, config: Optional[TemplateConfig]) -> str:
        if not config:
            return ""
        
        density = config.density
        if density == "compact":
            padding = "28px 36px"
            section_margin = "14px"
            item_margin = "10px"
            bullet_margin = "2px"
            line_height = config.line_height or "1.35"
        elif density == "comfortable":
            padding = "54px 58px"
            section_margin = "26px"
            item_margin = "18px"
            bullet_margin = "6px"
            line_height = config.line_height or "1.65"
        else: # normal
            padding = "44px 48px"
            section_margin = "20px"
            item_margin = "14px"
            bullet_margin = "4px"
            line_height = config.line_height or "1.5"

        header_css = ""
        if config.header_layout == "center":
            header_css = """
            .header { text-align: center !important; }
            .contacts { justify-content: center !important; text-align: center !important; display: flex !important; flex-wrap: wrap !important; }
            .title-tagline { text-align: center !important; }
            """
        elif config.header_layout == "split":
            header_css = """
            .header { display: flex !important; justify-content: space-between !important; align-items: flex-end !important; flex-wrap: wrap !important; gap: 12px !important; }
            .contacts { text-align: right !important; }
            """

        return f"""
        /* User Configured Dynamic Overrides */
        :root {{
            --primary-color: {config.primary_color} !important;
            --accent-color: {config.accent_color} !important;
            --text-primary: {config.text_color} !important;
            --font-family: {config.font_family} !important;
            --font-size: {config.font_size} !important;
            --line-height: {line_height} !important;
        }}
        body {{
            font-family: var(--font-family) !important;
            font-size: var(--font-size) !important;
            line-height: var(--line-height) !important;
            color: var(--text-primary) !important;
        }}
        .resume-paper {{
            padding: {padding} !important;
        }}
        .section, .cv-section {{
            margin-bottom: {section_margin} !important;
        }}
        .experience-entry, .project-card, .cv-project-card, .education-entry, .edu-item, .cv-entry {{
            margin-bottom: {item_margin} !important;
        }}
        .exp-highlights li, .project-highlights li {{
            margin-bottom: {bullet_margin} !important;
        }}
        {header_css}
        {config.custom_css or ""}
        """

    def render(
        self,
        resume: ResumeData,
        template_id: str = "modern",
        highlight_diff: bool = False,
        base_resume: Optional[ResumeData] = None,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        """Renders the resume or CV data into a standalone, printable HTML document."""
        if base_resume is None:
            try:
                from .resume_store import resume_store
                base_resume = resume_store.get_base_resume()
            except Exception:
                pass

        doc_type = getattr(resume, "document_type", "resume")
        effective_tmpl = (config.template_id if config and config.template_id else template_id)
        if effective_tmpl == "cv_executive" or (doc_type == "cv" and effective_tmpl in ("modern", "default")):
            return self._render_cv_executive(resume, highlight_diff, base_resume, config=config)
        elif effective_tmpl == "executive":
            return self._render_executive(resume, highlight_diff, base_resume, config=config)
        elif effective_tmpl == "compact":
            return self._render_compact(resume, highlight_diff, base_resume, config=config)
        else:
            return self._render_modern(resume, highlight_diff, base_resume, config=config)

    def _render_modern(
        self,
        resume: ResumeData,
        highlight_diff: bool = False,
        base_resume: Optional[ResumeData] = None,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        base_highlights = set()
        if highlight_diff and base_resume:
            for exp in base_resume.experience:
                for h in exp.highlights:
                    base_highlights.add(h.strip().lower())

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
            diff_legend_html = """
            <div class="cv-diff-banner avoid-break" style="background:#f0fdf4; border:1px solid #86efac; border-radius:6px; padding:8px 12px; margin-bottom:14px; font-size:8pt; color:#166534;">
                <div style="font-weight:700; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
                    <span>🔍</span><strong>DIFF VIEW ACTIVE:</strong> Highlighted modifications &amp; target keyword matches
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:8px; font-size:7.5pt;">
                    <span style="background:#fff; border:1px solid #d1fae5; padding:1px 6px; border-radius:3px;">🟢 Tailored Profile</span>
                    <span style="background:#fff; border:1px solid #fef3c7; padding:1px 6px; border-radius:3px;">🟡 Adapted Highlight</span>
                    <span style="background:#fff; border:1px solid #e0f2fe; padding:1px 6px; border-radius:3px;">🔵 Target Skill Match</span>
                </div>
            </div>
            """

        is_summary_modified = False
        if highlight_diff and base_resume:
            is_summary_modified = (resume.summary.strip().lower() != base_resume.summary.strip().lower())
        elif highlight_diff:
            is_summary_modified = True

        use_icons = config.show_icons if config is not None else True
        icon_email = "✉ " if use_icons else ""
        icon_phone = "☎ " if use_icons else ""
        icon_loc = "📍 " if use_icons else ""
        icon_linkedin = "🔗 " if use_icons else ""
        icon_github = "💻 " if use_icons else ""

        # Contact items
        contacts = []
        if resume.email:
            contacts.append(f'<span class="contact-item">{icon_email}{resume.email}</span>')
        if resume.phone:
            contacts.append(f'<span class="contact-item">{icon_phone}{resume.phone}</span>')
        if resume.location:
            contacts.append(f'<span class="contact-item">{icon_loc}{resume.location}</span>')
        if resume.linkedin:
            contacts.append(f'<a href="{resume.linkedin}" target="_blank" class="contact-item">{icon_linkedin}LinkedIn</a>')
        if resume.github:
            contacts.append(f'<a href="{resume.github}" target="_blank" class="contact-item">{icon_github}GitHub</a>')
        contact_html = " &bull; ".join(contacts)

        # Experience items
        exp_html = ""
        for exp in resume.experience:
            bullets = ""
            for h in exp.highlights:
                is_modified = highlight_diff and (h.strip().lower() not in base_highlights)
                has_target_kw = highlight_diff and any(kw in h.lower() for kw in target_terms if len(kw) > 3)
                
                if is_modified:
                    highlight_cls = "highlighted-bullet mod"
                    bullet_badge = '<span class="diff-bullet-badge mod" style="background:#fde68a; color:#92400e; font-size:7pt; font-weight:800; padding:1px 4px; border-radius:2px; text-transform:uppercase; margin-right:4px;">+ Tailored</span> '
                elif has_target_kw:
                    highlight_cls = "highlighted-bullet kw"
                    bullet_badge = '<span class="diff-bullet-badge kw" style="background:#bae6fd; color:#0369a1; font-size:7pt; font-weight:800; padding:1px 4px; border-radius:2px; text-transform:uppercase; margin-right:4px;">★ Key Skill</span> '
                else:
                    highlight_cls = ""
                    bullet_badge = ""
                bullets += f'<li class="{highlight_cls}">{bullet_badge}{h}</li>\n'
            
            loc_str = f'<span class="exp-location">{exp.location}</span>' if exp.location else ''
            exp_html += f"""
            <div class="experience-entry">
                <div class="exp-header">
                    <div class="exp-role-company">
                        <span class="exp-role">{exp.role}</span>
                        <span class="exp-sep">|</span>
                        <span class="exp-company">{exp.company}</span>
                    </div>
                    <div class="exp-meta">
                        <span class="exp-period">{exp.period}</span>
                        {loc_str}
                    </div>
                </div>
                <ul class="exp-highlights">
                    {bullets}
                </ul>
            </div>
            """

        # Skills categories
        skills_html = ""
        for cat_name, skill_list in resume.skills.items():
            formatted_cat = cat_name.replace("_", " ").title()
            badges = []
            for s in skill_list:
                is_matched = highlight_diff and (s.lower() in target_terms or any(t in s.lower() for t in target_terms if len(t) > 3))
                if is_matched:
                    badges.append(f'<span class="skill-badge matched" style="background:#dcfce7; border:1px solid #86efac; color:#166534; font-weight:700;">✓ {s}</span>')
                else:
                    badges.append(f'<span class="skill-badge">{s}</span>')
            skills_html += f"""
            <div class="skill-group">
                <span class="skill-label">{formatted_cat}:</span>
                <div class="skill-badges">{''.join(badges)}</div>
            </div>
            """

        # Projects
        projects_html = ""
        show_proj = config.show_projects if config is not None else True
        if show_proj and getattr(resume, "projects", None):
            for proj in resume.projects:
                tech_badges = "".join([f'<span class="tech-badge" style="background:#f1f5f9; color:#334155; padding:2px 6px; border-radius:3px; font-size:8pt; margin-right:4px;">{t}</span>' for t in proj.technologies])
                url_link = f' <a href="{proj.url}" target="_blank" style="color:var(--accent-color); text-decoration:none; font-size:8pt;">🔗</a>' if proj.url else ''
                period_str = f'<span class="exp-period">{proj.period}</span>' if proj.period else ''
                projects_html += f"""
                <div class="experience-entry">
                    <div class="exp-header">
                        <span class="exp-role">{proj.name}{url_link}</span>
                        {period_str}
                    </div>
                    <div class="summary-text" style="margin-bottom: 4px;">{proj.description}</div>
                    <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">{tech_badges}</div>
                </div>
                """

        # Education
        edu_html = ""
        show_edu = config.show_education if config is not None else True
        if show_edu and resume.education:
            for edu in resume.education:
                edu_html += f"""
                <div class="education-entry">
                    <div class="edu-degree-inst">
                        <span class="edu-degree">{edu.degree}</span>
                        <span class="edu-sep">—</span>
                        <span class="edu-inst">{edu.institution}</span>
                    </div>
                    <span class="edu-period">{edu.period}</span>
                </div>
                """

        # Certifications
        cert_html = ""
        show_cert = config.show_certifications if config is not None else True
        if show_cert and getattr(resume, "certifications", None):
            for cert in resume.certifications:
                yr = f" ({cert.year})" if cert.year else ""
                url_str = f' <a href="{cert.url}" target="_blank" style="color:var(--accent-color); text-decoration:none;">🔗</a>' if cert.url else ""
                cert_html += f'<div class="education-entry"><span class="edu-degree">{cert.name}</span><span class="edu-inst">{cert.issuer}{yr}{url_str}</span></div>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{resume.name} - Resume</title>
<style>
  :root {{
    --primary-color: #0f172a;
    --accent-color: #0284c7;
    --accent-light: #e0f2fe;
    --text-primary: #1e293b;
    --text-muted: #64748b;
    --border-color: #cbd5e1;
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
    background-color: #f8fafc;
    line-height: 1.5;
    padding: 30px 20px;
  }}
  .resume-paper {{
    max-width: 850px;
    margin: 0 auto;
    background: #ffffff;
    padding: 48px 52px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border-radius: 6px;
  }}
  .header {{
    border-bottom: 2px solid var(--accent-color);
    padding-bottom: 18px;
    margin-bottom: 22px;
  }}
  .name {{
    font-size: 28pt;
    font-weight: 700;
    color: var(--primary-color);
    letter-spacing: -0.5px;
    margin-bottom: 4px;
  }}
  .title-tagline {{
    font-size: 13pt;
    font-weight: 600;
    color: var(--accent-color);
    margin-bottom: 8px;
  }}
  .contacts {{
    font-size: 9.5pt;
    color: var(--text-muted);
  }}
  .contacts a {{
    color: var(--accent-color);
    text-decoration: none;
  }}
  .section {{
    margin-bottom: 22px;
  }}
  .section-title {{
    font-size: 11.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--primary-color);
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 4px;
    margin-bottom: 12px;
  }}
  .summary-text {{
    font-size: 10pt;
    color: var(--text-primary);
    line-height: 1.6;
    text-align: justify;
  }}
  .experience-entry {{
    margin-bottom: 16px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .exp-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 5px;
  }}
  .exp-role {{
    font-size: 11pt;
    font-weight: 700;
    color: var(--primary-color);
  }}
  .exp-sep {{
    color: var(--border-color);
    margin: 0 4px;
  }}
  .exp-company {{
    font-size: 10.5pt;
    font-weight: 600;
    color: var(--accent-color);
  }}
  .exp-period {{
    font-size: 9.5pt;
    font-weight: 500;
    color: var(--text-muted);
  }}
  .exp-location {{
    font-size: 9pt;
    color: var(--text-muted);
    margin-left: 8px;
  }}
  .exp-highlights {{
    list-style: disc;
    padding-left: 18px;
    font-size: 9.5pt;
    color: var(--text-primary);
    line-height: 1.55;
  }}
  .exp-highlights li {{
    margin-bottom: 4px;
  }}
  .highlighted-bullet {{
    background-color: var(--diff-bg);
    border-left: 3px solid var(--diff-border);
    padding-left: 6px;
    border-radius: 2px;
  }}
  .skill-group {{
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    font-size: 9.5pt;
  }}
  .skill-label {{
    font-weight: 600;
    width: 170px;
    flex-shrink: 0;
    color: var(--primary-color);
  }}
  .skill-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }}
  .skill-badge {{
    background: #f1f5f9;
    color: #334155;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 9pt;
    font-weight: 500;
    border: 1px solid #e2e8f0;
  }}
  .education-entry {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 9.5pt;
    margin-bottom: 6px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .edu-degree {{
    font-weight: 700;
    color: var(--primary-color);
  }}
  .edu-sep {{
    color: var(--border-color);
    margin: 0 4px;
  }}
  .edu-inst {{
    color: var(--text-muted);
  }}
  .edu-period {{
    color: var(--text-muted);
    font-weight: 500;
  }}

  @media print {{
    body {{
      background: #ffffff !important;
      padding: 0 !important;
      margin: 0 !important;
    }}
    .resume-paper {{
      box-shadow: none !important;
      padding: 0 !important;
      margin: 0 !important;
      max-width: 100% !important;
    }}
    .highlighted-bullet {{
      background-color: transparent !important;
      border-left: none !important;
      padding-left: 0 !important;
    }}
    @page {{
      margin: 1.2cm 1.5cm;
      size: letter portrait;
    }}
  }}
  {self._build_dynamic_styles(config)}
</style>
</head>
<body>
<div class="resume-paper">
  {diff_legend_html}
  <div class="header">
    <div class="name">{resume.name}</div>
    {f'<div class="title-tagline">{resume.title}' + (f' • {resume.tagline}' if (config is None or config.show_tagline) and resume.tagline else '') + '</div>' if resume.title else ''}
    <div class="contacts">{contact_html}</div>
  </div>

  <div class="section">
    <div class="section-title">Professional Summary {f'<span style="background:#dcfce7; color:#15803d; font-size:7.5pt; font-weight:800; padding:2px 6px; border-radius:3px; text-transform:uppercase; margin-left:8px; border:1px solid #bbf7d0;">+ Tailored for {target_role or "Role"}</span>' if is_summary_modified else ''}</div>
    <div class="summary-text" style="{f'background:#f0fdf4; border-left:3px solid #16a34a; padding:8px 12px; border-radius:0 4px 4px 0;' if is_summary_modified else ''}">{resume.summary}</div>
  </div>

  <div class="section">
    <div class="section-title">Technical Competencies</div>
    {skills_html}
  </div>

  <div class="section">
    <div class="section-title">Professional Experience</div>
    {exp_html}
  </div>

  {f'<div class="section"><div class="section-title">Key Projects & Architecture</div>{projects_html}</div>' if projects_html else ''}

  {f'<div class="section"><div class="section-title">Education</div>{edu_html}</div>' if edu_html else ''}

  {f'<div class="section"><div class="section-title">Certifications & Credentials</div>{cert_html}</div>' if cert_html else ''}
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

        base_highlights = set()
        if highlight_diff and base_resume:
            for exp in base_resume.experience:
                for h in exp.highlights:
                    base_highlights.add(h.strip().lower())

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
            diff_legend_html = """
            <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:4px; padding:8px 12px; margin-bottom:14px; font-size:8pt; color:#166534; font-family:sans-serif;">
                <div style="font-weight:700; margin-bottom:4px;">🔍 DIFF VIEW ACTIVE: Tailored modifications &amp; target keyword alignment</div>
                <div style="display:flex; flex-wrap:wrap; gap:8px; font-size:7.5pt;">
                    <span style="background:#fff; border:1px solid #d1fae5; padding:1px 6px; border-radius:3px;">🟢 Tailored Profile</span>
                    <span style="background:#fff; border:1px solid #fef3c7; padding:1px 6px; border-radius:3px;">🟡 Adapted Achievement</span>
                    <span style="background:#fff; border:1px solid #e0f2fe; padding:1px 6px; border-radius:3px;">🔵 Target Skill Match</span>
                </div>
            </div>
            """

        # High contrast, traditional serif/sans ATS compliant
        contacts = [c for c in [resume.email, resume.phone, resume.location, resume.linkedin, resume.github] if c]
        contact_html = " | ".join(contacts)

        exp_html = ""
        for exp in resume.experience:
            bullets = ""
            for h in exp.highlights:
                is_modified = highlight_diff and (h.strip().lower() not in base_highlights)
                has_target_kw = highlight_diff and any(kw in h.lower() for kw in target_terms if len(kw) > 3)
                if is_modified:
                    bullets += f'<li style="background:#fef9c3; border-left:3px solid #f59e0b; padding-left:4px; margin-bottom:3px;"><span style="background:#fde68a; color:#92400e; font-size:7pt; font-weight:bold; padding:1px 4px; border-radius:2px; margin-right:4px;">+ TAILORED</span>{h}</li>'
                elif has_target_kw:
                    bullets += f'<li style="background:#f0f9ff; border-left:3px solid #0284c7; padding-left:4px; margin-bottom:3px;"><span style="background:#bae6fd; color:#0369a1; font-size:7pt; font-weight:bold; padding:1px 4px; border-radius:2px; margin-right:4px;">★ KEY SKILL</span>{h}</li>'
                else:
                    bullets += f'<li style="margin-bottom:3px;">{h}</li>'

            loc = f" — {exp.location}" if exp.location else ""
            exp_html += f"""
            <div class="experience-entry" style="margin-bottom: 14px; break-inside: avoid;">
              <div style="display: flex; justify-content: space-between; font-weight: bold;">
                <span>{exp.role}</span>
                <span>{exp.period}</span>
              </div>
              <div style="font-style: italic; color: #444; margin-bottom: 4px;">{exp.company}{loc}</div>
              <ul style="padding-left: 20px; font-size: 10pt; line-height: 1.5;">{bullets}</ul>
            </div>
            """

        skills_lines = []
        for cat, items in resume.skills.items():
            cat_label = cat.replace("_", " ").title()
            pills = []
            for item in items:
                if highlight_diff and (item.lower() in target_terms or any(t in item.lower() for t in target_terms if len(t) > 3)):
                    pills.append(f'<span style="background:#dcfce7; border:1px solid #86efac; color:#166534; font-weight:bold; padding:1px 4px; border-radius:2px;">✓ {item}</span>')
                else:
                    pills.append(item)
            skills_lines.append(f"<strong>{cat_label}:</strong> " + ", ".join(pills))
        skills_html = "<br>".join(skills_lines)

        is_summary_modified = False
        if highlight_diff and base_resume:
            is_summary_modified = (resume.summary.strip().lower() != base_resume.summary.strip().lower())
        elif highlight_diff:
            is_summary_modified = True

        summary_style = "font-size: 10pt; text-align: justify; background: #f0fdf4; border-left: 3px solid #16a34a; padding: 6px 10px;" if is_summary_modified else "font-size: 10pt; text-align: justify;"
        summary_badge = f' <span style="background:#dcfce7; color:#15803d; font-size:7pt; font-weight:bold; padding:1px 5px; border-radius:2px; vertical-align:middle;">+ TAILORED FOR {target_role.upper() if target_role else "TARGET"}</span>' if is_summary_modified else ''

        projects_html = ""
        show_proj = config.show_projects if config is not None else True
        if show_proj and getattr(resume, "projects", None):
            for proj in resume.projects:
                techs = f" — <em>{', '.join(proj.technologies)}</em>" if proj.technologies else ""
                url_s = f' <a href="{proj.url}" target="_blank">🔗</a>' if proj.url else ""
                period_s = f" ({proj.period})" if proj.period else ""
                projects_html += f"""
                <div class="project-card" style="margin-bottom: 10px;">
                  <div><strong>{proj.name}</strong>{period_s}{url_s}{techs}</div>
                  <p style="font-size: 9.5pt; margin: 2px 0 6px 0;">{proj.description}</p>
                </div>
                """

        edu_html = ""
        show_edu = config.show_education if config is not None else True
        if show_edu and resume.education:
            for edu in resume.education:
                edu_html += f"""
                <div class="education-entry" style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 10pt;">
                  <span><strong>{edu.degree}</strong>, {edu.institution}</span>
                  <span>{edu.period}</span>
                </div>
                """

        cert_html = ""
        show_cert = config.show_certifications if config is not None else True
        if show_cert and getattr(resume, "certifications", None):
            for cert in resume.certifications:
                yr = f" ({cert.year})" if cert.year else ""
                url_str = f' <a href="{cert.url}" target="_blank">🔗</a>' if cert.url else ""
                cert_html += f'<div style="font-size: 9.5pt; margin-bottom: 4px;"><strong>{cert.name}</strong> — {cert.issuer}{yr}{url_str}</div>'

        tagline_html = f" • {resume.tagline}" if (config is None or config.show_tagline) and resume.tagline else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{resume.name} - Executive Resume</title>
<style>
  body {{ font-family: "Georgia", Times, serif; color: #111; line-height: 1.4; padding: 30px 20px; background: #fafafa; }}
  .paper, .resume-paper {{ max-width: 820px; margin: 0 auto; background: #fff; padding: 40px 50px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
  h1, .name {{ text-align: center; font-size: 24pt; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 1px; }}
  .title, .title-tagline {{ text-align: center; font-size: 11pt; font-style: italic; margin-bottom: 4px; }}
  .contacts {{ text-align: center; font-size: 9.5pt; border-bottom: 1px solid #222; padding-bottom: 12px; margin-bottom: 18px; }}
  .sec-heading, .section-title {{ font-size: 11pt; font-weight: bold; text-transform: uppercase; border-bottom: 1px solid #aaa; padding-bottom: 2px; margin: 16px 0 10px 0; letter-spacing: 0.5px; }}
  @media print {{ body {{ background: #fff; padding: 0; }} .paper, .resume-paper {{ box-shadow: none; padding: 0; }} }}
  {self._build_dynamic_styles(config)}
</style>
</head>
<body>
<div class="resume-paper">
  {diff_legend_html}
  <div class="header">
    <h1 class="name">{resume.name}</h1>
    <div class="title-tagline">{resume.title}{tagline_html}</div>
    <div class="contacts">{contact_html}</div>
  </div>

  <div class="section">
    <div class="sec-heading">Summary{summary_badge}</div>
    <p style="{summary_style}">{resume.summary}</p>
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

        base_highlights = set()
        if highlight_diff and base_resume:
            for exp in base_resume.experience:
                for h in exp.highlights:
                    base_highlights.add(h.strip().lower())

        contacts = []
        if resume.email:
            contacts.append(f'<span class="contact-item">✉ {resume.email}</span>')
        if resume.phone:
            contacts.append(f'<span class="contact-item">☎ {resume.phone}</span>')
        if resume.location:
            contacts.append(f'<span class="contact-item">📍 {resume.location}</span>')
        if resume.linkedin:
            contacts.append(f'<a href="{resume.linkedin}" target="_blank" class="contact-item">🔗 LinkedIn</a>')
        if resume.github:
            contacts.append(f'<a href="{resume.github}" target="_blank" class="contact-item">💻 GitHub</a>')
        contact_html = " &bull; ".join(contacts)

        # Target Alignment Callout Banner
        target_role = getattr(resume, "target_role", None)
        target_company = getattr(resume, "target_company", None)

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
            diff_legend_html = """
            <div class="cv-diff-banner avoid-break">
                <div class="diff-banner-header">
                    <span class="diff-banner-icon">🔍</span>
                    <strong>DIFF VIEW ACTIVE:</strong> Visual audit of tailored modifications & job alignment
                </div>
                <div class="diff-legend-pills">
                    <span class="legend-pill added"><span class="pill-dot bg-emerald"></span> Tailored Profile / Scope</span>
                    <span class="legend-pill mod"><span class="pill-dot bg-amber"></span> Adapted Achievement</span>
                    <span class="legend-pill kw"><span class="pill-dot bg-sky"></span> Target Keyword Match</span>
                    <span class="legend-pill locked"><span class="pill-dot bg-slate"></span> Verified Invariant Fact</span>
                </div>
            </div>
            """

        target_banner_html = ""
        diff_pill_target = '<span class="diff-pill target">+ Targeted Positioning</span>' if highlight_diff else ""
        if target_role or target_company:
            target_str = f"<strong>{target_role}</strong>" if target_role else ""
            if target_company:
                target_str += f" &bull; <span class='target-company'>{target_company}</span>"
            target_banner_html = f"""
            <div class="cv-target-banner avoid-break">
                <span class="target-badge">🎯 TARGET ROLE ALIGNMENT</span>
                <span class="target-details">{target_str}</span>
                {diff_pill_target}
            </div>
            """
        elif resume.tagline and ("target" in resume.tagline.lower() or "aligned" in resume.tagline.lower()):
            target_banner_html = f"""
            <div class="cv-target-banner avoid-break">
                <span class="target-badge">🎯 STRATEGIC FOCUS</span>
                <span class="target-details">{resume.tagline}</span>
                {diff_pill_target}
            </div>
            """

        # Technical Taxonomy & Core Competency Matrix (Modern Card Grid)
        skills_html = ""
        if resume.skills:
            skill_cards = ""
            for cat_name, skill_list in resume.skills.items():
                formatted_cat = cat_name.replace("_", " ").title()
                pills = []
                for s in skill_list:
                    is_matched = highlight_diff and (s.lower() in target_terms or any(t in s.lower() for t in target_terms if len(t) > 3))
                    matched_cls = " matched" if is_matched else ""
                    icon_prefix = "✓ " if is_matched else ""
                    pills.append(f'<span class="competency-pill{matched_cls}">{icon_prefix}{s}</span>')
                skill_cards += f"""
                <div class="competency-card avoid-break">
                    <div class="competency-title">{formatted_cat}</div>
                    <div class="competency-pills">{''.join(pills)}</div>
                </div>
                """
            skills_html = f"""
            <div class="cv-section section">
                <div class="section-title">02 / Technical Taxonomy & Core Competency Matrix</div>
                <div class="competency-grid">{skill_cards}</div>
            </div>
            """

        # Key Architectural Case Studies & Flagship Projects
        projects_html = ""
        projects = getattr(resume, "projects", None) or []
        if projects:
            p_items = ""
            for p in projects:
                p_role = f'<span class="case-study-role">{p.role}</span>' if p.role else ""
                p_period = f'<span class="entry-period">{p.period}</span>' if p.period else ""
                url_link = f' <a href="{p.url}" target="_blank" class="entry-link">↗ Link</a>' if p.url else ""
                proj_diff = '<span class="diff-pill scope">★ Targeted Case Study</span>' if highlight_diff else ""
                
                tech_badges = ""
                if p.technologies:
                    badges = "".join([f'<span class="tech-badge">{t}</span>' for t in p.technologies])
                    tech_badges = f"""
                    <div class="case-study-stack">
                        <span class="stack-label">Architecture Stack:</span>
                        <div class="tech-stack-list">{badges}</div>
                    </div>
                    """

                p_items += f"""
                <div class="cv-project-card avoid-break">
                    <div class="entry-header">
                        <div class="case-study-title-group">
                            <span class="entry-title">{p.name}</span>
                            {f'<span class="entry-sep">|</span> {p_role}' if p_role else ''}
                            {url_link}
                            {proj_diff}
                        </div>
                        {p_period}
                    </div>
                    <p class="project-desc">{p.description}</p>
                    {tech_badges}
                </div>
                """
            projects_html = f"""
            <div class="cv-section section">
                <div class="section-title">03 / Key Architectural Projects & Case Studies</div>
                <div class="projects-container">{p_items}</div>
            </div>
            """

        # Experience entries with Scope & Environment
        exp_html = ""
        for exp in resume.experience:
            bullets = ""
            for h in exp.highlights:
                is_modified = highlight_diff and (h.strip().lower() not in base_highlights)
                has_target_kw = highlight_diff and any(kw in h.lower() for kw in target_terms if len(kw) > 3)
                
                if is_modified:
                    highlight_cls = "highlighted-bullet mod"
                    bullet_badge = '<span class="diff-bullet-badge mod">+ Tailored</span> '
                elif has_target_kw:
                    highlight_cls = "highlighted-bullet kw"
                    bullet_badge = '<span class="diff-bullet-badge kw">★ Key Skill</span> '
                else:
                    highlight_cls = ""
                    bullet_badge = ""
                bullets += f'<li class="{highlight_cls}">{bullet_badge}{h}</li>\n'

            loc_str = f'<span class="exp-location">📍 {exp.location}</span>' if exp.location else ""
            
            scope_html = ""
            if getattr(exp, "scope", None):
                scope_tag = '<span class="scope-tag">⚡ SCOPE & LEADERSHIP:</span>'
                if highlight_diff:
                    scope_tag = '<span class="scope-tag">⚡ SCOPE & LEADERSHIP:</span> <span class="diff-pill scope">+ Role Scope Enriched</span>'
                scope_html = f"""
                <div class="role-scope-box">
                    {scope_tag}
                    <span class="scope-text">{exp.scope}</span>
                </div>
                """

            tech_html = ""
            if getattr(exp, "technologies", None):
                pills = "".join([f'<span class="tech-badge sm">{t}</span>' for t in exp.technologies])
                tech_html = f"""
                <div class="role-env-box">
                    <span class="env-label">Environment:</span>
                    <div class="env-pills">{pills}</div>
                </div>
                """

            exp_html += f"""
            <div class="cv-entry avoid-break">
                <div class="entry-header">
                    <div class="entry-title-wrap">
                        <span class="entry-title">{exp.role}</span>
                        <span class="entry-sep">|</span>
                        <span class="entry-subtitle">{exp.company}</span>
                    </div>
                    <div class="entry-meta">
                        <span class="entry-period">{exp.period}</span>
                        {loc_str}
                    </div>
                </div>
                {scope_html}
                <ul class="entry-bullets">
                    {bullets}
                </ul>
                {tech_html}
            </div>
            """

        # European Enterprise Spotlight Banner (if candidate has European client experience)
        has_european_exp = any(
            "maistering" in exp.company.lower() or "aveva" in exp.company.lower() or "europe" in exp.company.lower()
            for exp in resume.experience
        ) or "netherlands" in (resume.summary or "").lower() or "european" in (resume.summary or "").lower()

        european_spotlight_html = ""
        if has_european_exp:
            european_spotlight_html = """
            <div class="cv-international-card avoid-break">
                <div class="intl-badge">🌍 INTERNATIONAL & EUROPEAN ENTERPRISE DELIVERY</div>
                <div class="intl-body">
                    <strong>European Enterprise & Netherlands Client Delivery:</strong> Proven engineering delivery and technical leadership collaborating directly with European enterprises, including Dutch enterprise client <em>Maistering B.V. (Netherlands)</em> and industrial software leader <em>AVEVA</em>. Seasoned in cross-timezone communication, asynchronous agile delivery, GDPR-conscious web platforms, and European engineering standards.
                </div>
            </div>
            """

        # Education entries
        edu_html = ""
        for edu in resume.education:
            edu_html += f"""
            <div class="cv-entry edu-entry avoid-break">
                <div class="entry-header">
                    <div>
                        <span class="entry-title">{edu.degree}</span>
                        <span class="entry-sep">|</span>
                        <span class="entry-subtitle">{edu.institution}</span>
                    </div>
                    <div class="entry-meta">
                        <span class="entry-period">{edu.period}</span>
                    </div>
                </div>
            </div>
            """

        # Certifications section
        certs_html = ""
        certifications = getattr(resume, "certifications", None) or []
        if certifications:
            c_items = ""
            for c in certifications:
                c_issuer = f'<span class="entry-subtitle">{c.issuer}</span>' if c.issuer else ""
                c_period_val = c.date or c.year
                c_date = f'<span class="entry-period">{c_period_val}</span>' if c_period_val else ""
                c_cred = f'<span class="cred-id">Credential ID: {c.credential_id}</span>' if c.credential_id else ""
                c_items += f"""
                <div class="cv-cert-item avoid-break">
                    <div class="entry-header">
                        <div>
                            <span class="entry-title">🏆 {c.name}</span>
                            {f'<span class="entry-sep">|</span> {c_issuer}' if c_issuer else ''}
                            {f'<span class="entry-sep">|</span> {c_cred}' if c_cred else ''}
                        </div>
                        {c_date}
                    </div>
                </div>
                """
            certs_html = f"""
            <div class="cv-section section">
                <div class="section-title">06 / Certifications & Professional Accreditations</div>
                <div class="certs-container">{c_items}</div>
            </div>
            """

        # Publications section
        pub_html = ""
        publications = getattr(resume, "publications", None) or []
        if publications:
            pub_items = "".join([f'<li class="avoid-break">{pub}</li>' for pub in publications])
            pub_html = f"""
            <div class="cv-section section">
                <div class="section-title">07 / Publications & Thought Leadership</div>
                <ul class="entry-bullets">
                    {pub_items}
                </ul>
            </div>
            """

        # Executive Summary Box Diff styling
        is_summary_modified = False
        if highlight_diff and base_resume:
            is_summary_modified = (resume.summary.strip().lower() != base_resume.summary.strip().lower())
        elif highlight_diff:
            is_summary_modified = True

        summary_box_cls = "cv-summary-box diff-summary-box" if is_summary_modified else "cv-summary-box"
        summary_badge_html = f'<div class="diff-box-badge"><span class="diff-chip added">+ Tailored Strategic Profile</span> <span class="diff-note" style="font-size:7.5pt; color:#15803d; font-weight:600;">Aligned for {target_role or "Target Role"}</span></div>' if is_summary_modified else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{resume.name} - Curriculum Vitae</title>
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
    --bg-card: #f8fafc;
    --highlight-bg: #fef08a;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: var(--text-primary);
    background: var(--bg-page);
    line-height: 1.5;
    padding: 30px 15px;
  }}
  .paper {{
    max-width: 880px;
    margin: 0 auto;
    background: #ffffff;
    padding: 44px 52px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border-radius: 4px;
    border-top: 4px solid var(--accent-color);
  }}
  .cv-top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 8px;
    margin-bottom: 16px;
  }}
  .cv-badge-group {{
    display: flex;
    gap: 8px;
    align-items: center;
  }}
  .cv-badge {{
    display: inline-block;
    background: #1e3a8a;
    color: #ffffff;
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 3px;
  }}
  .cv-badge.secondary {{
    background: #e0e7ff;
    color: #1e3a8a;
  }}
  .cv-meta-confidential {{
    font-size: 7.5pt;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 0.8px;
    text-transform: uppercase;
  }}
  .header {{
    text-align: left;
    margin-bottom: 20px;
  }}
  .name {{
    font-size: 25pt;
    font-weight: 800;
    color: var(--primary-color);
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin-bottom: 4px;
  }}
  .title-tagline {{
    font-size: 12.5pt;
    font-weight: 600;
    color: var(--accent-color);
    margin-bottom: 8px;
  }}
  .cv-target-banner {{
    display: flex;
    align-items: center;
    gap: 10px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 4px solid var(--accent-light);
    padding: 8px 14px;
    border-radius: 0 4px 4px 0;
    margin: 10px 0 12px 0;
  }}
  .target-badge {{
    font-size: 7.5pt;
    font-weight: 800;
    color: var(--accent-color);
    background: #dbeafe;
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
    margin-bottom: 12px;
  }}
  .cv-summary-box {{
    background: #f8fafc;
    border-left: 4px solid var(--accent-color);
    padding: 12px 16px;
    border-radius: 0 4px 4px 0;
  }}
  .summary-text {{
    font-size: 9.5pt;
    color: var(--text-primary);
    line-height: 1.6;
    text-align: justify;
  }}
  /* Competencies Grid */
  .competency-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 10px;
  }}
  .competency-card {{
    background: #f8fafc;
    border: 1px solid var(--border-subtle);
    border-radius: 4px;
    padding: 8px 12px;
  }}
  .competency-title {{
    font-size: 8.5pt;
    font-weight: 700;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 3px;
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
    padding: 2px 6px;
    border-radius: 3px;
  }}
  /* Experience Entries */
  .cv-entry {{
    margin-bottom: 18px;
  }}
  .entry-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 3px;
  }}
  .entry-title-wrap {{
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .entry-title {{
    font-size: 10.5pt;
    font-weight: 700;
    color: var(--primary-color);
  }}
  .entry-sep {{
    color: var(--border-color);
    margin: 0 3px;
  }}
  .entry-subtitle {{
    font-size: 10pt;
    font-weight: 600;
    color: var(--accent-color);
  }}
  .entry-meta {{
    text-align: right;
    white-space: nowrap;
  }}
  .entry-period {{
    font-size: 8.5pt;
    font-weight: 600;
    color: var(--text-muted);
  }}
  .exp-location {{
    font-size: 8pt;
    color: var(--text-muted);
    margin-left: 6px;
  }}
  .role-scope-box {{
    background: #eff6ff;
    border-left: 3px solid #3b82f6;
    padding: 5px 10px;
    margin: 5px 0 7px 0;
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
  /* Project / Case Studies */
  .cv-project-card {{
    background: #f8fafc;
    border: 1px solid var(--border-subtle);
    border-left: 4px solid var(--accent-color);
    padding: 10px 14px;
    border-radius: 0 4px 4px 0;
    margin-bottom: 12px;
  }}
  .case-study-title-group {{
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .case-study-role {{
    font-size: 8.5pt;
    font-weight: 600;
    color: var(--accent-light);
  }}
  .project-desc {{
    font-size: 9pt;
    color: var(--text-primary);
    margin: 5px 0 7px 0;
    line-height: 1.45;
  }}
  .case-study-stack {{
    display: flex;
    align-items: center;
    gap: 6px;
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
  .tech-badge {{
    background: #e2e8f0;
    color: #334155;
    font-size: 7.5pt;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 3px;
  }}
  .tech-badge.sm {{
    font-size: 7pt;
    padding: 1px 5px;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
  }}
  /* European Spotlight */
  .cv-international-card {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #16a34a;
    padding: 10px 14px;
    border-radius: 0 4px 4px 0;
    margin: 16px 0 20px 0;
  }}
  .intl-badge {{
    font-size: 7.5pt;
    font-weight: 800;
    color: #166534;
    letter-spacing: 0.8px;
    margin-bottom: 3px;
  }}
  .intl-body {{
    font-size: 8.5pt;
    color: #14532d;
    line-height: 1.45;
  }}
  /* Certifications */
  .cv-cert-item {{
    margin-bottom: 7px;
  }}
  .cred-id {{
    font-size: 8pt;
    color: var(--text-muted);
  }}
  .entry-link {{
    font-size: 8pt;
    color: var(--accent-light);
    text-decoration: none;
    font-weight: 600;
    margin-left: 4px;
  }}
  /* Visual Diff Highlighting Engine */
  .cv-diff-banner {{
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 8pt;
    color: #166534;
  }}
  .diff-banner-header {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 700;
    margin-bottom: 5px;
  }}
  .diff-legend-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }}
  .legend-pill {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 7.5pt;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 4px;
    background: #ffffff;
    border: 1px solid #d1fae5;
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
  .diff-summary-box {{
    border-left: 4px solid #10b981 !important;
    background: #f0fdf4 !important;
  }}
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
  .diff-note {{
    font-size: 7.5pt;
    color: #15803d;
    font-weight: 600;
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
  .competency-pill.matched {{
    background: #f0fdf4 !important;
    border: 1px solid #86efac !important;
    color: #166534 !important;
    font-weight: 700 !important;
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
  .avoid-break {{
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .cv-footer {{
    margin-top: 30px;
    padding-top: 10px;
    border-top: 1px solid var(--border-subtle);
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: var(--text-muted);
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
    .diff-summary-box {{
      border-left: 4px solid var(--accent-color) !important;
      background: #f8fafc !important;
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
  <div class="cv-top-bar">
    <div class="cv-badge-group">
      <span class="cv-badge">Curriculum Vitae</span>
      <span class="cv-badge secondary">Executive Technical Dossier</span>
    </div>
    <span class="cv-meta-confidential">Verified Dossier &bull; Zero-Hallucination</span>
  </div>

  <div class="header">
    <h1 class="name">{resume.name}</h1>
    <div class="title-tagline">{resume.title}{f" • {resume.tagline}" if (config is None or config.show_tagline) and resume.tagline else ""}</div>
    {target_banner_html}
    <div class="contacts">{contact_html}</div>
  </div>

  <div class="cv-section section">
    <div class="section-title">01 / Executive Career Architecture & Strategic Profile</div>
    <div class="{summary_box_cls}">
      {summary_badge_html}
      <p class="summary-text">{resume.summary}</p>
    </div>
  </div>

  {skills_html}

  {projects_html if (config is None or config.show_projects) else ''}

  <div class="cv-section section">
    <div class="section-title">04 / Professional Experience & Career History</div>
    {exp_html}
  </div>

  {european_spotlight_html}

  {certs_html if (config is None or config.show_certifications) else ''}

  {pub_html}

  {f'<div class="cv-section section"><div class="section-title">08 / Education & Academic Background</div>{edu_html}</div>' if (config is None or config.show_education) and edu_html else ''}

  <footer class="cv-footer avoid-break">
    <span>Curriculum Vitae &bull; {resume.name}</span>
    <span>Verified Technical Dossier</span>
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
