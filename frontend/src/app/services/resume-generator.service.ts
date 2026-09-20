import { Injectable, computed, signal } from '@angular/core';
import {
  AlignmentReport,
  GeneratorStep,
  JobInput,
  LLMConfig,
  ResumeData,
  ResumeTemplate,
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
  ]);
  readonly selectedTemplate = signal<string>('modern');
  readonly comparisonMode = signal<boolean>(false);

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
  }

  async loadBaseResume(): Promise<void> {
    try {
      const res = await fetch(`${this.API_BASE}/api/resume/base`);
      if (res.ok) {
        const data: ResumeData = await res.json();
        this.baseResume.set(data);
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

  async selectTemplate(templateId: string): Promise<void> {
    this.selectedTemplate.set(templateId);
    const active = this.activeResume();
    if (active) {
      await this.renderResume(active, templateId, this.comparisonMode());
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

    const payload = {
      job_input: jobInput,
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
      this.activeStreamingText.update((text) => text + (data.content || ''));
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
    const iframe = document.querySelector('iframe.resume-frame') as HTMLIFrameElement;
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    } else {
      window.print();
    }
  }

  downloadHtml(): void {
    const html = this.renderedHtml();
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const name = this.activeResume()?.name?.replace(/\s+/g, '_') || 'Resume';
    a.download = `${name}_Tailored_Resume.html`;
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
    const name = resume.name?.replace(/\s+/g, '_') || 'Resume';
    a.download = `${name}_Tailored_Resume.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
