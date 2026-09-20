import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ResumeGeneratorService } from '../../services/resume-generator.service';
import { ExperienceItem, ProjectItem, ResumeData } from '../../models/resume.models';

export interface DiffWord {
  text: string;
  type: 'unchanged' | 'deleted' | 'added' | 'keyword';
}

export interface DiffLine {
  type: 'unchanged' | 'deleted' | 'added';
  oldLineNum?: number | null;
  newLineNum?: number | null;
  text: string;
  words?: DiffWord[];
}

export interface SplitRow {
  left?: DiffLine | null;
  right?: DiffLine | null;
}

export interface DiffHunk {
  id: string;
  title: string;
  fileLabel: string;
  header: string;
  collapsed: boolean;
  additions: number;
  deletions: number;
  lines: DiffLine[];
  splitRows: SplitRow[];
}

@Component({
  selector: 'app-git-diff-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './git-diff-viewer.component.html',
  styleUrl: './git-diff-viewer.component.scss',
})
export class GitDiffViewerComponent {
  private readonly resumeService = inject(ResumeGeneratorService);

  readonly baseResume = this.resumeService.baseResume;
  readonly tailoredResume = this.resumeService.tailoredResume;
  readonly auditReport = this.resumeService.auditReport;

  readonly diffMode = signal<'unified' | 'split'>('unified');
  readonly filterChangesOnly = signal<boolean>(false);
  readonly copiedPatch = signal<boolean>(false);
  readonly collapsedHunks = signal<Record<string, boolean>>({});

