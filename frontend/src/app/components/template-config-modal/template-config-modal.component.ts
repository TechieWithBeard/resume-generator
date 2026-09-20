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

  close(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    this.resumeService.showTemplateConfigModal.set(false);
  }
}
