import { Component, inject, signal } from '@angular/core';
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
  readonly editMode = signal<'form' | 'json'>('form');
  readonly jsonError = signal<string | null>(null);

  formData: ResumeData = {
    name: '',
    title: '',
    summary: '',
    experience: [],
    education: [],
    skills: {},
  };
  rawJson = '';

  constructor() {
    const base = this.resumeService.baseResume();
    if (base) {
      this.formData = JSON.parse(JSON.stringify(base));
      this.rawJson = JSON.stringify(base, null, 2);
    }
  }

  close(): void {
    this.resumeService.showBaseResumeModal.set(false);
  }

  onSwitchToJson(): void {
    this.rawJson = JSON.stringify(this.formData, null, 2);
    this.editMode.set('json');
  }

  async onReset(): Promise<void> {
    if (confirm('Reset Ground Truth to default profile?')) {
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
