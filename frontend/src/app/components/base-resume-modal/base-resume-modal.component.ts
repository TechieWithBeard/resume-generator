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

  readonly expandedExpIndices = signal<Set<number>>(new Set<number>());
  private prevIsOpen = false;

  formData: ResumeData = {
    name: '',
    title: '',
    linkedin: '',
    github: '',
    portfolio: '',
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
      const open = this.isOpen();
      if (open && !this.prevIsOpen) {
        const base = this.resumeService.baseResume();
        if (base) {
          this.formData = JSON.parse(JSON.stringify(base));
          this.rawJson = JSON.stringify(base, null, 2);
        }
        this.expandedExpIndices.set(new Set<number>());
      }
      this.prevIsOpen = open;
    });
  }

  isExpExpanded(index: number): boolean {
    return this.expandedExpIndices().has(index);
  }

  toggleExp(index: number): void {
    const current = new Set(this.expandedExpIndices());
    if (current.has(index)) {
      current.delete(index);
    } else {
      current.add(index);
    }
    this.expandedExpIndices.set(current);
  }

  expandAllExp(): void {
    const all = new Set<number>();
    (this.formData.experience || []).forEach((_, i) => all.add(i));
    this.expandedExpIndices.set(all);
  }

  collapseAllExp(): void {
    this.expandedExpIndices.set(new Set<number>());
  }

  addExperience(): void {
    if (!this.formData.experience) {
      this.formData.experience = [];
    }
    const newIdx = this.formData.experience.length;
    this.formData.experience.unshift({
      role: '',
      company: '',
      period: '',
      location: '',
      highlights: [''],
    });
    const current = new Set(this.expandedExpIndices());
    // Remap existing expanded indices by +1 since we unshifted to top
    const updated = new Set<number>();
    updated.add(0);
    current.forEach((idx) => updated.add(idx + 1));
    this.expandedExpIndices.set(updated);
  }

  removeExperience(index: number): void {
    if (index >= 0 && index < this.formData.experience.length) {
      this.formData.experience.splice(index, 1);
      const current = new Set<number>();
      this.expandedExpIndices().forEach((i) => {
        if (i < index) current.add(i);
        else if (i > index) current.add(i - 1);
      });
      this.expandedExpIndices.set(current);
    }
  }

  moveExperience(index: number, direction: 'up' | 'down'): void {
    const exps = this.formData.experience;
    const targetIdx = direction === 'up' ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= exps.length) return;
    const temp = exps[index];
    exps[index] = exps[targetIdx];
    exps[targetIdx] = temp;
    this.swapExpandedIndex(index, targetIdx);
  }

  private swapExpandedIndex(i1: number, i2: number): void {
    const current = new Set(this.expandedExpIndices());
    const has1 = current.has(i1);
    const has2 = current.has(i2);
    if (has1) current.add(i2); else current.delete(i2);
    if (has2) current.add(i1); else current.delete(i1);
    this.expandedExpIndices.set(current);
  }

  addHighlight(expIndex: number): void {
    const exp = this.formData.experience[expIndex];
    if (exp) {
      if (!exp.highlights) exp.highlights = [];
      exp.highlights.push('');
    }
  }

  removeHighlight(expIndex: number, hIndex: number): void {
    const exp = this.formData.experience[expIndex];
    if (exp && exp.highlights && hIndex >= 0 && hIndex < exp.highlights.length) {
      exp.highlights.splice(hIndex, 1);
      if (exp.highlights.length === 0) {
        exp.highlights.push('');
      }
    }
  }

  moveHighlight(expIndex: number, hIndex: number, direction: 'up' | 'down'): void {
    const exp = this.formData.experience[expIndex];
    if (!exp || !exp.highlights) return;
    const targetIdx = direction === 'up' ? hIndex - 1 : hIndex + 1;
    if (targetIdx < 0 || targetIdx >= exp.highlights.length) return;
    const temp = exp.highlights[hIndex];
    exp.highlights[hIndex] = exp.highlights[targetIdx];
    exp.highlights[targetIdx] = temp;
  }

  addProject(): void {
    if (!this.formData.projects) this.formData.projects = [];
    this.formData.projects.unshift({
      name: '',
      description: '',
      technologies: [],
    });
  }

  removeProject(index: number): void {
    if (this.formData.projects && index >= 0 && index < this.formData.projects.length) {
      this.formData.projects.splice(index, 1);
    }
  }

  addEducation(): void {
    if (!this.formData.education) this.formData.education = [];
    this.formData.education.unshift({
      degree: '',
      institution: '',
      period: '',
    });
  }

  removeEducation(index: number): void {
    if (this.formData.education && index >= 0 && index < this.formData.education.length) {
      this.formData.education.splice(index, 1);
    }
  }

  trackByIndex(index: number): number {
    return index;
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
