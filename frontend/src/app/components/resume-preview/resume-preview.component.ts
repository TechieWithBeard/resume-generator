import { Component, ElementRef, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { CardComponent } from '../../shared/components/card/card.component';

@Component({
  selector: 'app-resume-preview',
  standalone: true,
  imports: [CommonModule, CardComponent],
  templateUrl: './resume-preview.component.html',
  styleUrl: './resume-preview.component.scss',
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
