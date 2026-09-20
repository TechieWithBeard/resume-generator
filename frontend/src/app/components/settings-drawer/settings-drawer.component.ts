import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { LLMConfig } from '../../models/resume.models';

@Component({
  selector: 'app-settings-drawer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    @if (isOpen()) {
      <div class="drawer-backdrop" (click)="close()">
        <div class="drawer-panel" (click)="$event.stopPropagation()">
          <div class="drawer-header">
            <div class="header-title">
              <span class="settings-icon">⚙️</span>
              <h3>LLM Engine & Provider Settings</h3>
            </div>
            <button type="button" class="btn-close" (click)="close()">✕</button>
          </div>

          <div class="drawer-body">
            <div class="setting-group">
              <label class="setting-label">AI Execution Provider</label>
              <select class="form-select" [(ngModel)]="config.provider">
                <option value="auto">⚡ Auto (Ollama -> OpenAI -> Heuristic)</option>
                <option value="ollama">🦙 Local Ollama (Privacy First, Offline)</option>
                <option value="openai">✨ OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="huggingface">🤗 Hugging Face Inference</option>
                <option value="heuristic">🎯 High-Precision Deterministic Engine (No Keys Needed)</option>
              </select>
              <div class="setting-hint">
                Configurable per run. The package supports local privacy as well as cloud LLMs.
              </div>
            </div>

            @if (config.provider === 'ollama' || config.provider === 'auto') {
              <div class="setting-group">
                <label class="setting-label">Ollama Base URL</label>
                <input
                  type="text"
                  class="form-input"
                  placeholder="http://localhost:11434"
                  [(ngModel)]="config.base_url"
                />
              </div>
              <div class="setting-group">
                <label class="setting-label">Ollama Model Name</label>
                <input
                  type="text"
                  class="form-input"
                  placeholder="llama3 / mistral / qwen2.5"
                  [(ngModel)]="config.model_name"
                />
              </div>
            }

            @if (config.provider === 'openai' || config.provider === 'auto') {
              <div class="setting-group">
                <label class="setting-label">OpenAI API Key</label>
                <input
                  type="password"
                  class="form-input"
                  placeholder="sk-..."
                  [(ngModel)]="config.api_key"
                />
                <div class="setting-hint">Leave blank to use server OPENAI_API_KEY env var.</div>
              </div>
            }

            <div class="setting-group">
              <label class="setting-label">Creativity / Temperature: {{ config.temperature }}</label>
              <input
                type="range"
                min="0"
                max="0.8"
                step="0.05"
                class="form-range"
                [(ngModel)]="config.temperature"
              />
              <div class="setting-hint">
                Lower values enforce stricter fidelity to ground truth resume data.
              </div>
            </div>
          </div>

          <div class="drawer-footer">
            <button type="button" class="btn-save" (click)="save()">
              Save Settings
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    .drawer-backdrop {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.5);
      backdrop-filter: blur(2px);
      z-index: 1000;
      display: flex;
      justify-content: flex-end;
    }
    .drawer-panel {
      background: #ffffff;
      width: 100%;
      max-width: 420px;
      height: 100%;
      display: flex;
      flex-direction: column;
      box-shadow: -10px 0 30px rgba(0, 0, 0, 0.15);
      animation: slideIn 0.25s ease-out;
    }
    @keyframes slideIn {
      from { transform: translateX(100%); }
      to { transform: translateX(0); }
    }
    .drawer-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
    }
    .header-title {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .header-title h3 {
      font-size: 15px;
      font-weight: 700;
      color: #0f172a;
      margin: 0;
    }
    .settings-icon {
      font-size: 18px;
    }
    .btn-close {
      background: none;
      border: none;
      font-size: 18px;
      color: #64748b;
      cursor: pointer;
    }
    .drawer-body {
      padding: 20px;
      flex: 1;
      overflow-y: auto;
    }
    .setting-group {
      margin-bottom: 18px;
    }
    .setting-label {
      display: block;
      font-size: 12.5px;
      font-weight: 600;
      color: #334155;
      margin-bottom: 6px;
    }
    .setting-hint {
      font-size: 11.5px;
      color: #94a3b8;
      margin-top: 4px;
    }
    .form-select, .form-input {
      width: 100%;
      padding: 8px 10px;
      font-size: 13px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      outline: none;
      font-family: inherit;
    }
    .form-select:focus, .form-input:focus {
      border-color: #0284c7;
    }
    .form-range {
      width: 100%;
    }
    .drawer-footer {
      padding: 14px 20px;
      background: #f8fafc;
      border-top: 1px solid #e2e8f0;
    }
    .btn-save {
      width: 100%;
      background: #0284c7;
      color: #ffffff;
      border: none;
      padding: 10px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-save:hover {
      background: #0369a1;
    }
  `]
})
export class SettingsDrawerComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  readonly isOpen = this.resumeService.showSettingsDrawer;
  config: LLMConfig = { ...this.resumeService.llmConfig() };

  close(): void {
    this.resumeService.showSettingsDrawer.set(false);
  }

  save(): void {
    this.resumeService.llmConfig.set(this.config);
    this.close();
  }
}
