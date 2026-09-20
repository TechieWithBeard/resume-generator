import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { ResumeData } from '../../models/resume.models';
import { ModalComponent } from '../../shared/components/modal/modal.component';

@Component({
  selector: 'app-base-resume-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ModalComponent],
  templateUrl: './base-resume-modal.component.html',
  styleUrl: './base-resume-modal.component.scss',
})
export class BaseResumeModalComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  readonly isOpen = this.resumeService.showBaseResumeModal;
  readonly editMode = signal<'form' | 'raw' | 'json'>('form');
  readonly jsonError = signal<string | null>(null);

  readonly isUploading = signal<boolean>(false);
  readonly uploadMessage = signal<string | null>(null);
  readonly uploadIsError = signal<boolean>(false);
  readonly uploadMetadata = signal<any>(null);
  readonly isDragOver = signal<boolean>(false);

  formData: ResumeData = {
    name: '',
    title: '',
    summary: '',
    experience: [],
    education: [],
    skills: {},
    projects: [],
    certifications: [],
    raw_text: '',
  };
  rawJson = '';

  constructor() {
    // Whenever modal opens, sync from active baseResume in service
    effect(() => {
      if (this.isOpen()) {
        const base = this.resumeService.baseResume();
        if (base) {
          this.formData = JSON.parse(JSON.stringify(base));
          this.rawJson = JSON.stringify(base, null, 2);
        }
      }
    });
  }

  get skillCategories(): string[] {
    return Object.keys(this.formData.skills || {});
  }

  get rawTextWordCount(): number {
    if (!this.formData.raw_text) return 0;
    return this.formData.raw_text.trim().split(/\s+/).filter(Boolean).length;
  }

  get rawTextCharCount(): number {
    return (this.formData.raw_text || '').length;
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
  }

  async onDrop(event: DragEvent): Promise<void> {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
    if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      await this.handleFile(event.dataTransfer.files[0]);
    }
  }

  async onFileSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      await this.handleFile(input.files[0]);
      input.value = '';
    }
  }

  async handleFile(file: File): Promise<void> {
    this.isUploading.set(true);
    this.uploadMessage.set(`Uploading and analyzing ${file.name}...`);
    this.uploadIsError.set(false);

    const result = await this.resumeService.uploadResumeFile(file, false);
    this.isUploading.set(false);

    if (result.success && result.resume) {
      this.formData = result.resume;
      this.rawJson = JSON.stringify(result.resume, null, 2);
      this.uploadMetadata.set(result.metadata);
      const meta = result.metadata || {};
      const expCount = result.resume.experience?.length || 0;
      const eduCount = result.resume.education?.length || 0;
      const skillCount = Object.values(result.resume.skills || {}).flat().length;
      const projCount = result.resume.projects?.length || 0;
      this.uploadMessage.set(
        `✓ Extracted from ${meta.filename || file.name}: ${expCount} experiences, ${eduCount} degrees, ${projCount} projects, and ${skillCount} skills (${meta.word_count || 0} words, 100% data preserved).`
      );
      this.uploadIsError.set(false);
      this.editMode.set('form');
    } else {
      this.uploadMessage.set(result.error || 'Failed to extract resume content.');
      this.uploadIsError.set(true);
    }
  }

  close(): void {
    this.resumeService.showBaseResumeModal.set(false);
  }

  onSwitchMode(mode: 'form' | 'raw' | 'json'): void {
    if (this.editMode() === 'json' && mode !== 'json') {
      try {
        this.formData = JSON.parse(this.rawJson);
        this.jsonError.set(null);
      } catch (e: any) {
        this.jsonError.set(`Invalid JSON syntax: ${e.message}`);
        return;
      }
    } else if (mode === 'json') {
      this.rawJson = JSON.stringify(this.formData, null, 2);
    }
    this.editMode.set(mode);
  }

  async onReset(): Promise<void> {
    if (confirm('Reset Ground Truth to default baseline profile?')) {
      await this.resumeService.resetBaseResume();
      const base = this.resumeService.baseResume();
      if (base) {
        this.formData = JSON.parse(JSON.stringify(base));
        this.rawJson = JSON.stringify(base, null, 2);
      }
      this.close();
    }
  }

  async onSave(): Promise<void> {
    try {
      let dataToSave: ResumeData;
      if (this.editMode() === 'json') {
        dataToSave = JSON.parse(this.rawJson);
      } else {
        dataToSave = this.formData;
      }
      await this.resumeService.saveBaseResume(dataToSave);
      this.close();
    } catch (e: any) {
      this.jsonError.set(`Invalid JSON: ${e.message}`);
    }
  }
}
