import { Component, ElementRef, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { CardComponent } from '../../shared/components/card/card.component';
import { GitDiffViewerComponent } from '../git-diff-viewer/git-diff-viewer.component';

@Component({
  selector: 'app-resume-preview',
  standalone: true,
  imports: [CommonModule, CardComponent, GitDiffViewerComponent],
  templateUrl: './resume-preview.component.html',
  styleUrl: './resume-preview.component.scss',
})
export class ResumePreviewComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  @ViewChild('resumeIframe') resumeIframe?: ElementRef<HTMLIFrameElement>;

  readonly renderedHtml = this.resumeService.renderedHtml;
  readonly baseRenderedHtml = this.resumeService.baseRenderedHtml;
  readonly templates = this.resumeService.availableTemplates;
  readonly selectedTemplate = this.resumeService.selectedTemplate;
  readonly comparisonMode = this.resumeService.comparisonMode;
  readonly viewMode = this.resumeService.viewMode;
  readonly documentMode = this.resumeService.documentMode;
  readonly isFullscreen = this.resumeService.isFullscreen;
  readonly previewZoom = this.resumeService.previewZoom;
  readonly auditReport = this.resumeService.auditReport;
  readonly baseResume = this.resumeService.baseResume;
  readonly tailoredResume = this.resumeService.tailoredResume;

  onSelectTemplate(tmplId: string): void {
    this.resumeService.selectTemplate(tmplId);
  }

  onSetViewMode(mode: 'single' | 'split' | 'git-diff'): void {
    this.resumeService.setViewMode(mode);
  }

  onToggleDiff(): void {
    this.resumeService.toggleComparisonMode();
  }

  onZoomIn(): void {
    this.resumeService.zoomIn();
  }

  onZoomOut(): void {
    this.resumeService.zoomOut();
  }

  onResetZoom(): void {
    this.resumeService.resetZoom();
  }

  onToggleFullscreen(): void {
    this.resumeService.toggleFullscreen();
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

  onOpenTemplateStudio(): void {
    this.resumeService.showTemplateConfigModal.set(true);
  }
}
