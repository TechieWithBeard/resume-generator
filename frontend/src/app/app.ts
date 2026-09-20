import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from './components/header/header.component';
import { JobInputComponent } from './components/job-input/job-input.component';
import { StreamConsoleComponent } from './components/stream-console/stream-console.component';
import { ResumePreviewComponent } from './components/resume-preview/resume-preview.component';
import { BaseResumeModalComponent } from './components/base-resume-modal/base-resume-modal.component';
import { SettingsDrawerComponent } from './components/settings-drawer/settings-drawer.component';
import { TemplateConfigModalComponent } from './components/template-config-modal/template-config-modal.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    JobInputComponent,
    StreamConsoleComponent,
    ResumePreviewComponent,
    BaseResumeModalComponent,
    SettingsDrawerComponent,
    TemplateConfigModalComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {}
