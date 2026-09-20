import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { JobInputComponent } from './components/job-input/job-input.component';
import { StreamConsoleComponent } from './components/stream-console/stream-console.component';
import { ResumePreviewComponent } from './components/resume-preview/resume-preview.component';
import { BaseResumeModalComponent } from './components/base-resume-modal/base-resume-modal.component';
import { SettingsDrawerComponent } from './components/settings-drawer/settings-drawer.component';
import { ResumeGeneratorService } from './services/resume-generator.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    JobInputComponent,
    StreamConsoleComponent,
    ResumePreviewComponent,
    BaseResumeModalComponent,
    SettingsDrawerComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly resumeService = inject(ResumeGeneratorService);

  readonly baseResume = this.resumeService.baseResume;
  readonly tailoredResume = this.resumeService.tailoredResume;
  readonly activeResume = this.resumeService.activeResume;
  readonly llmConfig = this.resumeService.llmConfig;

  openBaseResumeModal(): void {
    this.resumeService.showBaseResumeModal.set(true);
  }

  openSettingsDrawer(): void {
    this.resumeService.showSettingsDrawer.set(true);
  }
}
