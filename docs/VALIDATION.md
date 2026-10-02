# Validation status

## v0.3.0 — unreleased

The planning modules are removed from the interface. The suite is now 46 tests (was 50): tests for removed goal, task, note and module-layout features were dropped, and new ones check that the app opens on literature evidence without planning navigation, and that 0.2 goals, tasks and notes load, survive appearance and language saves, and are written back unchanged. The evidence, provider, export and packaging tests are unchanged and pass. Ruff passes. These were run locally on Linux with Python 3.11; the Windows/Python 3.13 CI matrix has not run on this change yet.

## v0.2.0 — 2026-09-26

Local automated tests cover:

- Separate experimental conditions and pollutant/TOC endpoints, supplement provenance, fabricated quotes, missing units and human revision history.
- Mocked OpenAI/Anthropic HTTP contracts, refusal/truncation handling and interruption recovery. No live API key was used.
- Learning-step progress and edits; dated-task completion, reopening, overdue and archive rules; note editing, pinning, colors, archive and restore.
- Atomic workspace save, simulated write failure, corrupt-file preservation, restart persistence and idempotent demo seeding.
- English/Chinese switching, captured widget-label language, module visibility/order/reset, palette persistence and color contrast.
- Source-package exclusions and spreadsheet formula injection protection.

Browser acceptance uses 1440px desktop and 390px narrow viewports, English and Chinese, all four presets and a dark custom-background stress check. Published screenshots are captured from the running app with synthetic records.

CI runs Ruff, pytest, the offline CLI demo and package builds on Windows/Linux with Python 3.11/3.13. See the repository Actions page for the result of each exact commit; configured CI is not itself proof of a successful run.

## Not yet verified

Live model extraction, scientific accuracy on real papers, independent colleague installation, OCR, complex table reconstruction and multi-user editing. Automated source matching does not validate scientific interpretation. The software does not claim official OpenAI or Anthropic endorsement.
