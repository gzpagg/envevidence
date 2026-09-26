# Validation status

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
