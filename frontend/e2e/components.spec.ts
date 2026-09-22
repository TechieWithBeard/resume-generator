import { test, expect } from '@playwright/test';

test.describe('Component-Level Interaction & DOM Structure Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('app-header')).toBeVisible({ timeout: 15000 });
  });

  test('Component: HeaderComponent - branding, status, and modal triggers', async ({ page }) => {
    const header = page.locator('app-header');
    await expect(header).toBeVisible();

    // 1. Brand logo and titles
    await expect(header.locator('.w-9.h-9')).toHaveText('AI');
    await expect(header.getByRole('heading', { level: 1 })).toHaveText('Resume Architect');
    await expect(header.locator('app-badge')).toContainText('ATS Engine');

    // 2. Ground Truth button
    const groundTruthBtn = header.locator('button').filter({ hasText: 'Source of Truth' });
    await expect(groundTruthBtn).toBeVisible();
    await expect(groundTruthBtn).toContainText('Alex Mercer');
    await expect(groundTruthBtn.locator('span').filter({ hasText: 'Edit' })).toBeVisible();

    // 3. Settings button
    const settingsBtn = header.locator('button').filter({ hasText: /⚙️/ });
    await expect(settingsBtn).toBeVisible();
    await expect(settingsBtn).toContainText(/(auto|heuristic|ollama|openai)/i);
  });

  test('Component: JobInputComponent - input fields, validation, and mode switches', async ({ page }) => {
    const jobInput = page.locator('app-job-input');
    await expect(jobInput).toBeVisible();

    // 1. Navigation tabs
    const textTab = jobInput.getByRole('button', { name: /Paste Job Content/ });
    const linkedinTab = jobInput.getByRole('button', { name: /LinkedIn Job URL/ });
    await expect(textTab).toBeVisible();
    await expect(linkedinTab).toBeVisible();

    // 2. Source of truth status card
    await expect(jobInput.getByText('Source of Truth')).toBeVisible();
    await expect(jobInput.getByText('✓ Loaded & Grounded')).toBeVisible();
    const reviewBtn = jobInput.getByRole('button', { name: 'Review' });
    await expect(reviewBtn).toBeVisible();

    // 3. Document Mode Buttons
    const targetedBtn = jobInput.getByRole('button', { name: /Targeted Resume/ });
    const cvBtn = jobInput.getByRole('button', { name: /Custom CV/ });
    await expect(targetedBtn).toBeVisible();
    await expect(cvBtn).toBeVisible();

    // 4. Job Description Textarea and Character Counter
    const textarea = jobInput.locator('#jobDesc');
    await expect(textarea).toBeVisible();
    await textarea.fill('Short JD');
    // Button prompts user when requirements are empty or short
    const promptBtn = jobInput.getByRole('button', { name: /Paste Target Job Description/ });
    await expect(promptBtn).toBeVisible();

    // Fill with enough characters
    await textarea.fill('A'.repeat(50));
    await expect(jobInput.getByText('(50 characters)')).toBeVisible();
    const generateBtn = jobInput.getByRole('button', { name: /Generate Tailored ATS Resume/ });
    await expect(generateBtn).toBeVisible();

    // 5. Target Title Input
    const titleInput = jobInput.locator('#targetTitle');
    await expect(titleInput).toBeVisible();
    await titleInput.fill('Lead Systems Engineer');
    await expect(titleInput).toHaveValue('Lead Systems Engineer');
  });

  test('Component: StreamConsoleComponent - collapse toggle and pipeline stage indicators', async ({ page }) => {
    const streamConsole = page.locator('app-stream-console');
    await expect(streamConsole).toBeVisible();

    // 1. Terminal title and step badge
    await expect(streamConsole.getByText('AI Reasoning Stream & Audit')).toBeVisible();

    // 2. Pipeline stepper indicators
    await expect(streamConsole.getByText('Job Analysis')).toBeVisible();
    await expect(streamConsole.getByText('Truth Audit')).toBeVisible();
    await expect(streamConsole.getByText('Synthesis')).toBeVisible();
    await expect(streamConsole.getByText('Guardrail')).toBeVisible();

    // 3. Terminal output container
    const terminalBox = streamConsole.locator('div.font-mono').first();
    await expect(terminalBox).toBeVisible();

    // 4. Toggle collapse / expand
    const collapseBtn = streamConsole.getByRole('button', { name: /Collapse|Show Stream/ });
    await expect(collapseBtn).toBeVisible();
    await collapseBtn.click();
    // After collapsing, button changes to Show Stream
    await expect(streamConsole.getByRole('button', { name: /Show Stream/ })).toBeVisible();
    // Re-expand
    await streamConsole.getByRole('button', { name: /Show Stream/ }).click();
    await expect(streamConsole.getByRole('button', { name: /Collapse/ })).toBeVisible();
  });

  test('Component: ResumePreviewComponent - toolbar, zoom, view modes, and export actions', async ({ page }) => {
    const preview = page.locator('app-resume-preview');
    await expect(preview).toBeVisible();

    // 1. Segmented View Switcher buttons
    await expect(preview.getByRole('button', { name: /Single View/ })).toBeVisible();
    await expect(preview.getByRole('button', { name: /Compare with Base/ })).toBeVisible();
    await expect(preview.getByRole('button', { name: /Text Diff/ })).toBeVisible();

    // 2. Template Selector Dropdown
    const templateSelect = preview.locator('select');
    await expect(templateSelect).toBeVisible();
    const options = await templateSelect.locator('option').allTextContents();
    expect(options.length).toBeGreaterThanOrEqual(3);

    // 3. Styling / Customizer Button
    const styleBtn = preview.getByRole('button', { name: /Styling/ });
    await expect(styleBtn).toBeVisible();

    // 4. Zoom Controls
    const zoomReset = preview.getByTitle('Reset zoom to 100%');
    await expect(zoomReset).toHaveText('100%');

    // 5. Fullscreen button
    const fullscreenBtn = preview.getByRole('button', { name: /Fullscreen/ });
    await expect(fullscreenBtn).toBeVisible();

    // 6. Export Buttons
    await expect(preview.getByRole('button', { name: /PDF/ })).toBeVisible();
    await expect(preview.getByRole('button', { name: /HTML/ })).toBeVisible();
    await expect(preview.getByRole('button', { name: /JSON/ })).toBeVisible();

    // 7. Embedded Preview Iframe
    const iframe = preview.locator('iframe[title="Resume Live Preview"]');
    await expect(iframe).toBeVisible();
  });

  test('Component: BaseResumeModalComponent - tabs, inputs, accordion, and controls', async ({ page }) => {
    // Open Ground Truth modal
    await page.locator('app-job-input button').filter({ hasText: 'Review' }).click();

    const modal = page.locator('app-base-resume-modal app-modal');
    await expect(modal).toBeVisible();

    // 1. Header and Icon
    await expect(modal.getByText('Candidate Ground Truth (Source of Truth)')).toBeVisible();
    await expect(modal.locator('[modal-header-icon]')).toHaveText('🛡️');

    // 2. Tab Navigation
    const structuredTab = modal.getByRole('button', { name: /Structured Profile/ });
    const rawTab = modal.getByRole('button', { name: /Raw Knowledge Base/ });
    const jsonTab = modal.getByRole('button', { name: /JSON Schema/ });
    await expect(structuredTab).toBeVisible();
    await expect(rawTab).toBeVisible();
    await expect(jsonTab).toBeVisible();

    // 3. Contact & Candidate Identification inputs
    await expect(modal.getByText('Full Name')).toBeVisible();
    await expect(modal.getByText('Professional Title')).toBeVisible();
    await expect(modal.getByText('Email')).toBeVisible();
    await expect(modal.getByText('Phone')).toBeVisible();
    await expect(modal.getByText('LinkedIn Profile')).toBeVisible();
    await expect(modal.getByText('GitHub Profile')).toBeVisible();

    // 4. Upload drop zone
    await expect(modal.getByText('Upload Candidate Resume / CV')).toBeVisible();

    // 5. Action Buttons
    await expect(modal.getByRole('button', { name: /Reset to Baseline/ })).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Cancel' })).toBeVisible();
    await expect(modal.getByRole('button', { name: /Save Ground Truth/ })).toBeVisible();

    // Close modal
    await modal.getByRole('button', { name: 'Cancel' }).click();
    await expect(modal).not.toBeVisible();
  });

  test('Component: TemplateConfigModalComponent - design controls, swatches, and live frame', async ({ page }) => {
    // Open Template Studio
    await page.getByRole('button', { name: /Styling/ }).click();

    const modal = page.locator('app-template-config-modal app-modal');
    await expect(modal).toBeVisible();

    // 1. Template Layout Engine section
    await expect(modal.getByText('1. Base Template')).toBeVisible();

    // 2. Color Palette section & swatches
    await expect(modal.getByText('2. Color Palette')).toBeVisible();
    await expect(modal.getByText('Sapphire Tech')).toBeVisible();
    await expect(modal.getByText('Emerald Enterprise')).toBeVisible();
    await expect(modal.getByText('Royal Indigo')).toBeVisible();
    await expect(modal.getByText('Executive Slate')).toBeVisible();

    // 3. Typography & Spacing sections
    await expect(modal.getByText('3. Typography')).toBeVisible();
    await expect(modal.getByText('4. Layout Density & Header')).toBeVisible();

    // 4. Density buttons
    await expect(modal.getByRole('button', { name: 'Compact', exact: true })).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Standard', exact: true })).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Spacious', exact: true })).toBeVisible();

    // 5. Section Visibility & Ordering
    await expect(modal.getByText('5. Section Visibility')).toBeVisible();

    // 6. Live Preview Iframe inside modal
    const modalIframe = modal.locator('iframe[title="Live Template Preview"]');
    await expect(modalIframe).toBeVisible();

    // 7. Footer buttons
    await expect(modal.getByRole('button', { name: /Reset to Defaults/ })).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Cancel' })).toBeVisible();
    await expect(modal.getByRole('button', { name: /Save & Apply Template/ })).toBeVisible();

    // Close modal
    await modal.getByRole('button', { name: 'Cancel' }).click();
    await expect(modal).not.toBeVisible();
  });

  test('Component: SettingsDrawerComponent - AI Provider selection and temperature control', async ({ page }) => {
    // Open Settings Drawer
    await page.locator('header button').filter({ hasText: /⚙️/ }).click();

    // Verify drawer elements
    await expect(page.getByText('AI Engine & Model Settings')).toBeVisible();
    await expect(page.getByText('Execution Provider')).toBeVisible();

    // Verify provider options
    const select = page.locator('select').filter({ hasText: /Auto/ });
    await expect(select).toBeVisible();

    // Temperature slider and value
    await expect(page.getByText('Generation Temperature')).toBeVisible();
    const rangeSlider = page.locator('input[type="range"]');
    await expect(rangeSlider).toBeVisible();

    // Save button
    const saveBtn = page.getByRole('button', { name: 'Save Configuration' });
    await expect(saveBtn).toBeVisible();

    // Close drawer via header close button
    const closeBtn = page.locator('button').filter({ hasText: '✕' }).first();
    await closeBtn.click();
    await expect(page.getByText('AI Engine & Model Settings')).not.toBeVisible();
  });

  test('Component: GitDiffViewerComponent - statistics and diff modes', async ({ page }) => {
    // Switch to Text Diff view mode
    await page.getByRole('button', { name: /Text Diff/ }).click();

    const diffViewer = page.locator('app-git-diff-viewer');
    await expect(diffViewer).toBeVisible();

    // 1. Branch comparison bar
    await expect(diffViewer.getByText('compare:')).toBeVisible();
    await expect(diffViewer.getByText('base/ground-truth')).toBeVisible();

    // 2. Additions and deletions badges in the top bar
    await expect(diffViewer.locator('.diff-top-bar').getByText(/\+\d+/)).toBeVisible();
    await expect(diffViewer.locator('.diff-top-bar').getByText(/-\d+/)).toBeVisible();

    // 3. Unified and Split mode buttons
    const unifiedBtn = diffViewer.getByRole('button', { name: 'Unified' });
    const splitBtn = diffViewer.getByRole('button', { name: 'Split' });
    await expect(unifiedBtn).toBeVisible();
    await expect(splitBtn).toBeVisible();

    // Switch between diff modes
    await splitBtn.click();
    await unifiedBtn.click();

    // Switch back to Single View
    await page.getByRole('button', { name: /Single View/ }).click();
  });
});