  readonly targetTerms = computed<Set<string>>(() => {
    const tailored = this.tailoredResume();
    const terms = new Set<string>();
    if (!tailored) return terms;
    if (tailored.target_role) {
      tailored.target_role
        .toLowerCase()
        .replace(/[^\w\s\+#]/g, ' ')
        .split(/\s+/)
        .filter((w) => w.length > 2 && !['and', 'for', 'the', 'developer', 'engineer'].includes(w))
        .forEach((w) => terms.add(w));
    }
    if (tailored.skills) {
      Object.values(tailored.skills).forEach((list) => {
        list.slice(0, 4).forEach((s) => terms.add(s.toLowerCase()));
      });
    }
    return terms;
  });

  readonly diffHunks = computed<DiffHunk[]>(() => {
    const base = this.baseResume();
    const tailored = this.tailoredResume() || base;
    if (!tailored) return [];

    const hunks: DiffHunk[] = [];
    const terms = this.targetTerms();
    const collapsedMap = this.collapsedHunks();

    // 1. Positioning Hunk
    const posHunk = this.buildPositioningHunk(base, tailored, terms);
    if (posHunk) hunks.push(posHunk);

    // 2. Summary Hunk
    const summaryHunk = this.buildSummaryHunk(base, tailored, terms);
    if (summaryHunk) hunks.push(summaryHunk);

    // 3. Skills Matrix Hunk
    const skillsHunk = this.buildSkillsHunk(base, tailored, terms);
    if (skillsHunk) hunks.push(skillsHunk);

    // 4. Experience Hunks (one per job experience)
    const expHunks = this.buildExperienceHunks(base, tailored, terms);
    hunks.push(...expHunks);

    // 5. Projects Hunk
    const projHunk = this.buildProjectsHunk(base, tailored, terms);
    if (projHunk) hunks.push(projHunk);

    // 6. Education Hunk
    const eduHunk = this.buildEducationHunk(base, tailored);
    if (eduHunk) hunks.push(eduHunk);

    return hunks.map((h) => ({
      ...h,
      collapsed: !!collapsedMap[h.id],
    }));
  });

  readonly totalStats = computed(() => {
    const hunks = this.diffHunks();
    let additions = 0;
    let deletions = 0;
    hunks.forEach((h) => {
      additions += h.additions;
      deletions += h.deletions;
    });
    return { additions, deletions, hunksCount: hunks.length };
  });

  readonly rawPatch = computed<string>(() => {
    const hunks = this.diffHunks();
    const tailored = this.tailoredResume();
    const role = tailored?.target_role || 'tailored-position';
    const lines: string[] = [
      `diff --git a/base_ground_truth.json b/tailored_target.json`,
      `--- a/base_ground_truth.json\t(Ground Truth Source of Truth)`,
      `+++ b/tailored_target.json\t(Tailored for ${role})`,
    ];

    hunks.forEach((h) => {
      lines.push(h.header);
      h.lines.forEach((l) => {
        const sign = l.type === 'added' ? '+' : l.type === 'deleted' ? '-' : ' ';
        lines.push(`${sign} ${l.text}`);
      });
    });

    return lines.join('\n');
  });

  onSetDiffMode(mode: 'unified' | 'split'): void {
    this.diffMode.set(mode);
  }

  onToggleFilter(): void {
    this.filterChangesOnly.update((v) => !v);
  }

  onToggleHunk(id: string): void {
    this.collapsedHunks.update((m) => ({ ...m, [id]: !m[id] }));
  }

  onExpandAll(): void {
    this.collapsedHunks.set({});
  }

  onCollapseAll(): void {
    const map: Record<string, boolean> = {};
    this.diffHunks().forEach((h) => (map[h.id] = true));
    this.collapsedHunks.set(map);
  }

  async onCopyPatch(): Promise<void> {
    try {
      await navigator.clipboard.writeText(this.rawPatch());
      this.copiedPatch.set(true);
      setTimeout(() => this.copiedPatch.set(false), 2500);
    } catch (err) {
      console.error('Failed to copy patch:', err);
    }
  }

  onDownloadPatch(): void {
    const patch = this.rawPatch();
    const blob = new Blob([patch], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resume_tailored_${Date.now()}.diff`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // --- Hunk Builders ---

  private buildPositioningHunk(
    base: ResumeData | null,
    tailored: ResumeData,
    terms: Set<string>
  ): DiffHunk | null {
    const lines: DiffLine[] = [];
    let oldNum = 1;
    let newNum = 1;

    // Title diff
    const baseTitle = base?.title?.trim() || '';
    const tailoredTitle = tailored.title?.trim() || '';
    if (baseTitle && baseTitle !== tailoredTitle) {
      lines.push({
        type: 'deleted',
        oldLineNum: oldNum++,
        text: `Title: ${baseTitle}`,
        words: this.diffWords(`Title: ${baseTitle}`, `Title: ${tailoredTitle}`, terms).deletedWords,
      });
      lines.push({
        type: 'added',
        newLineNum: newNum++,
        text: `Title: ${tailoredTitle}`,
        words: this.diffWords(`Title: ${baseTitle}`, `Title: ${tailoredTitle}`, terms).addedWords,
      });
    } else {
      lines.push({
        type: 'unchanged',
        oldLineNum: oldNum++,
        newLineNum: newNum++,
        text: `Title: ${tailoredTitle}`,
      });
    }

    // Target Role (added)
    if (tailored.target_role) {
      lines.push({
        type: 'added',
        newLineNum: newNum++,
        text: `Target Role: ${tailored.target_role}`,
        words: this.diffWords('', `Target Role: ${tailored.target_role}`, terms).addedWords,
      });
    }

    // Target Company (added)
    if (tailored.target_company) {
      lines.push({
        type: 'added',
        newLineNum: newNum++,
        text: `Target Company: ${tailored.target_company}`,
        words: this.diffWords('', `Target Company: ${tailored.target_company}`, terms).addedWords,
      });
    }

    // Tagline
    const baseTag = base?.tagline?.trim() || '';
    const tailoredTag = tailored.tagline?.trim() || '';
    if (tailoredTag && baseTag !== tailoredTag) {
      if (baseTag) {
        lines.push({
          type: 'deleted',
          oldLineNum: oldNum++,
          text: `Tagline: ${baseTag}`,
          words: this.diffWords(`Tagline: ${baseTag}`, `Tagline: ${tailoredTag}`, terms).deletedWords,
        });
      }
      lines.push({
        type: 'added',
        newLineNum: newNum++,
        text: `Tagline: ${tailoredTag}`,
        words: this.diffWords(`Tagline: ${baseTag}`, `Tagline: ${tailoredTag}`, terms).addedWords,
      });
    }

    const adds = lines.filter((l) => l.type === 'added').length;
    const dels = lines.filter((l) => l.type === 'deleted').length;

    return {
      id: 'hunk-positioning',
      title: '01 / Strategic Positioning & Target Alignment',
      fileLabel: 'dossier://metadata/positioning.json',
      header: `@@ -1,${oldNum - 1} +1,${newNum - 1} @@ [Strategic Positioning]`,
      collapsed: false,
      additions: adds,
      deletions: dels,
      lines,
      splitRows: this.buildSplitRows(lines),
    };
  }

  private buildSummaryHunk(
    base: ResumeData | null,
    tailored: ResumeData,
    terms: Set<string>
  ): DiffHunk | null {
    const baseSummary = base?.summary?.trim() || '';
    const tailoredSummary = tailored.summary?.trim() || '';
    if (!tailoredSummary) return null;

    const baseSentences = this.splitIntoSentences(baseSummary);
    const tailoredSentences = this.splitIntoSentences(tailoredSummary);

    const lines: DiffLine[] = [];
    let oldNum = 1;
    let newNum = 1;

    const maxLen = Math.max(baseSentences.length, tailoredSentences.length);
    for (let i = 0; i < maxLen; i++) {
      const bS = baseSentences[i] || '';
      const tS = tailoredSentences[i] || '';

      if (bS && tS && bS.toLowerCase() === tS.toLowerCase()) {
        lines.push({
          type: 'unchanged',
          oldLineNum: oldNum++,
          newLineNum: newNum++,
          text: tS,
        });
      } else if (bS && tS) {
        const diff = this.diffWords(bS, tS, terms);
        lines.push({
          type: 'deleted',
          oldLineNum: oldNum++,
          text: bS,
          words: diff.deletedWords,
        });
        lines.push({
          type: 'added',
          newLineNum: newNum++,
          text: tS,
          words: diff.addedWords,
        });
      } else if (bS && !tS) {
        lines.push({
          type: 'deleted',
          oldLineNum: oldNum++,
          text: bS,
          words: this.diffWords(bS, '', terms).deletedWords,
        });
      } else if (!bS && tS) {
        lines.push({
          type: 'added',
          newLineNum: newNum++,
          text: tS,
          words: this.diffWords('', tS, terms).addedWords,
        });
      }
    }

    const adds = lines.filter((l) => l.type === 'added').length;
    const dels = lines.filter((l) => l.type === 'deleted').length;

    return {
      id: 'hunk-summary',
      title: '02 / Executive Career Architecture & Strategic Profile',
      fileLabel: 'dossier://sections/01_executive_summary.md',
      header: `@@ -1,${oldNum - 1} +1,${newNum - 1} @@ [Summary Profile]`,
      collapsed: false,
      additions: adds,
      deletions: dels,
      lines,
      splitRows: this.buildSplitRows(lines),
    };
  }

  private buildSkillsHunk(
    base: ResumeData | null,
    tailored: ResumeData,
    terms: Set<string>
  ): DiffHunk | null {
    if (!tailored.skills) return null;
    const lines: DiffLine[] = [];
    let oldNum = 1;
    let newNum = 1;

    for (const [cat, skills] of Object.entries(tailored.skills)) {
      const baseSkills = base?.skills?.[cat] || [];
      const catLabel = cat.replace(/_/g, ' ').toUpperCase();

      const baseLine = `${catLabel}: ${baseSkills.join(', ')}`;
      const tailoredLine = `${catLabel}: ${skills.join(', ')}`;

      if (baseSkills.length > 0 && baseLine === tailoredLine) {
        lines.push({
          type: 'unchanged',
          oldLineNum: oldNum++,
          newLineNum: newNum++,
          text: tailoredLine,
        });
      } else {
        if (baseSkills.length > 0) {
          lines.push({
            type: 'deleted',
            oldLineNum: oldNum++,
            text: baseLine,
            words: this.diffWords(baseLine, tailoredLine, terms).deletedWords,
          });
        }
        lines.push({
          type: 'added',
          newLineNum: newNum++,
          text: tailoredLine,
          words: this.diffWords(baseLine, tailoredLine, terms).addedWords,
        });
      }
    }

    const adds = lines.filter((l) => l.type === 'added').length;
    const dels = lines.filter((l) => l.type === 'deleted').length;

    return {
      id: 'hunk-skills',
      title: '03 / Core Competencies & Technical Taxonomy',
      fileLabel: 'dossier://sections/02_technical_skills.json',
      header: `@@ -1,${oldNum - 1} +1,${newNum - 1} @@ [Competencies Matrix]`,
      collapsed: false,
      additions: adds,
      deletions: dels,
      lines,
      splitRows: this.buildSplitRows(lines),
    };
  }

  private buildExperienceHunks(
    base: ResumeData | null,
    tailored: ResumeData,
    terms: Set<string>
  ): DiffHunk[] {
    const hunks: DiffHunk[] = [];
    const baseExps = base?.experience || [];

    tailored.experience.forEach((exp, idx) => {
      const baseExp =
        baseExps.find(
          (b) => b.company.trim().toLowerCase() === exp.company.trim().toLowerCase()
        ) || baseExps[idx];

      const lines: DiffLine[] = [];
      let oldNum = 1;
      let newNum = 1;

      // Header info (Role, Period)
      const baseRole = baseExp?.role || '';
      if (baseRole && baseRole !== exp.role) {
        lines.push({
          type: 'deleted',
          oldLineNum: oldNum++,
          text: `ROLE: ${baseRole} | ${exp.company}`,
          words: this.diffWords(baseRole, exp.role, terms).deletedWords,
        });
        lines.push({
          type: 'added',
          newLineNum: newNum++,
          text: `ROLE: ${exp.role} | ${exp.company}`,
          words: this.diffWords(baseRole, exp.role, terms).addedWords,
        });
      } else {
        lines.push({
          type: 'unchanged',
          oldLineNum: oldNum++,
          newLineNum: newNum++,
          text: `ROLE: ${exp.role} | ${exp.company} (${exp.period})`,
        });
      }

      // Scope
      if (exp.scope) {
        const baseScope = baseExp?.scope || '';
        if (baseScope && baseScope !== exp.scope) {
          lines.push({
            type: 'deleted',
            oldLineNum: oldNum++,
            text: `SCOPE: ${baseScope}`,
            words: this.diffWords(baseScope, exp.scope, terms).deletedWords,
          });
          lines.push({
            type: 'added',
            newLineNum: newNum++,
            text: `SCOPE: ${exp.scope}`,
            words: this.diffWords(baseScope, exp.scope, terms).addedWords,
          });
        } else if (!baseScope) {
          lines.push({
            type: 'added',
            newLineNum: newNum++,
            text: `SCOPE: ${exp.scope}`,
            words: this.diffWords('', exp.scope, terms).addedWords,
          });
        } else {
          lines.push({
            type: 'unchanged',
            oldLineNum: oldNum++,
            newLineNum: newNum++,
            text: `SCOPE: ${exp.scope}`,
          });
        }
      }

      // Bullets
      const baseBullets = baseExp?.highlights || [];
      const baseBulletSet = new Set(baseBullets.map((b) => b.trim().toLowerCase()));

      exp.highlights.forEach((h) => {
        const hClean = h.trim().toLowerCase();
        if (baseBulletSet.has(hClean)) {
          lines.push({
            type: 'unchanged',
            oldLineNum: oldNum++,
            newLineNum: newNum++,
            text: `• ${h}`,
          });
        } else {
          // Find closest base bullet
          const closestBase = this.findClosestMatch(h, baseBullets);
          if (closestBase) {
            const diff = this.diffWords(closestBase, h, terms);
            lines.push({
              type: 'deleted',
              oldLineNum: oldNum++,
              text: `• ${closestBase}`,
              words: diff.deletedWords,
            });
            lines.push({
              type: 'added',
              newLineNum: newNum++,
              text: `• ${h}`,
              words: diff.addedWords,
            });
          } else {
            lines.push({
              type: 'added',
              newLineNum: newNum++,
              text: `• ${h}`,
              words: this.diffWords('', h, terms).addedWords,
            });
          }
        }
      });

      const adds = lines.filter((l) => l.type === 'added').length;
      const dels = lines.filter((l) => l.type === 'deleted').length;

      hunks.push({
        id: `hunk-exp-${idx}`,
        title: `04 / Experience: ${exp.company} — ${exp.role}`,
        fileLabel: `dossier://experience/${exp.company.replace(/\s+/g, '_').toLowerCase()}.md`,
        header: `@@ -1,${oldNum - 1} +1,${newNum - 1} @@ [${exp.company}]`,
        collapsed: false,
        additions: adds,
        deletions: dels,
        lines,
        splitRows: this.buildSplitRows(lines),
      });
    });

