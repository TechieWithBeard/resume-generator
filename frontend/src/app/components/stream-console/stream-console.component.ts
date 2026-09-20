import { Component, ElementRef, ViewChild, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { CardComponent } from '../../shared/components/card/card.component';
import { BadgeComponent } from '../../shared/components/badge/badge.component';

@Component({
  selector: 'app-stream-console',
  standalone: true,
  imports: [CommonModule, CardComponent, BadgeComponent],
  templateUrl: './stream-console.component.html',
  styleUrl: './stream-console.component.scss',
})
export class StreamConsoleComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  @ViewChild('terminalBox') terminalBox!: ElementRef<HTMLDivElement>;

  readonly logs = this.resumeService.streamLogs;
  readonly isStreaming = this.resumeService.isStreaming;
  readonly currentStep = this.resumeService.currentStep;
  readonly auditReport = this.resumeService.auditReport;

  constructor() {
    effect(() => {
      this.logs();
      setTimeout(() => {
        if (this.terminalBox) {
          this.terminalBox.nativeElement.scrollTop = this.terminalBox.nativeElement.scrollHeight;
        }
      }, 40);
    });
  }

  formatStep(step: string): string {
    const map: Record<string, string> = {
      analysis: 'Deconstruct',
      audit: 'Truth Audit',
      synthesis: 'Synthesize',
      verification: 'Guardrail',
    };
    return map[step] || step;
  }

  isPast(step: string): boolean {
    const order = ['analysis', 'audit', 'synthesis', 'verification', 'done'];
    const currentIdx = order.indexOf(this.currentStep());
    const targetIdx = order.indexOf(step);
    return currentIdx > targetIdx;
  }
}
