# Architecture

`parsing → Study/Document/Block → provider → Extraction → verification → ProjectStore → review/export`

- `parsing.py` uses pypdf locally. A document ID derives from SHA-256; each block is one complete PDF page. Empty or failed pages are reported, never renumbered.
- `models.py` defines strict Pydantic models. A Project has studies, field definitions, provider/model, runs, experiments, and revision history. A Study owns its main paper and supplements.
- `providers.py` uses fixed official HTTPS endpoints. OpenAI uses Responses `text.format`; Anthropic uses Messages `output_config.format`. No tools, code execution, document instruction following, or arbitrary endpoints are enabled. Model IDs are user-configured. Payloads are checked against the shared schema, then locally validated.
- Extraction sends all successfully parsed pages of a single study in one request to preserve main/supplement context. Studies over 160,000 characters are rejected before transmission. Automatic chunk merging and automatic retry are deliberately not implemented in v0.1.
- `verification.py` resolves model-supplied block IDs against that study only. Document names and page numbers come from the local index. Unicode and whitespace normalization are allowed; values are not fuzzily matched. Location checks do not establish scientific entailment.
- `pipeline.py` atomically checkpoints before and after each study. Completed studies are skipped during resume. A failed study is not partially accepted. Error bodies and keys are not stored.
- `storage.py` stores one schema-versioned JSON snapshot per project using a temporary file and atomic replace. It includes source text and audit history. The UI is single-user; concurrent writes to the same project are not supported.
- `exporting.py` writes long-form CSV and five-sheet Excel. Formula-like spreadsheet values are neutralized. JSON preserves the complete canonical record.
- `demo.py` only returns recorded results when imported file hashes match the distributed synthetic fixtures. It cannot silently generate fake results for arbitrary PDFs.

## Evidence and revision semantics

`original` is the unmodified model field; `sources` contains program-resolved origin and location status. Each revision appends current value/unit, selected evidence, reviewer, note, and timestamp. Exports present original and effective values separately. `verified` is an explicit human decision requiring a nonempty value and located source; it is never set by the model.

The UI selects project objects by stable IDs before mutation, so edits apply to the canonical project rather than a widget's copied object.

## API references

- https://developers.openai.com/api/docs/guides/structured-outputs
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs

Native Claude citations are not combined with strict JSON outputs. Both providers return source block references and quotations inside the application schema, which are checked locally.

