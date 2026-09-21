import { Injectable, computed, signal } from '@angular/core';
import {
  AlignmentReport,
  GeneratorStep,
  JobInput,
  LLMConfig,
  ResumeData,
  ResumeTemplate,
  TemplateConfig,
  ThoughtLog,
} from '../models/resume.models';

@Injectable({
  providedIn: 'root',
})
export class ResumeGeneratorService {
  private readonly API_BASE = 'http://localhost:8000';

  // Reactive State via Signals
  readonly baseResume = signal<ResumeData | null>(null);
  readonly tailoredResume = signal<ResumeData | null>(null);
  readonly activeResume = computed(() => this.tailoredResume() || this.baseResume());
  readonly renderedHtml = signal<string>('');
  readonly streamLogs = signal<ThoughtLog[]>([]);
  readonly activeStreamingText = signal<string>('');
  readonly currentStep = signal<GeneratorStep>('idle');
  readonly auditReport = signal<AlignmentReport | null>(null);
  readonly isStreaming = signal<boolean>(false);
  readonly streamError = signal<string | null>(null);

  readonly availableTemplates = signal<ResumeTemplate[]>([
    { id: 'modern', name: 'Modern Tech', description: 'Clean, accent styling, skill badges', is_default: true },
    { id: 'executive', name: 'Executive Minimalist', description: 'High-contrast classic ATS layout', is_default: false },
    { id: 'compact', name: 'Compact Classic', description: 'Space-efficient engineering layout', is_default: false },
    { id: 'cv_executive', name: 'Executive CV', description: 'Multi-page comprehensive CV with projects & certs', is_default: false },
  ]);
  readonly selectedTemplate = signal<string>('modern');
  readonly documentMode = signal<'resume' | 'cv'>('resume');
  readonly comparisonMode = signal<boolean>(false);
  readonly viewMode = signal<'single' | 'split' | 'git-diff'>('single');
  readonly baseRenderedHtml = signal<string>('');
  readonly isFullscreen = signal<boolean>(false);
  readonly previewZoom = signal<number>(100);

  readonly defaultTemplateConfig: TemplateConfig = {
    template_id: 'modern',
    primary_color: '#0284c7',
    accent_color: '#0284c7',
    text_color: '#1e293b',
    font_family: 'system-ui, -apple-system, sans-serif',
    font_size: '11.5px',
    line_height: '1.36',
    density: 'normal',
    header_layout: 'left',
    show_tagline: true,
    show_icons: true,
    show_projects: true,
    show_certifications: true,
    show_education: true,
    custom_css: '',
  };

