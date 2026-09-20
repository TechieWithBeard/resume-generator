import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { ResumeData } from '../../models/resume.models';

@Component({
  selector: 'app-base-resume-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    @if (isOpen()) {
      <div class="modal-backdrop" (click)="close()">
        <div class="modal-dialog" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <div class="header-title">
              <span class="shield-icon">🛡️</span>
              <h3>Base Resume (Ground Truth)</h3>
            </div>
            <button type="button" class="btn-close" (click)="close()">✕</button>
          </div>

          <div class="modal-body">
            <div class="info-alert">
              <strong>Source of Truth Invariant:</strong> The AI generator uses this profile as the immutable ground truth. The AI will never fabricate companies, degrees, or tools outside of this profile. You can edit this profile or import your own resume data.
            </div>

            <div class="view-toggle">
              <button
                type="button"
                class="toggle-btn"
                [class.active]="editMode() === 'form'"
                (click)="editMode.set('form')"
              >
                Structured Form
              </button>
              <button
                type="button"
                class="toggle-btn"
                [class.active]="editMode() === 'json'"
                (click)="onSwitchToJson()"
              >
                Raw JSON Schema
              </button>
            </div>

            @if (editMode() === 'form') {
              <div class="form-container">
                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Full Name</label>
                    <input type="text" class="form-input" [(ngModel)]="formData.name" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Professional Title</label>
                    <input type="text" class="form-input" [(ngModel)]="formData.title" />
                  </div>
                </div>

                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-input" [(ngModel)]="formData.email" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">Phone</label>
                    <input type="text" class="form-input" [(ngModel)]="formData.phone" />
                  </div>
                </div>

                <div class="form-row-2">
                  <div class="form-group">
                    <label class="form-label">LinkedIn URL</label>
                    <input type="text" class="form-input" [(ngModel)]="formData.linkedin" />
                  </div>
                  <div class="form-group">
                    <label class="form-label">GitHub URL</label>
                    <input type="text" class="form-input" [(ngModel)]="formData.github" />
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">Executive Summary</label>
                  <textarea class="form-input" rows="3" [(ngModel)]="formData.summary"></textarea>
                </div>

                <div class="section-title">Verified Experience ({{ formData.experience.length }} roles)</div>
                @for (exp of formData.experience; track exp.company + exp.period) {
                  <div class="exp-block">
                    <div class="exp-block-title">
                      <strong>{{ exp.role }}</strong> at <strong>{{ exp.company }}</strong> ({{ exp.period }})
                    </div>
                    <ul class="exp-bullets">
                      @for (h of exp.highlights; track h) {
                        <li>{{ h }}</li>
                      }
                    </ul>
                  </div>
                }
              </div>
            } @else {
              <div class="json-container">
                <textarea
                  class="json-textarea"
                  rows="18"
                  [(ngModel)]="rawJson"
                ></textarea>
                @if (jsonError()) {
                  <div class="json-error">{{ jsonError() }}</div>
                }
              </div>
            }
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-reset" (click)="onReset()">
              ↺ Reset to Default
            </button>
            <div class="footer-right">
              <button type="button" class="btn-cancel" (click)="close()">
                Cancel
              </button>
              <button type="button" class="btn-save" (click)="onSave()">
                Save Ground Truth
              </button>
            </div>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    .modal-backdrop {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.65);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }
    .modal-dialog {
      background: #ffffff;
      border-radius: 14px;
      width: 90%;
      max-width: 780px;
      max-height: 88vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
      overflow: hidden;
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 22px;
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
    }
    .header-title {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .header-title h3 {
      font-size: 16px;
      font-weight: 700;
      color: #0f172a;
      margin: 0;
    }
    .shield-icon {
      font-size: 20px;
    }
    .btn-close {
      background: none;
      border: none;
      font-size: 18px;
      color: #64748b;
      cursor: pointer;
    }
    .modal-body {
      padding: 20px 22px;
      overflow-y: auto;
      flex: 1;
    }
    .info-alert {
      background: #f0fdf4;
      border-left: 4px solid #16a34a;
      padding: 10px 14px;
      border-radius: 4px;
      font-size: 12.5px;
      color: #166534;
      margin-bottom: 16px;
      line-height: 1.5;
    }
    .view-toggle {
      display: flex;
      background: #e2e8f0;
      padding: 3px;
      border-radius: 6px;
      width: fit-content;
      margin-bottom: 16px;
    }
    .toggle-btn {
      padding: 6px 14px;
      border: none;
      background: transparent;
      font-size: 12px;
      font-weight: 600;
      color: #475569;
      border-radius: 4px;
      cursor: pointer;
    }
    .toggle-btn.active {
      background: #ffffff;
      color: #0284c7;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .form-row-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }
    .form-group {
      margin-bottom: 12px;
    }
    .form-label {
      display: block;
      font-size: 12px;
      font-weight: 600;
      color: #334155;
      margin-bottom: 4px;
    }
    .form-input {
      width: 100%;
      padding: 8px 10px;
      font-size: 13px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      outline: none;
      font-family: inherit;
    }
    .form-input:focus {
      border-color: #0284c7;
    }
    .section-title {
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
      margin: 16px 0 8px 0;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
    }
    .exp-block {
      background: #f8fafc;
      padding: 10px 12px;
      border-radius: 6px;
      border: 1px solid #e2e8f0;
      margin-bottom: 10px;
      font-size: 12px;
    }
    .exp-block-title {
      color: #0f172a;
      margin-bottom: 6px;
    }
    .exp-bullets {
      padding-left: 18px;
      color: #334155;
      line-height: 1.4;
    }
    .json-textarea {
      width: 100%;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      padding: 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      line-height: 1.5;
    }
    .json-error {
      color: #dc2626;
      font-size: 12px;
      margin-top: 6px;
    }
    .modal-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 22px;
      background: #f8fafc;
      border-top: 1px solid #e2e8f0;
    }
    .footer-right {
      display: flex;
      gap: 10px;
    }
    .btn-reset {
      background: none;
      border: 1px solid #cbd5e1;
      padding: 7px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      color: #64748b;
      cursor: pointer;
    }
    .btn-reset:hover {
      background: #f1f5f9;
      color: #0f172a;
    }
    .btn-cancel {
      background: none;
      border: 1px solid #cbd5e1;
      padding: 7px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      color: #334155;
      cursor: pointer;
    }
    .btn-save {
      background: #0284c7;
      border: none;
      padding: 7px 16px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      color: #ffffff;
      cursor: pointer;
    }
    .btn-save:hover {
      background: #0369a1;
    }
  `]
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
    if (confirm('Reset Ground Truth to default sample resume?')) {
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