    return hunks;
  }

  private buildProjectsHunk(
    base: ResumeData | null,
    tailored: ResumeData,
    terms: Set<string>
  ): DiffHunk | null {
    const projects = tailored.projects || [];
    if (projects.length === 0) return null;

    const baseProjects = base?.projects || [];
    const lines: DiffLine[] = [];
    let oldNum = 1;
    let newNum = 1;

    projects.forEach((p) => {
      const baseP = baseProjects.find(
        (bp) => bp.name.trim().toLowerCase() === p.name.trim().toLowerCase()
      );

      lines.push({
        type: 'unchanged',
        oldLineNum: oldNum++,
        newLineNum: newNum++,
        text: `PROJECT: ${p.name} ${p.period ? '(' + p.period + ')' : ''}`,
      });

      if (baseP && baseP.description !== p.description) {
        const diff = this.diffWords(baseP.description, p.description, terms);
        lines.push({
          type: 'deleted',
          oldLineNum: oldNum++,
          text: `  ${baseP.description}`,
          words: diff.deletedWords,
        });
        lines.push({
          type: 'added',
          newLineNum: newNum++,
          text: `  ${p.description}`,
          words: diff.addedWords,
        });
      } else if (!baseP) {
        lines.push({
          type: 'added',
          newLineNum: newNum++,
          text: `  ${p.description}`,
          words: this.diffWords('', p.description, terms).addedWords,
        });
      } else {
        lines.push({
          type: 'unchanged',
          oldLineNum: oldNum++,
          newLineNum: newNum++,
          text: `  ${p.description}`,
        });
      }

      if (p.technologies && p.technologies.length > 0) {
        const techStr = `  Stack: ${p.technologies.join(', ')}`;
        lines.push({
          type: 'unchanged',
          oldLineNum: oldNum++,
          newLineNum: newNum++,
          text: techStr,
        });
      }
    });

    const adds = lines.filter((l) => l.type === 'added').length;
    const dels = lines.filter((l) => l.type === 'deleted').length;

    return {
      id: 'hunk-projects',
      title: '05 / Architectural Projects & Case Studies',
      fileLabel: 'dossier://sections/03_case_studies.json',
      header: `@@ -1,${oldNum - 1} +1,${newNum - 1} @@ [Projects & Architecture]`,
      collapsed: false,
      additions: adds,
      deletions: dels,
      lines,
      splitRows: this.buildSplitRows(lines),
    };
  }

  private buildEducationHunk(base: ResumeData | null, tailored: ResumeData): DiffHunk | null {
    if (!tailored.education || tailored.education.length === 0) return null;
    const lines: DiffLine[] = [];
    let oldNum = 1;
    let newNum = 1;

    tailored.education.forEach((edu) => {
      lines.push({
        type: 'unchanged',
        oldLineNum: oldNum++,
        newLineNum: newNum++,
        text: `${edu.degree} — ${edu.institution} (${edu.period})`,
      });
    });

    return {
      id: 'hunk-education',
      title: '06 / Education & Verified Academic Background',
      fileLabel: 'dossier://credentials/education.md',
      header: `@@ -1,${oldNum - 1} +1,${newNum - 1} @@ [Education (Verified Invariant)]`,
      collapsed: false,
      additions: 0,
      deletions: 0,
      lines,
      splitRows: this.buildSplitRows(lines),
    };
  }

  // --- Split Rows Builder ---

  private buildSplitRows(lines: DiffLine[]): SplitRow[] {
    const rows: SplitRow[] = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (line.type === 'unchanged') {
        rows.push({ left: line, right: line });
        i++;
      } else if (line.type === 'deleted') {
        const next = lines[i + 1];
        if (next && next.type === 'added') {
          rows.push({ left: line, right: next });
          i += 2;
        } else {
          rows.push({ left: line, right: null });
          i++;
        }
      } else if (line.type === 'added') {
        rows.push({ left: null, right: line });
        i++;
      }
    }
    return rows;
  }

  // --- Diff Words Tokenizer ---

  private diffWords(
    oldText: string,
    newText: string,
    terms: Set<string>
  ): { deletedWords: DiffWord[]; addedWords: DiffWord[] } {
    const oldWords = oldText.split(/\s+/).filter(Boolean);
    const newWords = newText.split(/\s+/).filter(Boolean);

    const oldSet = new Set(oldWords.map((w) => w.toLowerCase().replace(/[^\w]/g, '')));
    const newSet = new Set(newWords.map((w) => w.toLowerCase().replace(/[^\w]/g, '')));

    const deletedWords: DiffWord[] = oldWords.map((w) => {
      const clean = w.toLowerCase().replace(/[^\w]/g, '');
      const isDeleted = !newSet.has(clean);
      return {
        text: w,
        type: isDeleted ? 'deleted' : 'unchanged',
      };
    });

    const addedWords: DiffWord[] = newWords.map((w) => {
      const clean = w.toLowerCase().replace(/[^\w]/g, '');
      const isAdded = !oldSet.has(clean);
      const isKw = terms.has(clean) || Array.from(terms).some((t) => t.length > 3 && clean.includes(t));
      return {
        text: w,
        type: isKw ? 'keyword' : isAdded ? 'added' : 'unchanged',
      };
    });

    return { deletedWords, addedWords };
  }

  private splitIntoSentences(text: string): string[] {
    if (!text) return [];
    return text
      .split(/(?<=[.!?])\s+/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  private findClosestMatch(target: string, candidates: string[]): string | null {
    if (!candidates || candidates.length === 0) return null;
    const tWords = new Set(target.toLowerCase().split(/\s+/));
    let bestMatch: string | null = null;
    let maxOverlap = 0;

    for (const c of candidates) {
      const cWords = c.toLowerCase().split(/\s+/);
      let overlap = 0;
      for (const w of cWords) {
        if (tWords.has(w)) overlap++;
      }
      const score = overlap / Math.max(tWords.size, cWords.length);
      if (score > 0.25 && score > maxOverlap) {
        maxOverlap = score;
        bestMatch = c;
      }
    }

    return bestMatch;
  }
}