  private loadInitialTemplateConfig(): TemplateConfig {
    try {
      const saved = localStorage.getItem('resume_template_config');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.font_size && (parsed.font_size === '14px' || parseFloat(parsed.font_size) >= 13.8)) {
          parsed.font_size = '11.5px';
        }
        if (parsed.line_height && (parsed.line_height === '1.5' || parseFloat(parsed.line_height) >= 1.48)) {
          parsed.line_height = '1.36';
        }
        return { ...this.defaultTemplateConfig, ...parsed };
      }
    } catch (_) {}
    return { ...this.defaultTemplateConfig };
  }

  readonly templateConfig = signal<TemplateConfig>(this.loadInitialTemplateConfig());
  readonly showTemplateConfigModal = signal<boolean>(false);

  readonly llmConfig = signal<LLMConfig>({
    provider: 'auto',
    model_name: 'llama3.1:8b',
    base_url: 'http://localhost:11434',
    temperature: 0.2,
  });

  // UI Dialog Controls
  readonly showBaseResumeModal = signal<boolean>(false);
  readonly showSettingsDrawer = signal<boolean>(false);


  constructor() {
    this.init();
  }

  async init() {
    await this.loadBaseResume();
    await this.loadTemplates();
    await this.loadTemplateConfig();
  }

  async loadBaseResume(): Promise<void> {
    try {
      const res = await fetch(`${this.API_BASE}/api/resume/base`);
      if (res.ok) {
        const data: ResumeData = await res.json();
        this.baseResume.set(data);
        await this.renderBaseResume();
        if (!this.tailoredResume()) {
          await this.renderResume(data, this.selectedTemplate(), false);
        }
      }
    } catch (err) {
      console.warn('Could not connect to backend API, using initial sample.', err);
    }
  }

  async saveBaseResume(updated: ResumeData): Promise<void> {
    try {
      const res = await fetch(`${this.API_BASE}/api/resume/base`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated),
      });
      if (res.ok) {
        const saved: ResumeData = await res.json();
        this.baseResume.set(saved);
        if (!this.tailoredResume()) {
          await this.renderResume(saved, this.selectedTemplate(), false);
        }
      }
    } catch (err) {
      console.error('Failed to save base resume:', err);
    }
  }

  async resetBaseResume(): Promise<void> {
    try {
      const res = await fetch(`${this.API_BASE}/api/resume/reset`, { method: 'POST' });
      if (res.ok) {
        const data: ResumeData = await res.json();
        this.baseResume.set(data);
        this.tailoredResume.set(null);
        await this.renderResume(data, this.selectedTemplate(), false);
      }
    } catch (err) {
      console.error('Failed to reset base resume:', err);
    }
  }

  async uploadResumeFile(
    file: File,
    autoSave: boolean = false
  ): Promise<{ success: boolean; resume?: ResumeData; metadata?: any; error?: string }> {
    try {
      const base64Content = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = (err) => reject(err);
        reader.readAsDataURL(file);
      });

      const payload = {
        filename: file.name,
        file_data: base64Content,
        save: autoSave,
        llm_config: this.llmConfig(),
      };

      const res = await fetch(`${this.API_BASE}/api/resume/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });


      const data = await res.json();
      if (res.ok && data.success) {
        if (autoSave && data.resume) {
          this.baseResume.set(data.resume);
          if (!this.tailoredResume()) {
            await this.renderResume(data.resume, this.selectedTemplate(), false);
          }
        }
        return {
          success: true,
          resume: data.resume,
          metadata: data.metadata,
        };
      } else {
        return {
          success: false,
          error: data.error || 'Failed to extract resume content.',
        };
      }
    } catch (err: any) {
      console.error('Resume upload error:', err);
      return {
        success: false,
        error: err.message || 'Network error uploading resume file.',
      };
    }
  }

  async loadTemplates(): Promise<void> {
    try {
      const res = await fetch(`${this.API_BASE}/api/templates`);
      if (res.ok) {
        const data: ResumeTemplate[] = await res.json();
        this.availableTemplates.set(data);
      }
    } catch (err) {
      console.warn('Failed to load templates from server:', err);
    }
  }

  async loadTemplateConfig(): Promise<void> {
    try {
      const res = await fetch(`${this.API_BASE}/api/template/config`);
      if (res.ok) {
        const data: TemplateConfig = await res.json();
        this.templateConfig.set(data);
        localStorage.setItem('resume_template_config', JSON.stringify(data));
      }
    } catch (err) {
      console.warn('Could not fetch template config from server, using local defaults:', err);
    }
  }

  async saveTemplateConfig(cfg: TemplateConfig): Promise<void> {
    this.templateConfig.set(cfg);
    if (cfg.template_id) {
      this.selectedTemplate.set(cfg.template_id);
    }
    localStorage.setItem('resume_template_config', JSON.stringify(cfg));
    try {
      await fetch(`${this.API_BASE}/api/template/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cfg),
      });
    } catch (err) {
      console.warn('Failed to sync template config to server:', err);
    }
    const active = this.activeResume();
    if (active) {
      await this.renderResume(active, cfg.template_id || this.selectedTemplate(), this.comparisonMode());
    }
  }

  async renderPreviewWithConfig(resume: ResumeData, templateId: string, cfg: TemplateConfig): Promise<string> {
    try {
      const res = await fetch(`${this.API_BASE}/api/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume,
          template_id: templateId,
          highlight_diff: false,
          base_resume: this.baseResume(),
          template_config: cfg,
        }),
      });
      if (res.ok) {
        return await res.text();
      }
    } catch (err) {
      console.error('Failed to render preview with config:', err);
    }
    return '';
  }

  async renderResume(resume: ResumeData, templateId: string, highlightDiff: boolean): Promise<void> {
    try {
      const res = await fetch(`${this.API_BASE}/api/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume,
          template_id: templateId,
          highlight_diff: highlightDiff,
          base_resume: this.baseResume(),
          template_config: this.templateConfig(),
        }),
      });
      if (res.ok) {
        const html = await res.text();
        this.renderedHtml.set(html);
      }
    } catch (err) {
      console.error('Failed to render resume template:', err);
    }
  }

  async renderBaseResume(): Promise<string> {
    const base = this.baseResume();
    if (!base) return '';
    try {
      const res = await fetch(`${this.API_BASE}/api/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume: base,
          template_id: this.selectedTemplate(),
          highlight_diff: false,
          base_resume: null,
          template_config: this.templateConfig(),
        }),
      });
      if (res.ok) {
        const html = await res.text();
        this.baseRenderedHtml.set(html);
        return html;
      }
    } catch (err) {
      console.error('Failed to render base resume:', err);
    }
    return '';
  }

  async setViewMode(mode: 'single' | 'split' | 'git-diff'): Promise<void> {
    this.viewMode.set(mode);
    if (mode === 'split') {
      await this.renderBaseResume();
      this.comparisonMode.set(true);
      const tailored = this.tailoredResume();
      if (tailored) {
        await this.renderResume(tailored, this.selectedTemplate(), true);
      }
    }
  }

  zoomIn(): void {
    this.previewZoom.update((z) => Math.min(140, z + 10));
  }

  zoomOut(): void {
    this.previewZoom.update((z) => Math.max(65, z - 10));
  }

  resetZoom(): void {
    this.previewZoom.set(100);
  }

  toggleFullscreen(): void {
    this.isFullscreen.update((f) => !f);
  }

  async selectTemplate(templateId: string): Promise<void> {
    this.selectedTemplate.set(templateId);
    const cfg = { ...this.templateConfig(), template_id: templateId };
    this.templateConfig.set(cfg);
    if (this.viewMode() === 'split') {
      await this.renderBaseResume();
    }
    const active = this.activeResume();
    if (active) {
      await this.renderResume(active, templateId, this.comparisonMode());
    }
  }

  async setDocumentMode(mode: 'resume' | 'cv'): Promise<void> {
    this.documentMode.set(mode);
    if (mode === 'cv' && this.selectedTemplate() === 'modern') {
      this.selectedTemplate.set('cv_executive');
    } else if (mode === 'resume' && this.selectedTemplate() === 'cv_executive') {
      this.selectedTemplate.set('modern');
    }
    if (this.viewMode() === 'split') {
      await this.renderBaseResume();
    }
    const active = this.activeResume();
    if (active) {
      await this.renderResume(active, this.selectedTemplate(), this.comparisonMode());
    }
  }

  async toggleComparisonMode(): Promise<void> {
    const newMode = !this.comparisonMode();
    this.comparisonMode.set(newMode);
    const active = this.activeResume();
    if (active) {
      await this.renderResume(active, this.selectedTemplate(), newMode);
    }
  }

  async extractFromLinkedIn(url: string): Promise<any> {
    try {
      const res = await fetch(`${this.API_BASE}/api/extract/linkedin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      return await res.json();
    } catch (err: any) {
      return { success: false, error: err.message || 'Network connection failed' };
    }
  }

  /**
   * Starts Server-Sent Events (SSE) streaming pipeline.
   * Decodes streaming chunks in real-time, feeding signals reactively.
   */
  async startGeneration(jobInput: JobInput): Promise<void> {
    this.isStreaming.set(true);
    this.streamError.set(null);
    this.streamLogs.set([]);
    this.activeStreamingText.set('');
    this.currentStep.set('analysis');

    const enrichedInput: JobInput = {
      ...jobInput,
      document_type: jobInput.document_type || this.documentMode(),
    };

    if (this.documentMode() === 'cv' && this.selectedTemplate() === 'modern') {
      this.selectedTemplate.set('cv_executive');
    }

    const payload = {
      job_input: enrichedInput,
      llm_config: this.llmConfig(),
      base_resume: this.baseResume(),
      template_id: this.selectedTemplate(),
    };


    try {
      const response = await fetch(`${this.API_BASE}/api/generate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          if (!block.trim()) continue;

          let eventType = 'message';
          let dataStr = '';

          for (const line of block.split('\n')) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              dataStr = line.slice(6).trim();
            }
          }

          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            this.handleStreamEvent(eventType, data);
          } catch (e) {
            console.warn('Failed to parse SSE JSON payload:', dataStr);
          }
        }
      }

      this.currentStep.set('done');
    } catch (err: any) {
      console.error('Streaming error:', err);
      this.streamError.set(err.message || 'Failed to complete generation stream.');
    } finally {
      this.isStreaming.set(false);
    }
  }

  private handleStreamEvent(type: string, data: any): void {
    if (type === 'step') {
      this.currentStep.set(data.step as GeneratorStep);
    } else if (type === 'thought_stream' || type === 'token') {
      const chunk = data.content || '';
      // Ignore bare dot characters from any legacy stream tasks
      if (chunk.trim() === '.' && (this.activeStreamingText().endsWith('.') || !this.activeStreamingText().trim())) {
        return;
      }
      this.activeStreamingText.update((text) => text + chunk);
    } else if (type === 'thought') {
      // If there was active streaming text accumulated, commit it to logs
      const currentStream = this.activeStreamingText().trim();
      if (currentStream) {
        this.streamLogs.update((logs) => [
          ...logs,
          {
            step: 'synthesis',
            content: currentStream,
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
        this.activeStreamingText.set('');
      }

      this.streamLogs.update((logs) => [
        ...logs,
        {
          step: data.step,
          content: data.content,
          timestamp: data.timestamp || new Date().toLocaleTimeString(),
        },
      ]);
    } else if (type === 'audit') {
      this.auditReport.set(data.data || data);
    } else if (type === 'complete') {
      const currentStream = this.activeStreamingText().trim();
      if (currentStream) {
        this.streamLogs.update((logs) => [
          ...logs,
          {
            step: 'synthesis',
            content: currentStream,
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
        this.activeStreamingText.set('');
      }
      if (data.resume) {
        this.tailoredResume.set(data.resume);
      }
      if (data.html) {
        this.renderedHtml.set(data.html);
      }
      if (data.audit) {
        this.auditReport.set(data.audit);
      }
    } else if (type === 'error') {
      this.streamError.set(data.error || 'Generation error occurred.');
    }
  }

  // Export & Download Actions
  downloadPdf(): void {
    const html = this.renderedHtml();
    if (!html) return;

    // Create an isolated hidden iframe loaded exclusively with the resume HTML
    // This ensures only the resume document is converted to PDF without web application UI bleed
    const printFrame = document.createElement('iframe');
    printFrame.style.position = 'fixed';
    printFrame.style.right = '0';
    printFrame.style.bottom = '0';
    printFrame.style.width = '0';
    printFrame.style.height = '0';
    printFrame.style.border = '0';
    printFrame.setAttribute('aria-hidden', 'true');
    document.body.appendChild(printFrame);

    const frameDoc = printFrame.contentWindow?.document;
    if (frameDoc) {
      frameDoc.open();
      frameDoc.write(html);
      frameDoc.close();
      setTimeout(() => {
        try {
          printFrame.contentWindow?.focus();
          printFrame.contentWindow?.print();
        } catch (err) {
          console.error('Failed to invoke print on isolated iframe:', err);
        } finally {
          setTimeout(() => {
            if (document.body.contains(printFrame)) {
              document.body.removeChild(printFrame);
            }
          }, 2000);
        }
      }, 300);
    }
  }

  downloadHtml(): void {
    const html = this.renderedHtml();
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const name = this.activeResume()?.name?.replace(/\s+/g, '_') || 'Profile';
    const docSuffix = this.documentMode() === 'cv' ? 'Custom_CV' : 'Tailored_Resume';
    a.download = `${name}_${docSuffix}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  downloadJson(): void {
    const resume = this.activeResume();
    if (!resume) return;
    const jsonStr = JSON.stringify(resume, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const name = resume.name?.replace(/\s+/g, '_') || 'Profile';
    const docSuffix = this.documentMode() === 'cv' ? 'Custom_CV' : 'Tailored_Resume';
    a.download = `${name}_${docSuffix}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

}
