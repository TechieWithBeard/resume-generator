import {
  Component,
  ElementRef,
  SecurityContext,
  ViewChild,
  computed,
  effect,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ResumeGeneratorService } from '../../services/resume-generator.service';

@Component({
  selector: 'app-resume-preview',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="preview-card">
      <div class="preview-toolbar">
        <div class="toolbar-left">
          <span class="preview-label">Live ATS Resume Preview</span>
          <!-- Template selector buttons -->
          <div class="template-selector">
            @for (tmpl of templates(); track tmpl.id) {
              <button
                type="button"
                class="btn-tmpl"
                [class.active]="selectedTemplate() === tmpl.id"
                (click)="onSelectTemplate(tmpl.id)"
                [title]="tmpl.description"
              >
                {{ tmpl.name }}
              </button>
            }
          </div>
        </div>

        <div class="toolbar-right">
          <!-- Diff comparison toggle -->
          <button
            type="button"
            class="btn-tool"
            [class.active]="comparisonMode()"
            (click)="onToggleDiff()"
            title="Highlight tailored modifications and emphasized achievements"
          >
            🔍 {{ comparisonMode() ? 'Diff View Active' : 'Highlight Changes' }}
          </button>

          <!-- Export buttons -->
          <button
            type="button"
            class="btn-export btn-pdf"
            (click)="onDownloadPdf()"
            title="Export as vector PDF via browser print"
          >
            🖨️ PDF
          </button>
          <button
            type="button"
            class="btn-export btn-html"
            (click)="onDownloadHtml()"
            title="Download standalone ATS HTML file"
          >
            🌐 HTML
          </button>
          <button
            type="button"
            class="btn-export btn-json"
            (click)="onDownloadJson()"
            title="Download raw resume JSON"
          >
            &#123; &#125; JSON
          </button>
        </div>
      </div>

      <!-- Resume Render Paper Frame -->
      <div class="paper-container">
        @if (renderedHtml()) {
          <iframe
            #resumeIframe
            class="resume-frame"
            title="Resume Preview"
            [srcdoc]="renderedHtml()"
          ></iframe>
        } @else {
          <div class="empty-state">
            <div class="empty-icon">📄</div>
            <div class="empty-text">Loading Base Resume (Source of Truth)...</div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .preview-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      height: 100%;
      min-height: 750px;
      box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
    }
    .preview-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 18px;
      background: #f8fafc;
      border-bottom: 1px solid #e2e8f0;
      flex-wrap: wrap;
      gap: 10px;
    }
    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .preview-label {
      font-size: 13.5px;
      font-weight: 700;
      color: #0f172a;
    }
    .template-selector {
      display: flex;
      background: #e2e8f0;
      padding: 2px;
      border-radius: 6px;
    }
    .btn-tmpl {
      padding: 5px 10px;
      border: none;
      background: transparent;
      font-size: 11.5px;
      font-weight: 600;
      color: #475569;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-tmpl.active {
      background: #ffffff;
      color: #0284c7;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .btn-tool {
      padding: 6px 12px;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #334155;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
    }
    .btn-tool:hover {
      background: #f1f5f9;
    }
    .btn-tool.active {
      background: #f0fdf4;
      border-color: #16a34a;
      color: #15803d;
    }
    .btn-export {
      padding: 6px 12px;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #0f172a;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-export:hover {
      background: #f8fafc;
      border-color: #94a3b8;
    }
    .btn-pdf {
      background: #0284c7;
      border-color: #0284c7;
      color: #ffffff;
    }
    .btn-pdf:hover {
      background: #0369a1;
      border-color: #0369a1;
    }
    .paper-container {
      flex: 1;
      background: #e2e8f0;
      padding: 20px;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      overflow: auto;
    }
    .resume-frame {
      width: 100%;
      height: 100%;
      min-height: 850px;
      border: none;
      background: #ffffff;
      border-radius: 4px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    }
    .empty-state {
      margin: auto;
      text-align: center;
      padding: 40px;
      color: #64748b;
    }
    .empty-icon {
      font-size: 48px;
      margin-bottom: 12px;
    }
    .empty-text {
      font-size: 14px;
      font-weight: 500;
    }
  `]
})
export class ResumePreviewComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  @ViewChild('resumeIframe') resumeIframe?: ElementRef<HTMLIFrameElement>;

  readonly renderedHtml = this.resumeService.renderedHtml;
  readonly templates = this.resumeService.availableTemplates;
  readonly selectedTemplate = this.resumeService.selectedTemplate;
  readonly comparisonMode = this.resumeService.comparisonMode;

  onSelectTemplate(tmplId: string): void {
    this.resumeService.selectTemplate(tmplId);
  }

  onToggleDiff(): void {
    this.resumeService.toggleComparisonMode();
  }

  onDownloadPdf(): void {
    this.resumeService.downloadPdf();
  }

  onDownloadHtml(): void {
    this.resumeService.downloadHtml();
  }

  onDownloadJson(): void {
    this.resumeService.downloadJson();
  }
}
