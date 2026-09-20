import { Component, ElementRef, ViewChild, computed, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResumeGeneratorService } from '../../services/resume-generator.service';

@Component({
  selector: 'app-stream-console',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="stream-console-card">
      <div class="console-header">
        <div class="header-left">
          <span class="live-dot" [class.pulsing]="isStreaming()"></span>
          <span class="console-title">AI Decision Stream & Alignment Engine</span>
        </div>
        @if (isStreaming()) {
          <span class="status-badge streaming">Processing Stream...</span>
        } @else if (currentStep() === 'done') {
          <span class="status-badge done">✓ Generation Complete</span>
        }
      </div>

      <!-- Step Stepper -->
      <div class="stepper-bar">
        <div class="step-item" [class.active]="currentStep() === 'analysis'" [class.completed]="isPast('analysis')">
          <span class="step-num">1</span>
          <span class="step-name">Job Analysis</span>
        </div>
        <div class="step-divider"></div>
        <div class="step-item" [class.active]="currentStep() === 'audit'" [class.completed]="isPast('audit')">
          <span class="step-num">2</span>
          <span class="step-name">Truth Audit</span>
        </div>
        <div class="step-divider"></div>
        <div class="step-item" [class.active]="currentStep() === 'synthesis'" [class.completed]="isPast('synthesis')">
          <span class="step-num">3</span>
          <span class="step-name">Synthesis</span>
        </div>
        <div class="step-divider"></div>
        <div class="step-item" [class.active]="currentStep() === 'verification'" [class.completed]="isPast('verification')">
          <span class="step-num">4</span>
          <span class="step-name">Anti-Hallucination</span>
        </div>
      </div>

      <!-- Terminal Output Window -->
      <div class="terminal-window" #terminalBox>
        @if (logs().length === 0 && !isStreaming()) {
          <div class="terminal-placeholder">
            <span class="term-prefix">&gt;</span> Ready. Paste a LinkedIn URL or Job Description above and click "Generate Tailored ATS Resume" to watch real-time AI reasoning and decision-making.
          </div>
        } @else {
          @for (log of logs(); track log.timestamp + log.content) {
            <div class="log-row">
              <span class="log-time">[{{ log.timestamp }}]</span>
              <span class="log-step" [ngClass]="log.step">{{ formatStep(log.step) }}</span>
              <span class="log-content">{{ log.content }}</span>
            </div>
          }
          @if (isStreaming()) {
            <div class="log-row current-streaming">
              <span class="cursor-blink">▍</span>
            </div>
          }
        }
      </div>

      <!-- Audit Report Summary Card -->
      @if (auditReport()) {
        <div class="audit-summary-card">
          <div class="audit-header">
            <div class="match-score-badge">
              <span class="score-num">{{ auditReport()?.match_score }}%</span>
              <span class="score-label">Competency Match</span>
            </div>
            <div class="hallucination-badge">
              <span class="guard-icon">🛡️</span>
              <span class="guard-text">Anti-Hallucination: <strong>PASSED</strong></span>
            </div>
          </div>

          <div class="competencies-grid">
            <div class="comp-col">
              <span class="comp-title">✓ Verified Direct Matches</span>
              <div class="comp-badges">
                @for (skill of auditReport()?.direct_matches; track skill) {
                  <span class="badge direct">{{ skill }}</span>
                }
              </div>
            </div>
            @if (auditReport()?.transferable_skills?.length) {
              <div class="comp-col">
                <span class="comp-title">🔄 Transferable Capabilities</span>
                <div class="comp-badges">
                  @for (skill of auditReport()?.transferable_skills; track skill) {
                    <span class="badge transferable">{{ skill }}</span>
                  }
                </div>
              </div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .stream-console-card {
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #1e293b;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .console-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 18px;
      background: #1e293b;
      border-bottom: 1px solid #334155;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .live-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #64748b;
    }
    .live-dot.pulsing {
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.6; transform: scale(1.2); }
    }
    .console-title {
      font-size: 13px;
      font-weight: 600;
      color: #f1f5f9;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .status-badge {
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
    }
    .status-badge.streaming {
      background: rgba(2, 132, 199, 0.2);
      color: #38bdf8;
      border: 1px solid rgba(2, 132, 199, 0.4);
    }
    .status-badge.done {
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .stepper-bar {
      display: flex;
      align-items: center;
      padding: 10px 18px;
      background: #090d16;
      border-bottom: 1px solid #1e293b;
      font-size: 11px;
    }
    .step-item {
      display: flex;
      align-items: center;
      gap: 6px;
      color: #64748b;
    }
    .step-item.active {
      color: #38bdf8;
      font-weight: 600;
    }
    .step-item.completed {
      color: #34d399;
    }
    .step-num {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #1e293b;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
    }
    .step-item.active .step-num {
      background: #0284c7;
      color: #ffffff;
    }
    .step-item.completed .step-num {
      background: #059669;
      color: #ffffff;
    }
    .step-divider {
      flex: 1;
      height: 1px;
      background: #1e293b;
      margin: 0 10px;
    }
    .terminal-window {
      padding: 16px 18px;
      height: 220px;
      overflow-y: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      line-height: 1.6;
      background: #020617;
    }
    .terminal-placeholder {
      color: #64748b;
      padding-top: 10px;
    }
    .term-prefix {
      color: #0284c7;
      margin-right: 6px;
    }
    .log-row {
      margin-bottom: 8px;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .log-time {
      color: #475569;
      margin-right: 8px;
      font-size: 10.5px;
    }
    .log-step {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: 600;
      margin-right: 8px;
      text-transform: uppercase;
    }
    .log-step.analysis { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
    .log-step.audit { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .log-step.synthesis { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
    .log-step.verification { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .log-content {
      color: #e2e8f0;
    }
    .cursor-blink {
      color: #38bdf8;
      animation: blink 1s infinite;
    }
    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0; }
    }
    .audit-summary-card {
      padding: 14px 18px;
      background: #0f172a;
      border-top: 1px solid #1e293b;
    }
    .audit-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .match-score-badge {
      display: flex;
      align-items: baseline;
      gap: 6px;
    }
    .score-num {
      font-size: 20px;
      font-weight: 700;
      color: #38bdf8;
    }
    .score-label {
      font-size: 12px;
      color: #94a3b8;
    }
    .hallucination-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11.5px;
      color: #34d399;
    }
    .competencies-grid {
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 11.5px;
    }
    .comp-title {
      color: #94a3b8;
      font-size: 11px;
      font-weight: 600;
      display: block;
      margin-bottom: 4px;
    }
    .comp-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .badge {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
    }
    .badge.direct {
      background: #1e293b;
      color: #38bdf8;
      border: 1px solid #0284c7;
    }
    .badge.transferable {
      background: #1e293b;
      color: #e2e8f0;
      border: 1px solid #475569;
    }
  `]
})
export class StreamConsoleComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  @ViewChild('terminalBox') terminalBox!: ElementRef<HTMLDivElement>;

  readonly logs = this.resumeService.streamLogs;
  readonly isStreaming = this.resumeService.isStreaming;
  readonly currentStep = this.resumeService.currentStep;
  readonly auditReport = this.resumeService.auditReport;

  constructor() {
    // Auto-scroll terminal when logs arrive
    effect(() => {
      this.logs();
      setTimeout(() => {
        if (this.terminalBox) {
          this.terminalBox.nativeElement.scrollTop = this.terminalBox.nativeElement.scrollHeight;
        }
      }, 50);
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
