import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { CardComponent } from '../../shared/components/card/card.component';
import { HumanGuidance, PreflightReport } from '../../models/resume.models';

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

  // Human-in-the-Loop Mismatch Guidance Signals
  readonly isCheckingPreflight = signal<boolean>(false);
  readonly showMismatchModal = signal<boolean>(false);
  readonly preflightReport = signal<PreflightReport | null>(null);
  readonly selectedStrategy = signal<'transferable' | 'strict_factual'>('transferable');
  readonly candidateNotes = signal<string>('');

  // Message to the Hiring Team Signals
  readonly isGeneratingNote = signal<boolean>(false);
  readonly showHiringNoteModal = signal<boolean>(false);
  readonly hiringNote = signal<{ note: string; target_company: string; target_role: string; word_count: number; char_count: number } | null>(null);
  readonly editedNote = signal<string>('');
  readonly noteCopied = signal<boolean>(false);

  linkedinUrl = '';
  jobDescription = '';
  targetTitle = '';

  readonly isStreaming = this.resumeService.isStreaming;
  readonly documentMode = this.resumeService.documentMode;
  readonly baseResume = this.resumeService.baseResume;

  setDocumentMode(mode: 'resume' | 'cv'): void {
    this.resumeService.setDocumentMode(mode);
  }

  hasBaseResume(): boolean {
    const base = this.baseResume();
    return Boolean(base && base.name && base.experience && base.experience.length > 0);
  }

  hasJobRequirements(): boolean {
    return Boolean((this.jobDescription && this.jobDescription.trim().length > 30) || this.linkedinUrl);
  }

  canGenerate(): boolean {
    return this.hasBaseResume() && this.hasJobRequirements();
  }

  openSourceOfTruthModal(): void {
    this.resumeService.showBaseResumeModal.set(true);
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

  async onGenerate(): Promise<void> {
    if (!this.hasBaseResume()) {
      this.openSourceOfTruthModal();
      return;
    }
    if (!this.hasJobRequirements()) return;

    const jobInput = {
      job_description: this.jobDescription,
      linkedin_url: this.linkedinUrl,
      target_title: this.targetTitle || undefined,
      document_type: this.documentMode(),
    };

    // Run Preflight Check to detect role mismatch
    this.isCheckingPreflight.set(true);
    const preflight = await this.resumeService.checkPreflight(jobInput);
    this.isCheckingPreflight.set(false);

    if (preflight && preflight.is_low_match) {
      // Severe or low competency match detected: trigger Human-in-the-Loop decision modal
      this.preflightReport.set(preflight);
      this.showMismatchModal.set(true);
      return;
    }

    // High/moderate alignment: proceed directly
    this.resumeService.startGeneration(jobInput);
  }

  confirmMismatchProceed(): void {
    const guidance: HumanGuidance = {
      strategy: this.selectedStrategy(),
      candidate_notes: this.candidateNotes().trim() || undefined,
      confirmed_proceed: true,
    };

    this.showMismatchModal.set(false);
    this.resumeService.startGeneration({
      job_description: this.jobDescription,
      linkedin_url: this.linkedinUrl,
      target_title: this.targetTitle || undefined,
      document_type: this.documentMode(),
      human_guidance: guidance,
    });
  }

  cancelMismatch(): void {
    this.showMismatchModal.set(false);
  }

  async onGenerateHiringNote(): Promise<void> {
    if (!this.canGenerate()) return;
    this.isGeneratingNote.set(true);
    try {
      const res = await this.resumeService.generateHiringNote({
        job_description: this.jobDescription,
        linkedin_url: this.linkedinUrl,
        target_title: this.targetTitle || undefined,
        document_type: this.documentMode(),
      });
      if (res && res.note) {
        this.hiringNote.set(res);
        this.editedNote.set(res.note);
        this.noteCopied.set(false);
        this.showHiringNoteModal.set(true);
      }
    } catch (err) {
      console.error('Failed to generate hiring note:', err);
    } finally {
      this.isGeneratingNote.set(false);
    }
  }

  async copyNoteToClipboard(): Promise<void> {
    const textToCopy = this.editedNote() || this.hiringNote()?.note || '';
    if (!textToCopy) return;
    try {
      await navigator.clipboard.writeText(textToCopy);
      this.noteCopied.set(true);
      setTimeout(() => this.noteCopied.set(false), 2500);
    } catch (e) {
      console.warn('Failed to copy to clipboard via navigator:', e);
    }
  }

  closeHiringNoteModal(): void {
    this.showHiringNoteModal.set(false);
  }
}
