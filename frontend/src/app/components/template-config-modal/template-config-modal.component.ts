import { Component, effect, inject, signal, untracked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { TemplateConfig } from '../../models/resume.models';
import { ModalComponent } from '../../shared/components/modal/modal.component';

export interface ColorPalette {
  name: string;
  primary: string;
  accent: string;
  text: string;
  badgeBg: string;
}

export interface FontOption {
  label: string;
  value: string;
  sample: string;
}

export interface StyleTokenDoc {
  token: string;
  category: 'Colors' | 'Typography' | 'Structure' | 'Diff & Badges';
  description: string;
  example: string;
}

export interface SelectorDoc {
  selector: string;
  description: string;
  recommendedStyles: string;
}

export interface QuickSnippet {
  label: string;
  description: string;
  code: string;
}

@Component({
  selector: 'app-template-config-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ModalComponent],
  templateUrl: './template-config-modal.component.html',
  styleUrl: './template-config-modal.component.scss',
})
export class TemplateConfigModalComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  readonly isOpen = this.resumeService.showTemplateConfigModal;
  readonly templates = this.resumeService.availableTemplates;

  readonly draftConfig = signal<TemplateConfig>({ ...this.resumeService.templateConfig() });
  readonly previewHtml = signal<string>('');
  readonly isUpdatingPreview = signal<boolean>(false);
  readonly showCustomCss = signal<boolean>(false);
  readonly showTokenDocs = signal<boolean>(false);
  readonly activeDocTab = signal<'tokens' | 'selectors' | 'snippets'>('tokens');

  private prevIsOpen = false;
  private renderRequestId = 0;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  readonly colorPalettes: ColorPalette[] = [
    { name: 'Sapphire Tech', primary: '#0284c7', accent: '#0369a1', text: '#0f172a', badgeBg: '#0284c7' },
    { name: 'Emerald Enterprise', primary: '#059669', accent: '#047857', text: '#064e3b', badgeBg: '#059669' },
    { name: 'Executive Slate', primary: '#1e293b', accent: '#475569', text: '#0f172a', badgeBg: '#1e293b' },
    { name: 'Royal Indigo', primary: '#4338ca', accent: '#3730a3', text: '#1e1b4b', badgeBg: '#4338ca' },
    { name: 'Crimson Modern', primary: '#dc2626', accent: '#b91c1c', text: '#18181b', badgeBg: '#dc2626' },
    { name: 'Midnight Charcoal', primary: '#09090b', accent: '#27272a', text: '#09090b', badgeBg: '#18181b' },
  ];

  readonly fontOptions: FontOption[] = [
    { label: 'System Clean (Modern Sans)', value: 'system-ui, -apple-system, sans-serif', sample: 'Aa Modern' },
    { label: 'Inter (Clean Grotesk)', value: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif', sample: 'Aa Inter' },
    { label: 'Merriweather (Executive Serif)', value: 'Merriweather, Georgia, serif', sample: 'Aa Serif' },
    { label: 'JetBrains Mono (Technical)', value: '"JetBrains Mono", Menlo, monospace', sample: 'Aa Mono' },
    { label: 'Garamond (Classic Editorial)', value: '"EB Garamond", Garamond, Georgia, serif', sample: 'Aa Classic' },
  ];

  readonly styleTokens: StyleTokenDoc[] = [
    { token: '--primary-color', category: 'Colors', description: 'Headings, applicant name, section divider underlines, and primary badges', example: '#0284c7' },
    { token: '--accent-color', category: 'Colors', description: 'Company titles, dates, hyperlinks, contact icons, and secondary accents', example: '#0369a1' },
    { token: '--text-primary', category: 'Colors', description: 'Body text, summary description, and achievement bullet points', example: '#1e293b' },
    { token: '--text-muted', category: 'Colors', description: 'Dates, locations, institution names, and subtle metadata', example: '#64748b' },
    { token: '--font-family', category: 'Typography', description: 'Font family applied globally across headings, body, and lists', example: 'Inter, sans-serif' },
    { token: '--font-size', category: 'Typography', description: 'Base font size (recommended: 10.5px – 12.5px for 1-2 page budget)', example: '11.5px' },
    { token: '--line-height', category: 'Typography', description: 'Line height ratio controlling vertical paragraph and list rhythm', example: '1.36' },
    { token: '--border-color', category: 'Structure', description: 'Light card dividers and borders between entries', example: '#cbd5e1' },
    { token: '--divider-subtle', category: 'Structure', description: 'Subtle separators between job experience entries', example: '#f1f5f9' },
    { token: '--diff-bg', category: 'Diff & Badges', description: 'Background tint for tailored job adaptations in diff view', example: '#f0fdf4' },
    { token: '--diff-border', category: 'Diff & Badges', description: 'Left border color for modified bullet points in diff mode', example: '#16a34a' },
  ];

  readonly selectorDocs: SelectorDoc[] = [
    { selector: '.resume-paper', description: 'The main document sheet container', recommendedStyles: 'border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);' },
    { selector: '.name, h1', description: 'Candidate main full name heading', recommendedStyles: 'letter-spacing: 0.5px; text-transform: uppercase;' },
    { selector: '.title-tagline', description: 'Professional title and strategic positioning tagline', recommendedStyles: 'letter-spacing: 0.2px; font-weight: 700;' },
    { selector: '.contacts', description: 'Contact bar container (email, phone, LinkedIn, location)', recommendedStyles: 'gap: 12px; font-size: 8.5pt;' },
    { selector: '.section', description: 'Major resume section block container', recommendedStyles: 'margin-bottom: 14px;' },
    { selector: '.section-title', description: 'Main section header (EXPERIENCE, SKILLS, etc.)', recommendedStyles: 'border-bottom: 2px solid var(--primary-color);' },
    { selector: '.experience-entry', description: 'Individual job role block container', recommendedStyles: 'margin-bottom: 10px; padding-bottom: 8px;' },
    { selector: '.exp-role', description: 'Job position / title in experience entries', recommendedStyles: 'font-weight: 700; color: var(--primary-color);' },
    { selector: '.exp-company', description: 'Company name for experience entries', recommendedStyles: 'color: var(--accent-color); font-weight: 600;' },
    { selector: '.exp-meta', description: 'Date range and location metadata for roles', recommendedStyles: 'font-size: 8pt; color: var(--text-muted);' },
    { selector: '.exp-highlights li', description: 'Individual achievement bullet points', recommendedStyles: 'margin-bottom: 2.5px; line-height: 1.36;' },
    { selector: '.project-entry', description: 'Key project entry container', recommendedStyles: 'margin-bottom: 9px; padding-bottom: 8px;' },
    { selector: '.skill-pill', description: 'Individual technical skill badge', recommendedStyles: 'border-radius: 9999px; padding: 2px 8px; background: #f8fafc;' },
    { selector: '.skill-pill.matched', description: 'Keyword skill matched with target job spec', recommendedStyles: 'background-color: #dcfce7 !important; color: #166534 !important;' },
    { selector: '.summary-text', description: 'Executive summary / strategic positioning statement', recommendedStyles: 'line-height: 1.4; text-align: justify;' },
    { selector: '.ats-banner', description: 'ATS compliance verification header banner', recommendedStyles: 'display: none !important; /* Hide banner */' },
  ];

  readonly quickSnippets: QuickSnippet[] = [
    {
      label: '+ Pill Badges',
      description: 'Gives skill badges full pill shape with crisp border',
      code: `.skill-pill {\n  border-radius: 9999px !important;\n  padding: 2px 9px !important;\n  font-weight: 600 !important;\n}`,
    },
    {
      label: '+ Left Accent Bar',
      description: 'Replaces underline with modern vertical accent bar',
      code: `.section-title {\n  border-bottom: none !important;\n  border-left: 4px solid var(--primary-color) !important;\n  padding-left: 8px !important;\n}`,
    },
    {
      label: '+ Underlined Roles',
      description: 'Accents job titles with an underline in accent color',
      code: `.exp-role {\n  text-decoration: underline !important;\n  text-decoration-color: var(--accent-color) !important;\n  text-underline-offset: 3px !important;\n}`,
    },
    {
      label: '+ Compact Bullets',
      description: 'Tightens spacing to maximize content on 1 page',
      code: `.exp-highlights li {\n  margin-bottom: 1.5px !important;\n  line-height: 1.30 !important;\n}`,
    },
    {
      label: '+ Hide ATS Banner',
      description: 'Removes the top green ATS verification banner',
      code: `.ats-banner {\n  display: none !important;\n}`,
    },
  ];

  constructor() {
    // Detect modal opening rising edge; use untracked so user edits don't trigger re-initialization
    effect(() => {
      const open = this.isOpen();
      if (open && !this.prevIsOpen) {
        const svcConfig = this.resumeService.templateConfig();
        const activeTmpl = this.resumeService.selectedTemplate();
        const initial: TemplateConfig = {
          ...svcConfig,
          template_id: activeTmpl || svcConfig.template_id || 'modern',
        };
        untracked(() => {
          this.draftConfig.set(initial);
          this.refreshPreview(0);
        });
      }
      this.prevIsOpen = open;
    });
  }

  updateField<K extends keyof TemplateConfig>(field: K, value: TemplateConfig[K], debounceMs = 120): void {
    this.draftConfig.update((cfg) => ({ ...cfg, [field]: value }));
    this.refreshPreview(debounceMs);
  }

  selectPalette(palette: ColorPalette): void {
    this.draftConfig.update((cfg) => ({
      ...cfg,
      primary_color: palette.primary,
      accent_color: palette.accent,
      text_color: palette.text,
    }));
    this.refreshPreview(0);
  }

  onSelectTemplate(tmplId: string): void {
    this.updateField('template_id', tmplId, 0);
  }

  refreshPreview(debounceMs = 0): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }

    const run = async () => {
      let resume = this.resumeService.activeResume();
      if (!resume) {
        await this.resumeService.loadBaseResume();
        resume = this.resumeService.activeResume();
      }
      if (!resume) {
        this.isUpdatingPreview.set(false);
        return;
      }

      this.isUpdatingPreview.set(true);
      const reqId = ++this.renderRequestId;
      const cfg = this.draftConfig();
      const tmplId = cfg.template_id || this.resumeService.selectedTemplate() || 'modern';

      try {
        const html = await this.resumeService.renderPreviewWithConfig(resume, tmplId, cfg);
        if (reqId === this.renderRequestId) {
          this.previewHtml.set(html);
        }
      } catch (err) {
        console.error('Failed to render template customizer preview:', err);
      } finally {
        if (reqId === this.renderRequestId) {
          this.isUpdatingPreview.set(false);
        }
      }
    };

    if (debounceMs <= 0) {
      run();
    } else {
      this.debounceTimer = setTimeout(run, debounceMs);
    }
  }

  onResetDefaults(): void {
    const defaults = { ...this.resumeService.defaultTemplateConfig };
    this.draftConfig.set(defaults);
    this.refreshPreview(0);
  }

  async onSave(): Promise<void> {
    const finalConfig = this.draftConfig();
    await this.resumeService.saveTemplateConfig(finalConfig);
    this.close();
  }

  insertSnippet(code: string): void {
    const curr = (this.draftConfig().custom_css || '').trim();
    const updated = curr.length > 0 ? `${curr}\n\n${code}` : code;
    this.updateField('custom_css', updated, 0);
  }

  insertTokenSnippet(token: string, example: string): void {
    const code = `:root {\n  ${token}: ${example} !important;\n}`;
    this.insertSnippet(code);
  }

  insertSelectorSnippet(selector: string, styles: string): void {
    const code = `${selector} {\n  ${styles}\n}`;
    this.insertSnippet(code);
  }

  clearCustomCss(): void {
    this.updateField('custom_css', '', 0);
  }

  setDocTab(tab: 'tokens' | 'selectors' | 'snippets'): void {
    this.activeDocTab.set(tab);
  }

  onIframeLoad(event: Event): void {
    const iframe = event.target as HTMLIFrameElement;
    try {
      const doc = iframe.contentDocument || iframe.contentWindow?.document;
      if (doc && doc.body) {
        doc.body.style.overflow = 'hidden';
        const h = Math.max(doc.body.scrollHeight, doc.documentElement.scrollHeight);
        if (h > 0) {
          iframe.style.height = `${h + 20}px`;
        }
      }
    } catch {}
  }

  close(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    this.resumeService.showTemplateConfigModal.set(false);
  }
}
