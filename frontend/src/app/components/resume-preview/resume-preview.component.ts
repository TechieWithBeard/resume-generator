import { Component, ElementRef, ViewChild, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { CardComponent } from '../../shared/components/card/card.component';
import { GitDiffViewerComponent } from '../git-diff-viewer/git-diff-viewer.component';
import { IframeHtmlDirective } from '../../shared/directives/iframe-html.directive';

@Component({
  selector: 'app-resume-preview',
  standalone: true,
  imports: [CommonModule, CardComponent, GitDiffViewerComponent, IframeHtmlDirective],
  templateUrl: './resume-preview.component.html',
  styleUrl: './resume-preview.component.scss',
})
export class ResumePreviewComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  @ViewChild('resumeIframe') resumeIframe?: ElementRef<HTMLIFrameElement>;
  @ViewChild('baseResumeIframe') baseResumeIframe?: ElementRef<HTMLIFrameElement>;
  @ViewChild('tailoredResumeIframe') tailoredResumeIframe?: ElementRef<HTMLIFrameElement>;

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

  constructor() {
    effect(() => {
      // Re-adjust iframe height when renderedHtml changes
      const _ = this.renderedHtml();
      setTimeout(() => {
        this.adjustIframeHeight(this.resumeIframe?.nativeElement);
        this.adjustIframeHeight(this.tailoredResumeIframe?.nativeElement);
      }, 50);
    });

    effect(() => {
      const _ = this.baseRenderedHtml();
      setTimeout(() => {
        this.adjustIframeHeight(this.baseResumeIframe?.nativeElement);
      }, 50);
    });
  }

  onIframeLoad(event: Event): void {
    const iframe = event.target as HTMLIFrameElement;
    this.adjustIframeHeight(iframe);
  }

  adjustIframeHeight(iframe?: HTMLIFrameElement | null): void {
    if (!iframe) return;
    try {
      const doc = iframe.contentDocument || iframe.contentWindow?.document;
      if (doc && doc.body) {
        doc.body.style.overflow = 'hidden';
        const height = Math.max(doc.body.scrollHeight, doc.documentElement.scrollHeight);
        if (height > 0) {
          iframe.style.height = `${height + 24}px`;
        }
      }
    } catch {
      iframe.style.height = '1100px';
    }
  }

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
