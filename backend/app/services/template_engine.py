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
            .header { text-align: center !important; display: block !important; }
            .name, h1 { text-align: center !important; }
            .contacts { justify-content: center !important; text-align: center !important; display: flex !important; flex-wrap: wrap !important; gap: 8px !important; }
            .title-tagline { text-align: center !important; }
            """
        elif config.header_layout == "split":
            header_css = """
            .header { display: flex !important; justify-content: space-between !important; align-items: flex-end !important; flex-wrap: wrap !important; gap: 12px !important; text-align: left !important; }
            .name, h1 { text-align: left !important; }
            .contacts { text-align: right !important; justify-content: flex-end !important; display: flex !important; flex-wrap: wrap !important; gap: 8px !important; }
            .title-tagline { text-align: left !important; }
            """
        elif config.header_layout == "left":
            header_css = """
            .header { text-align: left !important; display: block !important; }
            .name, h1 { text-align: left !important; }
            .contacts { justify-content: flex-start !important; text-align: left !important; display: flex !important; flex-wrap: wrap !important; gap: 8px !important; }
            .title-tagline { text-align: left !important; }
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
        body, body * {{
            font-family: var(--font-family) !important;
        }}
        pre, code, .diff-sign, .font-mono, [class*="mono"] {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace !important;
        }}
        body {{
            color: var(--text-primary) !important;
            line-height: var(--line-height) !important;
        }}
        body, p, li, .summary-text, .exp-highlights, .project-highlights, .contacts, .exp-period, .edu-item, .edu-period, .skill-badge {{
            font-size: var(--font-size) !important;
            line-height: var(--line-height) !important;
        }}
        .name, h1, .sec-heading, .section-title, .cv-section-title, .cv-section-title-alt, .cv-project-title, .exp-role, .project-name {{
            color: var(--primary-color) !important;
        }}
        .header, .sec-heading, .section-title, .cv-section-title {{
            border-bottom-color: var(--accent-color) !important;
        }}
        .title-tagline, .title, .exp-company, .cv-project-role, .edu-degree, .target-company, .skill-label {{
            color: var(--accent-color) !important;
        }}
        a, .contacts a {{
            color: var(--primary-color) !important;
        }}
        .cv-badge, .badge, .tag-primary {{
            background-color: var(--primary-color) !important;
            color: #ffffff !important;
        }}
        @media screen {{
            .resume-paper, .paper {{
                padding: {padding} !important;
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
                max-width: 100% !important;
            }}
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

    def highlight_target_terms(self, text: str, target_terms: Set[str]) -> str:
        """Highlights matching target keywords in text."""
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
        Computes word-level diff markup between base_text and new_text.
        - Inserts <mark class="diff-text-added"> for added words.
        - Inserts <mark class="diff-text-adapted"> for adapted/replaced words.
        - Inserts <mark class="diff-kw-term"> for target keyword matches.
        """
        if not new_text:
            return ""
        target_terms = target_terms or set()

        if base_text is None:
            return self.highlight_target_terms(new_text, target_terms)
        if base_text.strip() == new_text.strip():
            return self.highlight_target_terms(new_text, target_terms)

        base_words = base_text.split()
        new_words = new_text.split()

        matcher = difflib.SequenceMatcher(
            None,
            [w.lower() for w in base_words],
            [w.lower() for w in new_words],
        )

        out_tokens = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for w in new_words[j1:j2]:
                    w_clean = re.sub(r"[^\w\+\#]", "", w.lower())
                    if w_clean in target_terms or any(t in w_clean for t in target_terms if len(t) > 3):
                        out_tokens.append(f'<mark class="diff-kw-term">{w}</mark>')
                    else:
                        out_tokens.append(w)
            elif tag == "replace":
                del_chunk = " ".join(base_words[i1:i2])
                sub_tokens = []
                for w in new_words[j1:j2]:
                    w_clean = re.sub(r"[^\w\+\#]", "", w.lower())
                    if w_clean in target_terms or any(t in w_clean for t in target_terms if len(t) > 3):
                        sub_tokens.append(f'<strong class="diff-kw-match">{w}</strong>')
                    else:
                        sub_tokens.append(w)
                ins_chunk = " ".join(sub_tokens)
                del_html = f'<del class="git-diff-del"><span class="diff-sign">-</span>{del_chunk}</del>'
                ins_html = f'<ins class="git-diff-ins diff-text-adapted"><span class="diff-sign">+</span>{ins_chunk}</ins>'
                out_tokens.append(f'{del_html} {ins_html}')
            elif tag == "insert":
                sub_tokens = []
                for w in new_words[j1:j2]:
                    w_clean = re.sub(r"[^\w\+\#]", "", w.lower())
                    if w_clean in target_terms or any(t in w_clean for t in target_terms if len(t) > 3):
                        sub_tokens.append(f'<strong class="diff-kw-match">{w}</strong>')
                    else:
                        sub_tokens.append(w)
                ins_chunk = " ".join(sub_tokens)
                out_tokens.append(f'<ins class="git-diff-ins diff-text-added"><span class="diff-sign">+</span>{ins_chunk}</ins>')
            elif tag == "delete":
                del_chunk = " ".join(base_words[i1:i2])
                out_tokens.append(f'<del class="git-diff-del"><span class="diff-sign">-</span>{del_chunk}</del>')

        return " ".join(out_tokens)

    def diff_bullet(
        self,
        bullet: str,
        base_bullets: List[str],
        target_terms: Set[str],
    ) -> Tuple[str, bool, bool]:
        """
        Compares a tailored bullet against base bullets to find closest match and highlight changes.
        Returns: (highlighted_html, is_modified, has_target_kw)
        """
        b_clean = bullet.strip().lower()
        base_clean_set = {b.strip().lower() for b in base_bullets}
        has_target_kw = any(kw in b_clean for kw in target_terms if len(kw) > 3)

        if b_clean in base_clean_set:
            return self.highlight_target_terms(bullet, target_terms), False, has_target_kw

        closest = difflib.get_close_matches(bullet, base_bullets, n=1, cutoff=0.3)
        if closest:
            diffed = self.diff_text(bullet, closest[0], target_terms)
            return diffed, True, has_target_kw

        sub_tokens = []
        for w in bullet.split():
            w_clean = re.sub(r"[^\w\+\#]", "", w.lower())
            if w_clean in target_terms or any(t in w_clean for t in target_terms if len(t) > 3):
                sub_tokens.append(f'<strong class="diff-kw-match">{w}</strong>')
            else:
                sub_tokens.append(w)
        return f'<ins class="git-diff-ins diff-text-added"><span class="diff-sign">+</span>{" ".join(sub_tokens)}</ins>', True, has_target_kw

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
            <div class="cv-diff-banner avoid-break" style="background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:10px 14px; margin-bottom:16px; font-size:8pt; color:#c9d1d9; font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;">
                <div style="font-weight:700; margin-bottom:6px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:6px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="background:#238636; color:#ffffff; font-size:7pt; font-weight:800; padding:2px 6px; border-radius:3px; letter-spacing:0.5px;">GIT DIFF</span>
                        <span style="color:#58a6ff; font-weight:700;">DIFF VIEW ACTIVE: git diff base_profile &rarr; tailored_profile</span>
                    </div>
                    <span style="color:#8b949e; font-size:7.5pt;">origin/ground-truth &rarr; target/{target_role or "tailored"}</span>
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:8px; font-size:7.5pt;">
                    <span style="background:#ffebe9; color:#cf222e; border:1px solid #ffc1ba; padding:1px 6px; border-radius:3px; font-weight:700;">🔴 - Removed from Base</span>
                    <span style="background:#dafbe1; color:#116329; border:1px solid #86efac; padding:1px 6px; border-radius:3px; font-weight:700;">🟢 + Added / Tailored Profile</span>
                    <span style="background:#ddf4ff; color:#0969da; border:1px solid #54aeff; padding:1px 6px; border-radius:3px; font-weight:700;">🔵 ★ Target Keyword Match</span>
                    <span style="background:#21262d; color:#8b949e; border:1px solid #30363d; padding:1px 6px; border-radius:3px; font-weight:600;">⚪ Invariant Facts Preserved</span>
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
            c_key = exp.company.strip().lower()
            relevant_base_bullets = base_bullets_by_company.get(c_key, all_base_bullets)
            for h in exp.highlights:
                if highlight_diff:
                    h_rendered, is_modified, has_target_kw = self.diff_bullet(h, relevant_base_bullets, target_terms)
                    if is_modified:
                        highlight_cls = "highlighted-bullet mod"
                        bullet_badge = '<span class="diff-bullet-badge mod" style="background:#fde68a; color:#92400e; font-size:7pt; font-weight:800; padding:1px 4px; border-radius:2px; text-transform:uppercase; margin-right:4px;">+ Tailored</span> '
                    elif has_target_kw:
                        highlight_cls = "highlighted-bullet kw"
                        bullet_badge = '<span class="diff-bullet-badge kw" style="background:#bae6fd; color:#0369a1; font-size:7pt; font-weight:800; padding:1px 4px; border-radius:2px; text-transform:uppercase; margin-right:4px;">★ Key Skill</span> '
                    else:
                        highlight_cls = ""
                        bullet_badge = ""
                else:
                    h_rendered = h
                    highlight_cls = ""
                    bullet_badge = ""
                bullets += f'<li class="{highlight_cls}">{bullet_badge}{h_rendered}</li>\n'
            
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
                base_p_desc = base_projects_by_name.get(proj.name.strip().lower(), "")
                rendered_p_desc = (
                    self.diff_text(proj.description, base_p_desc, target_terms)
                    if highlight_diff and proj.description
                    else proj.description
                )
                projects_html += f"""
                <div class="experience-entry">
                    <div class="exp-header">
                        <span class="exp-role">{proj.name}{url_link}</span>
                        {period_str}
                    </div>
                    <div class="summary-text" style="margin-bottom: 4px;">{rendered_p_desc}</div>
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
    <div class="summary-text" style="{f'background:#f0fdf4; border-left:3px solid #16a34a; padding:8px 12px; border-radius:0 4px 4px 0;' if is_summary_modified else ''}">{rendered_summary}</div>
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
            <div class="cv-diff-banner avoid-break" style="background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:10px 14px; margin-bottom:16px; font-size:8pt; color:#c9d1d9; font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;">
                <div style="font-weight:700; margin-bottom:6px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:6px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="background:#238636; color:#ffffff; font-size:7pt; font-weight:800; padding:2px 6px; border-radius:3px; letter-spacing:0.5px;">GIT DIFF</span>
                        <span style="color:#58a6ff; font-weight:700;">DIFF VIEW ACTIVE: git diff base_profile &rarr; tailored_profile</span>
                    </div>
                    <span style="color:#8b949e; font-size:7.5pt;">origin/ground-truth &rarr; target/{target_role or "tailored"}</span>
                </div>
                <div style="display:flex; flex-wrap:gap; gap:8px; font-size:7.5pt;">
                    <span style="background:#ffebe9; color:#cf222e; border:1px solid #ffc1ba; padding:1px 6px; border-radius:3px; font-weight:700;">🔴 - Removed from Base</span>
                    <span style="background:#dafbe1; color:#116329; border:1px solid #86efac; padding:1px 6px; border-radius:3px; font-weight:700;">🟢 + Added / Tailored Profile</span>
                    <span style="background:#ddf4ff; color:#0969da; border:1px solid #54aeff; padding:1px 6px; border-radius:3px; font-weight:700;">🔵 ★ Target Keyword Match</span>
                    <span style="background:#21262d; color:#8b949e; border:1px solid #30363d; padding:1px 6px; border-radius:3px; font-weight:600;">⚪ Invariant Facts Preserved</span>
                </div>
            </div>
            """

        # High contrast, traditional serif/sans ATS compliant
        contacts = [c for c in [resume.email, resume.phone, resume.location, resume.linkedin, resume.github] if c]
        contact_html = " | ".join(contacts)

        exp_html = ""
        for exp in resume.experience:
            bullets = ""
            c_key = exp.company.strip().lower()
            relevant_base_bullets = base_bullets_by_company.get(c_key, all_base_bullets)
            for h in exp.highlights:
                if highlight_diff:
                    h_rendered, is_modified, has_target_kw = self.diff_bullet(h, relevant_base_bullets, target_terms)
                    if is_modified:
                        bullets += f'<li style="background:#fef9c3; border-left:3px solid #f59e0b; padding-left:4px; margin-bottom:3px;"><span style="background:#fde68a; color:#92400e; font-size:7pt; font-weight:bold; padding:1px 4px; border-radius:2px; margin-right:4px;">+ TAILORED</span>{h_rendered}</li>'
                    elif has_target_kw:
                        bullets += f'<li style="background:#f0f9ff; border-left:3px solid #0284c7; padding-left:4px; margin-bottom:3px;"><span style="background:#bae6fd; color:#0369a1; font-size:7pt; font-weight:bold; padding:1px 4px; border-radius:2px; margin-right:4px;">★ KEY SKILL</span>{h_rendered}</li>'
                    else:
                        bullets += f'<li style="margin-bottom:3px;">{h_rendered}</li>'
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

        summary_style = "font-size: 10pt; text-align: justify; background: #f0fdf4; border-left: 3px solid #16a34a; padding: 6px 10px;" if is_summary_modified else "font-size: 10pt; text-align: justify;"
        summary_badge = f' <span style="background:#dcfce7; color:#15803d; font-size:7pt; font-weight:bold; padding:1px 5px; border-radius:2px; vertical-align:middle;">+ TAILORED FOR {target_role.upper() if target_role else "TARGET"}</span>' if is_summary_modified else ''

        projects_html = ""
        show_proj = config.show_projects if config is not None else True
        if show_proj and getattr(resume, "projects", None):
            for proj in resume.projects:
                techs = f" — <em>{', '.join(proj.technologies)}</em>" if proj.technologies else ""
                url_s = f' <a href="{proj.url}" target="_blank">🔗</a>' if proj.url else ""
                period_s = f" ({proj.period})" if proj.period else ""
                base_p_desc = base_projects_by_name.get(proj.name.strip().lower(), "")
                rendered_p_desc = (
                    self.diff_text(proj.description, base_p_desc, target_terms)
                    if highlight_diff and proj.description
                    else proj.description
                )
                projects_html += f"""
                <div class="project-card" style="margin-bottom: 10px;">
                  <div><strong>{proj.name}</strong>{period_s}{url_s}{techs}</div>
                  <p style="font-size: 9.5pt; margin: 2px 0 6px 0;">{rendered_p_desc}</p>
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
    <h1 class="name">{resume.name}</h1>
    <div class="title-tagline">{resume.title}{tagline_html}</div>
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
            contacts.append(f'<a href="{resume.linkedin}" target="_blank" class="contact-item">{icon}LinkedIn</a>')
        if resume.github:
            icon = "💻 " if use_icons else ""
            contacts.append(f'<a href="{resume.github}" target="_blank" class="contact-item">{icon}GitHub</a>')
        contact_html = " &bull; ".join(contacts)

        target_role = getattr(resume, "target_role", None) or resume.title or "Target Role"
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
            diff_legend_html = """
            <div class="cv-diff-banner avoid-break">
                <div class="diff-banner-header">
                    <span class="diff-banner-icon">🔍</span>
                    <strong>DIFF VIEW ACTIVE:</strong> Visual audit of tailored modifications & job alignment
                </div>
                <div class="diff-legend-pills">
                    <span class="legend-pill added"><span class="pill-dot bg-emerald"></span> Tailored Profile / Motivation</span>
                    <span class="legend-pill mod"><span class="pill-dot bg-amber"></span> Adapted Fit & Value Driver</span>
                    <span class="legend-pill kw"><span class="pill-dot bg-sky"></span> Target Keyword Match</span>
                    <span class="legend-pill locked"><span class="pill-dot bg-slate"></span> Verified Ground Truth</span>
                </div>
            </div>
            """

        # Target Alignment Callout Banner
        diff_pill_target = '<span class="diff-pill target">+ Targeted Profile</span>' if highlight_diff else ""
        target_str = f"<strong>{target_role}</strong>"
        if target_company:
            target_str += f" &bull; <span class='target-company'>{target_company}</span>"
        target_banner_html = f"""
        <div class="cv-target-banner avoid-break">
            <span class="target-badge">TARGET ROLE ALIGNMENT</span>
            <span class="target-details">{target_str}</span>
            {diff_pill_target}
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
        why_comp_badge = f'<div class="diff-box-badge"><span class="diff-chip added">+ Tailored Profile</span> <span class="diff-note" style="font-size:7.5pt; color:#15803d; font-weight:600;">Aligned for {target_company}</span></div>' if highlight_diff else ""
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
        why_fit_badge = f'<div class="diff-box-badge"><span class="diff-chip added">+ Tailored Profile</span> <span class="diff-note" style="font-size:7.5pt; color:#15803d; font-weight:600;">Positioned for {target_role}</span></div>' if highlight_diff else ""
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
                if highlight_diff:
                    scope_tag = '<span class="scope-tag">SCOPE &amp; LEADERSHIP:</span> <span class="diff-pill scope">+ Role Scope Enriched</span>'

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
                        cls = "highlighted-bullet mod" if is_mod else ("highlighted-bullet kw" if has_kw else "")
                        b_badge = '<span class="diff-bullet-badge mod">+ Tailored</span> ' if is_mod else ('<span class="diff-bullet-badge kw">★ Key Skill</span> ' if has_kw else "")
                        b_html += f'<li class="{cls}">{b_badge}{h_rendered}</li>\n'
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
        projects = getattr(resume, "projects", None) or []
        project_callouts = []
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
                        {url_link}
                        {proj_diff}
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
        for cat_name, skill_list in (resume.skills or {}).items():
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

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{resume.name} - Curriculum Vitae &amp; Statement of Strategic Alignment</title>
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
  .header-top-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4px;
  }}
  .header-doc-type {{
    font-size: 8pt;
    font-weight: 700;
    color: var(--accent-color);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    background: #e0e7ff;
    padding: 3px 8px;
    border-radius: 3px;
  }}
  .header {{
    text-align: left;
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
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 4px solid var(--accent-light);
    padding: 8px 14px;
    border-radius: 0 4px 4px 0;
    margin: 10px 0 14px 0;
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
    background: #eff6ff;
    border-left: 3px solid #3b82f6;
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
    <div class="header-top-row">
      <h1 class="name">{resume.name}</h1>
      <span class="header-doc-type">Curriculum Vitae</span>
    </div>
    <div class="title-tagline">{resume.title}{f" • {resume.tagline}" if (config is None or config.show_tagline) and resume.tagline else ""}</div>
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
    <div class="signoff-name">{resume.name}</div>
    <div class="signoff-title">{resume.title or target_role}</div>
  </div>

  <footer class="cv-footer avoid-break">
    <span>Curriculum Vitae &bull; {resume.name}</span>
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
