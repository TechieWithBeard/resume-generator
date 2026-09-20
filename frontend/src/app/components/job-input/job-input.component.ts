import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResumeGeneratorService } from '../../services/resume-generator.service';

@Component({
  selector: 'app-job-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="job-input-card">
      <div class="tabs-header">
        <button
          type="button"
          class="tab-btn"
          [class.active]="activeTab() === 'linkedin'"
          (click)="activeTab.set('linkedin')"
        >
          <span class="tab-icon">🔗</span> LinkedIn URL
        </button>
        <button
          type="button"
          class="tab-btn"
          [class.active]="activeTab() === 'text'"
          (click)="activeTab.set('text')"
        >
          <span class="tab-icon">📝</span> Paste Job Content
        </button>
      </div>

      <div class="tab-body">
        <!-- LinkedIn URL Tab -->
        @if (activeTab() === 'linkedin') {
          <div class="input-group">
            <label for="linkedinUrl" class="input-label">LinkedIn Job Posting URL</label>
            <div class="url-input-row">
              <input
                id="linkedinUrl"
                type="url"
                class="form-control"
                placeholder="https://www.linkedin.com/jobs/view/..."
                [(ngModel)]="linkedinUrl"
                [disabled]="isExtracting() || isStreaming()"
              />
              <button
                type="button"
                class="btn-secondary"
                (click)="onExtractLinkedIn()"
                [disabled]="!linkedinUrl || isExtracting() || isStreaming()"
              >
                @if (isExtracting()) {
                  <span class="spinner"></span> Extracting...
                } @else {
                  <span>⚡ Extract</span>
                }
              </button>
            </div>
            @if (extractMessage()) {
              <div class="alert-message" [class.error]="extractIsError()">
                {{ extractMessage() }}
              </div>
            }
          </div>
        }

        <!-- Job Description Text Tab -->
        <div class="input-group" [style.display]="activeTab() === 'text' || jobDescription ? 'block' : 'none'">
          <div class="textarea-header">
            <label for="jobDesc" class="input-label">
              Target Job Description / Requirements
              @if (jobDescription) {
                <span class="char-count">({{ jobDescription.length }} chars)</span>
              }
            </label>
            <button
              type="button"
              class="btn-link"
              (click)="loadSampleJob()"
              [disabled]="isStreaming()"
            >
              📋 Load Sample Architect JD
            </button>
          </div>
          <textarea
            id="jobDesc"
            class="form-control job-textarea"
            rows="6"
            placeholder="Paste the job description, required technical competencies, responsibilities, or qualification bullet points..."
            [(ngModel)]="jobDescription"
            [disabled]="isStreaming()"
          ></textarea>
        </div>

        <!-- Target Title Input -->
        <div class="input-group">
          <label for="targetTitle" class="input-label">
            Target Job Title <span class="text-muted">(Optional override)</span>
          </label>
          <input
            id="targetTitle"
            type="text"
            class="form-control"
            placeholder="e.g. Senior Frontend Architect / Staff UI Engineer"
            [(ngModel)]="targetTitle"
            [disabled]="isStreaming()"
          />
        </div>

        <!-- Action Button -->
        <div class="actions-row">
          <button
            type="button"
            class="btn-primary btn-generate"
            (click)="onGenerate()"
            [disabled]="!canGenerate() || isStreaming()"
          >
            @if (isStreaming()) {
              <span class="spinner"></span> Generating Aligned Resume...
            } @else {
              <span>✨ Generate Tailored ATS Resume</span>
            }
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .job-input-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
      margin-bottom: 20px;
    }
    .tabs-header {
      display: flex;
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
    }
    .tab-btn {
      flex: 1;
      padding: 12px 16px;
      border: none;
      background: transparent;
      font-size: 13px;
      font-weight: 600;
      color: #64748b;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s ease;
      border-bottom: 2px solid transparent;
    }
    .tab-btn:hover {
      color: #0f172a;
      background: #f1f5f9;
    }
    .tab-btn.active {
      color: #0284c7;
      background: #ffffff;
      border-bottom-color: #0284c7;
    }
    .tab-body {
      padding: 20px;
    }
    .input-group {
      margin-bottom: 16px;
    }
    .input-label {
      display: block;
      font-size: 12.5px;
      font-weight: 600;
      color: #334155;
      margin-bottom: 6px;
    }
    .textarea-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }
    .char-count {
      font-weight: 400;
      color: #94a3b8;
      font-size: 11px;
    }
    .btn-link {
      background: none;
      border: none;
      color: #0284c7;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      padding: 0;
    }
    .btn-link:hover {
      text-decoration: underline;
    }
    .url-input-row {
      display: flex;
      gap: 8px;
    }
    .form-control {
      width: 100%;
      padding: 9px 12px;
      font-size: 13px;
      color: #0f172a;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      outline: none;
      transition: border-color 0.2s;
      font-family: inherit;
    }
    .form-control:focus {
      border-color: #0284c7;
      box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.12);
    }
    .job-textarea {
      resize: vertical;
      line-height: 1.45;
    }
    .btn-secondary {
      padding: 9px 16px;
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .btn-secondary:hover:not(:disabled) {
      background: #e2e8f0;
      color: #0f172a;
    }
    .btn-secondary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .alert-message {
      margin-top: 8px;
      padding: 8px 12px;
      background: #eff6ff;
      border-left: 3px solid #3b82f6;
      border-radius: 4px;
      font-size: 12px;
      color: #1e40af;
    }
    .alert-message.error {
      background: #fef2f2;
      border-left-color: #ef4444;
      color: #b91c1c;
    }
    .actions-row {
      margin-top: 18px;
    }
    .btn-primary {
      width: 100%;
      padding: 12px 18px;
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
      color: #ffffff;
      border: none;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 4px 10px rgba(2, 132, 199, 0.25);
      transition: all 0.2s ease;
    }
    .btn-primary:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 14px rgba(2, 132, 199, 0.35);
    }
    .btn-primary:disabled {
      background: #94a3b8;
      box-shadow: none;
      cursor: not-allowed;
    }
    .spinner {
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      display: inline-block;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .text-muted {
      color: #94a3b8;
      font-weight: normal;
    }
  `]
})
export class JobInputComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  readonly activeTab = signal<'linkedin' | 'text'>('text');
  readonly isExtracting = signal<boolean>(false);
  readonly extractMessage = signal<string | null>(null);
  readonly extractIsError = signal<boolean>(false);

  linkedinUrl = '';
  jobDescription = '';
  targetTitle = '';

  readonly isStreaming = this.resumeService.isStreaming;

  canGenerate(): boolean {
    return Boolean((this.jobDescription && this.jobDescription.trim().length > 30) || this.linkedinUrl);
  }

  async onExtractLinkedIn(): Promise<void> {
    if (!this.linkedinUrl) return;
    this.isExtracting.set(true);
    this.extractMessage.set(null);
    this.extractIsError.set(false);

    const result = await this.resumeService.extractFromLinkedIn(this.linkedinUrl);
    this.isExtracting.set(false);

    if (result.success) {
      this.jobDescription = result.job_description || '';
      if (result.title) this.targetTitle = result.title;
      this.extractMessage.set(`✓ Extracted job: "${result.title}" at ${result.company || 'Company'}`);
      this.extractIsError.set(false);
      this.activeTab.set('text');
    } else {
      this.extractMessage.set(result.error || 'Failed to extract job.');
      this.extractIsError.set(true);
    }
  }

  loadSampleJob(): void {
    this.targetTitle = 'Senior Frontend Architect (Enterprise & AI)';
    this.jobDescription = `Position: Senior Frontend Architect
Location: Global / Remote
Company: Enterprise AI SaaS Platform

We are seeking a Senior Frontend Architect to lead the evolution of our high-scale enterprise web applications. You will be responsible for defining architectural standards, guiding Nx monorepo restructuring, establishing design system guidelines, and architecting real-time streaming AI interfaces.

Key Qualifications:
• 7+ years of experience with Angular, TypeScript, and modern component architecture.
• Proven mastery of Angular Signals, RxJS, and scalable state management.
• Deep expertise in Nx monorepos, modular library boundaries, and CI/CD optimization.
• Experience building real-time streaming interfaces (Server-Sent Events, WebSockets, LangChain).
• Dedication to test coverage (Karma, Cypress, Playwright) and WCAG 2.1 accessibility.
• Track record leading legacy modernization migrations in enterprise environments.`;
    this.activeTab.set('text');
  }

  onGenerate(): void {
    if (!this.canGenerate()) return;
    this.resumeService.startGeneration({
      job_description: this.jobDescription,
      linkedin_url: this.linkedinUrl,
      target_title: this.targetTitle || undefined,
    });
  }
}
