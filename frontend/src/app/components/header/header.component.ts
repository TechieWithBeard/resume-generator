import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { BadgeComponent } from '../../shared/components/badge/badge.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, BadgeComponent],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss',
})
export class HeaderComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  readonly activeResume = this.resumeService.activeResume;
  readonly llmConfig = this.resumeService.llmConfig;

  openBaseResumeModal(): void {
    this.resumeService.showBaseResumeModal.set(true);
  }

  openSettingsDrawer(): void {
    this.resumeService.showSettingsDrawer.set(true);
  }
}
