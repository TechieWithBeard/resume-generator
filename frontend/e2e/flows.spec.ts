import { test, expect } from '@playwright/test';

test.describe('Resume Architect - End-to-End User Flows', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to root application
    await page.goto('/');
    // Wait for Angular app and base resume to initialize
    await expect(page.locator('app-header')).toBeVisible({ timeout: 15000 });
  });

  test('Flow 1: App Initialization and Ground Truth Verification', async ({ page }) => {
    // Check header branding and ATS badge
    await expect(page.getByRole('heading', { name: 'Resume Architect' })).toBeVisible();
    await expect(page.locator('app-badge').filter({ hasText: 'ATS Engine' })).toBeVisible();

    // Check Ground Truth status in header
    const headerGroundTruthBtn = page.locator('header button').filter({ hasText: 'Source of Truth' });
    await expect(headerGroundTruthBtn).toBeVisible();
    await expect(headerGroundTruthBtn).toContainText('Alex Mercer');

    // Check Source of Truth card in Job Input
    const truthCard = page.locator('div').filter({ hasText: 'Source of Truth' }).first();
    await expect(truthCard).toBeVisible();
    await expect(page.getByText('✓ Loaded & Grounded')).toBeVisible();
    await expect(page.getByText(/Alex Mercer • \d+ verified roles/)).toBeVisible();

    // Check preview iframe has rendered
    const previewIframe = page.frameLocator('iframe[title="Resume Live Preview"]');
    await expect(previewIframe.locator('body')).toBeVisible({ timeout: 10000 });
    await expect(previewIframe.getByText('Alex Mercer')).toBeVisible();
  });

  test('Flow 2: Ground Truth Modal - Inspect, Tab Navigation, and Save', async ({ page }) => {
    // Open Ground Truth modal via header button
    await page.locator('header button').filter({ hasText: 'Source of Truth' }).click();

    // Verify modal is displayed
    const modal = page.locator('app-base-resume-modal app-modal');
    await expect(modal).toBeVisible();
    await expect(modal.getByText('Candidate Ground Truth (Source of Truth)')).toBeVisible();
    await expect(modal.getByText('Ground Truth Invariant:')).toBeVisible();

    // Verify form fields
    const nameInput = modal.locator('input[type="text"]').first();
    await expect(nameInput).toHaveValue('Alex Mercer');

    // Test tab navigation: Structured Profile -> Raw Knowledge Base -> JSON Schema
    await modal.getByRole('button', { name: /Raw Knowledge Base/ }).click();
    await expect(modal.locator('textarea')).toBeVisible();

    await modal.getByRole('button', { name: /JSON Schema/ }).click();
    await expect(modal.locator('textarea')).toBeVisible();

    // Switch back to Structured Profile
    await modal.getByRole('button', { name: /Structured Profile/ }).click();
    await expect(modal.getByText('Candidate Identification')).toBeVisible();

    // Close modal via Cancel button
    await modal.getByRole('button', { name: 'Cancel' }).click();
    await expect(modal).not.toBeVisible();
  });

  test('Flow 3: Document Paradigm Switcher (Resume vs Custom CV)', async ({ page }) => {
    // Initially on Targeted Resume mode
    const resumeModeBtn = page.getByRole('button', { name: /Targeted Resume/ }).first();
    const cvModeBtn = page.getByRole('button', { name: /Custom CV/ }).first();

    await expect(resumeModeBtn).toBeVisible();
    await expect(cvModeBtn).toBeVisible();

    // Switch to Custom CV
    await cvModeBtn.click();
    await expect(page.locator('span').filter({ hasText: 'Executive CV' }).first()).toBeVisible();
    await expect(page.getByText('Bespoke executive CV with company research')).toBeVisible();

    // Switch back to Targeted Resume
    await resumeModeBtn.click();
    await expect(page.locator('span').filter({ hasText: 'Targeted Resume' }).first()).toBeVisible();
    await expect(page.getByText('Condensed 1–2 page ATS profile')).toBeVisible();
  });

  test('Flow 4: Job Input Tabs & Preflight HITL Role Mismatch Detection', async ({ page }) => {
    // Test tab switching: Paste Job Content vs LinkedIn Job URL
    const linkedinTab = page.getByRole('button', { name: /LinkedIn Job URL/ });
    const pasteTab = page.getByRole('button', { name: /Paste Job Content/ });

    await linkedinTab.click();
    await expect(page.locator('#linkedinUrl')).toBeVisible();
    await expect(page.getByRole('button', { name: /Extract/ })).toBeDisabled();

    // Switch back to Paste Job Content
    await pasteTab.click();
    const jdTextarea = page.locator('#jobDesc');
    await expect(jdTextarea).toBeVisible();

    // Type a role with severe mismatch (embedded firmware / hardware kernel)
    const mismatchedJD = `
      Embedded Systems Kernel Engineer:
      Required Qualifications:
      - 5+ years writing low-level bare-metal firmware in C and Assembly
      - Experience with RTOS internals, FPGA synthesis, Verilog, and VHDL
      - Device drivers for PCIe, I2C, SPI, and microcontroller peripheral registers
      - Hardware board bring-up, oscilloscope signal debugging, and JTAG flashing
    `;
    await jdTextarea.fill(mismatchedJD);
    await page.locator('#targetTitle').fill('Embedded Firmware Engineer');

    // Generate button is now enabled
    const generateBtn = page.locator('app-job-input button').filter({ hasText: /Generate/ });
    await expect(generateBtn).toBeEnabled();
    await generateBtn.click();

    // Expect Preflight HITL modal to appear
    const mismatchModal = page.locator('div[role="dialog"]').filter({ hasText: 'Role Competency Gap Detected' });
    await expect(mismatchModal).toBeVisible({ timeout: 15000 });

    // Verify modal elements
    await expect(mismatchModal.getByText(/Match/)).toBeVisible();
    await expect(mismatchModal.getByText('Strict Zero-Fabrication Invariant')).toBeVisible();
    await expect(mismatchModal.getByText('Pivot & Transferable Engineering Strengths')).toBeVisible();
    await expect(mismatchModal.getByText('Strict Factual Grounding')).toBeVisible();

    // Select Strict Factual Grounding strategy
    await mismatchModal.locator('#stratStrict').click();
    await expect(mismatchModal.locator('#stratStrict')).toBeChecked();

    // Enter guidance notes
    const notesInput = mismatchModal.locator('#candidateNotes');
    await notesInput.fill('Focus on scalable distributed systems and performance profiling.');
    await expect(notesInput).toHaveValue('Focus on scalable distributed systems and performance profiling.');

    // Cancel / Revise Job Requirements button closes dialog
    await mismatchModal.getByRole('button', { name: 'Revise Job Requirements' }).click();
    await expect(mismatchModal).not.toBeVisible();
  });

  test('Flow 5: End-to-End Resume Generation with Real-Time Streaming', async ({ page }) => {
    // Fill relevant Frontend / Full-Stack Job Description
    const targetJD = `
      Senior Staff Frontend Engineer (Web Applications):
      We are looking for an experienced Senior Frontend Engineer to architect performant web applications.
      Key Responsibilities:
      - Design scalable web architecture using modern TypeScript, Angular, and React
      - Optimize client-side bundle size, Core Web Vitals (LCP, INP), and state synchronization
      - Establish robust unit, component, and end-to-end automated testing pipelines
      - Collaborate with product designers and backend engineers on RESTful and streaming APIs
    `;
    const jdTextarea = page.locator('#jobDesc');
    await jdTextarea.fill(targetJD);

    // Provide optional target role title
    const titleInput = page.locator('#targetTitle');
    await titleInput.fill('Senior Staff Frontend Engineer');

    // Trigger generation
    const generateBtn = page.locator('app-job-input button').filter({ hasText: /Generate/ });
    await generateBtn.click();

    // Verify Stream Console displays active steps
    const streamConsole = page.locator('app-stream-console');
    await expect(streamConsole).toBeVisible();

    // Check pipeline steps are present
    await expect(streamConsole.getByText('Job Analysis')).toBeVisible();
    await expect(streamConsole.getByText('Truth Audit')).toBeVisible();
    await expect(streamConsole.getByText('Synthesis')).toBeVisible();
    await expect(streamConsole.getByText('Guardrail')).toBeVisible();

    // Wait for generation to complete (heuristic fallback completes in < 5s)
    await expect(generateBtn).not.toContainText('Streaming Real-Time', { timeout: 30000 });

    // Verify preview iframe contains updated tailored resume
    const previewIframe = page.frameLocator('iframe[title="Resume Live Preview"]');
    await expect(previewIframe.locator('body')).toBeVisible();
    await expect(previewIframe.getByText('Alex Mercer')).toBeVisible();
  });

  test('Flow 6: View Mode Switcher (Single, Split Comparison, and Git Diff)', async ({ page }) => {
    // Click 'Compare with Base'
    await page.getByRole('button', { name: /Compare with Base/ }).click();

    // Verify side-by-side view renders both iframes
    await expect(page.getByText('Profile Comparison:')).toBeVisible();
    await expect(page.getByText('Base Profile (Original)', { exact: true })).toBeVisible();
    await expect(page.getByText('Tailored Application', { exact: true })).toBeVisible();

    const baseIframe = page.frameLocator('iframe[title="Base Resume Source of Truth"]');
    await expect(baseIframe.locator('body')).toBeVisible();
    await expect(baseIframe.getByText('Alex Mercer')).toBeVisible();

    // Click 'Text Diff'
    await page.getByRole('button', { name: /Text Diff/ }).click();

    // Verify Git Diff Viewer is mounted
    const diffViewer = page.locator('app-git-diff-viewer');
    await expect(diffViewer).toBeVisible();
    await expect(diffViewer.getByText('compare:')).toBeVisible();
    await expect(diffViewer.getByText('base/ground-truth')).toBeVisible();

    // Switch back to 'Single View'
    await page.getByRole('button', { name: /Single View/ }).click();
    await expect(page.frameLocator('iframe[title="Resume Live Preview"]').locator('body')).toBeVisible();
  });

  test('Flow 7: Template Studio & Style Customizer Modal', async ({ page }) => {
    // Open Template Studio
    await page.getByRole('button', { name: /Styling/ }).click();

    const studioModal = page.locator('app-template-config-modal app-modal');
    await expect(studioModal).toBeVisible();

    // Check color palettes
    await expect(studioModal.getByText('2. Color Palette')).toBeVisible();
    await expect(studioModal.getByText('Sapphire Tech')).toBeVisible();
    await expect(studioModal.getByText('Emerald Enterprise')).toBeVisible();

    // Select Emerald Enterprise palette
    await studioModal.getByRole('button', { name: 'Emerald Enterprise' }).click();

    // Select Compact Classic template
    await studioModal.getByRole('button', { name: /Compact Classic/ }).click();

    // Save and apply template
    await studioModal.getByRole('button', { name: /Save & Apply Template/ }).click();
    await expect(studioModal).not.toBeVisible();

    // Template selector reflects selection
    const templateSelect = page.locator('select').first();
    await expect(templateSelect).toHaveValue('compact');
  });

  test('Flow 8: Keyword Highlight Toggle and Zoom Controls', async ({ page }) => {
    // Highlight Keywords toggle
    const highlightBtn = page.getByRole('button', { name: /Highlight/ });
    await expect(highlightBtn).toBeVisible();
    await highlightBtn.click();
    await expect(page.getByRole('button', { name: 'Keywords Highlighted' })).toBeVisible();

    // Zoom Controls: Zoom In (+)
    const zoomInBtn = page.getByRole('button', { name: '+', exact: true });
    const zoomResetBtn = page.getByTitle('Reset zoom to 100%');

    await expect(zoomResetBtn).toHaveText('100%');
    await zoomInBtn.click();
    await expect(zoomResetBtn).toHaveText('110%');

    // Zoom Out (-)
    const zoomOutBtn = page.getByRole('button', { name: '−', exact: true });
    await zoomOutBtn.click();
    await expect(zoomResetBtn).toHaveText('100%');
  });

  test('Flow 9: AI Settings Drawer Configuration', async ({ page }) => {
    // Click Settings button in Header
    const settingsBtn = page.locator('header button').filter({ hasText: /⚙️/ });
    await settingsBtn.click();

    // Drawer opens
    const drawer = page.locator('div').filter({ hasText: 'AI Engine & Model Settings' }).first();
    await expect(drawer).toBeVisible();

    // Change provider to High-Precision Deterministic Engine (Zero Keys)
    const providerSelect = page.locator('select').filter({ hasText: /Auto/ });
    await providerSelect.selectOption('heuristic');

    // Save Configuration
    await page.getByRole('button', { name: 'Save Configuration' }).click();
    await expect(page.getByText('AI Engine & Model Settings')).not.toBeVisible();

    // Verify header button displays updated provider
    await expect(settingsBtn).toContainText(/heuristic/i);
  });

  test('Flow 10: 9-Dimension Resume Score Checker API Response Verification', async ({ request }) => {
    // Validate score checker endpoint directly via Playwright API testing
    const response = await request.get('/api/resume/score');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('overall_score');
    expect(data.overall_score).toBeGreaterThanOrEqual(0);
    expect(data.overall_score).toBeLessThanOrEqual(100);

    // Verify each of the 9 required dimensions
    const dimensions = data.dimensions || {};
    const requiredDims = [
      'contact_information',
      'summary_statement',
      'word_choice',
      'measurable_results',
      'formatting',
      'optimal_length',
      'spelling_and_grammar',
      'comprehensiveness',
      'customization',
    ];

    for (const dim of requiredDims) {
      expect(dimensions, `Missing dimension: ${dim}`).toHaveProperty(dim);
      expect(dimensions[dim]).toHaveProperty('score');
      expect(dimensions[dim]).toHaveProperty('passed');
      expect(dimensions[dim]).toHaveProperty('feedback');
    }
  });
});
