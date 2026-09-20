import { Component, effect, inject, signal } from '@angular/core';
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
    // When modal opens, sync draftConfig from active service config and render live preview
    effect(() => {
      if (this.isOpen()) {
        this.draftConfig.set({ ...this.resumeService.templateConfig() });
        this.refreshPreview();
      }
    });
  }

  async selectPalette(palette: ColorPalette): Promise<void> {
    this.draftConfig.update((cfg) => ({
      ...cfg,
      primary_color: palette.primary,
      accent_color: palette.accent,
      text_color: palette.text,
    }));
    await this.refreshPreview();
  }

  async onConfigChange(): Promise<void> {
    this.draftConfig.update((c) => ({ ...c }));
    await this.refreshPreview();
  }

  async onSelectTemplate(tmplId: string): Promise<void> {
    this.draftConfig.update((cfg) => ({ ...cfg, template_id: tmplId }));
    await this.refreshPreview();
  }

  async refreshPreview(): Promise<void> {
    const resume = this.resumeService.activeResume();
    if (!resume) return;

    this.isUpdatingPreview.set(true);
    const cfg = this.draftConfig();
    const html = await this.resumeService.renderPreviewWithConfig(resume, cfg.template_id, cfg);
    this.previewHtml.set(html);
    this.isUpdatingPreview.set(false);
  }

  async onResetDefaults(): Promise<void> {
    const defaults = { ...this.resumeService.defaultTemplateConfig };
    this.draftConfig.set(defaults);
    await this.refreshPreview();
  }

  async onSave(): Promise<void> {
    await this.resumeService.saveTemplateConfig(this.draftConfig());
    this.close();
  }

  close(): void {
    this.resumeService.showTemplateConfigModal.set(false);
  }
}
