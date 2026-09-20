import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { CardComponent } from '../../shared/components/card/card.component';

@Component({
  selector: 'app-job-input',
  standalone: true,
  imports: [CommonModule, FormsModule, CardComponent],
  templateUrl: './job-input.component.html',
  styleUrl: './job-input.component.scss',
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
      this.extractMessage.set(`✓ Extracted: "${result.title}" at ${result.company || 'Target Company'}`);
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
