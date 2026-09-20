import { Component, HostListener, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { LLMConfig } from '../../models/resume.models';
@Component({
  selector: 'app-settings-drawer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings-drawer.component.html',
  styleUrl: './settings-drawer.component.scss',
})
export class SettingsDrawerComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  readonly isOpen = this.resumeService.showSettingsDrawer;
  config: LLMConfig = { ...this.resumeService.llmConfig() };

  @HostListener('document:keydown.escape')
  onEscape() {
    if (this.isOpen()) {
      this.close();
    }
  }

  close(): void {
    this.resumeService.showSettingsDrawer.set(false);
  }

  save(): void {
    this.resumeService.llmConfig.set(this.config);
    this.close();
  }
}
