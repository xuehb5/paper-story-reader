# Internal evidence ledger

The reader does not need to fill in or read this file. Generate a pending inventory only after drafting stable content:

```bash
python scripts/validate_evidence.py reader-input.json --init evidence-review.pending.json
python scripts/validate_evidence.py reader-input.json --review evidence-review.json --output evidence-checks.json
```

Initialization does not pass review. Use a fresh pending filename to preserve earlier records. An unresolved preview requires `--draft`; changed prose needs source rechecking, not just new hashes.

## Source-first process

Before drafting decisive claims, inspect the original passages and figures and record object/state, conditions, metrics and the basis for comparison. After drafting, reopen those sources without presuming the draft is right. Review all key claims, not just numbers or a small sample. Source truth takes priority over a smooth narrative. Narrow or remove unsupported transitions and disclose genuine unresolved contradictions. Do not infer unseen visual details from captions.

## Top-level fields

Use `schema_version: 1`, `input_sha256` for the exact input bytes, `claims`, `units` and `reviewer`. The latter contains `method` (`independent_agent` or `same_agent_second_pass`), `identity`, `source_first_summary` describing the actual scope/method, and `unresolved_items` (objects with `issue` and `disclosure_unit`). A nonempty `pending_checks` blocks final output. A disclosed unresolved issue in the source differs from an unfinished check. Method and identity fields are records, not independent identity verification.

## Claims

Each canonical claim requires:

- A unique `id` and a condition-preserving `statement`.
- `level`: `observation`, `derived`, `model_result`, `author_interpretation`, `author_claim`, `background` or `synthesis`.
- Nonempty `subject`, `conditions`, `scope`, `support` and `limit`. Identify the actual object/state, experimental/model conditions, tested range, reason for support and stronger inference not established.
- An `evidence` array with actual source text and/or viewed images sufficient for the claim.

Text evidence uses `kind: "text"`, `source`, `locator` and a **contiguous original-language** `quote`. PDFs also require a 1-based physical `page`; do not assign PDF pages to JATS. The checker matches normalized quotations to the original file/page. If an equation or quotation cannot be reliably extracted, use actual page-image evidence rather than inventing a quote.

Figure evidence uses `kind: "figure"`, `asset`, `panels`, `axes`, `legend`, `conditions` and `observation`. State what was actually viewed, including exceptions; a scheme may state that it has no quantitative axes. Assets must belong to current sources and pass file/hash checks. Every displayed image needs an actual-view record; repeated use of the same image hash may reuse that record. Do not label a caption-based guess as an actual visual inspection.

## Reader-visible units

The initializer enumerates JSON Pointer locations and `text_sha256` for scientific titles, thesis, trunk, branches, walkthroughs, captions, graph roles/findings/arrows and coverage. For each unit supply:

- `kind: "factual"`, supporting `claim_ids`, `verdict: "aligned"` or `"qualified"`, and a specific comparison `reason`. Link every scientific subclaim, using multiple claims when necessary. `pending` and `needs_revision` block final output.
- Use `kind: "navigation"`, empty `claim_ids`, `verdict: "aligned"` only for a genuinely non-scientific reading action. Explain why it asserts no scientific fact. A short question or title can still contain a scientific assertion.
- An unresolved source disagreement must be disclosed in a corresponding `qualified` unit, linked to the relevant evidence and listed in `reviewer.unresolved_items`.

Each `research_graph` node needs `claim_id`; its `finding` must **exactly equal** that claim's `statement`. Review the title separately. Review edge meaning, direction and evidence level too: two valid nodes do not automatically establish their connection.

The ledger does not prescribe a fixed count of claims, nodes or quotes. One generic abstract quote cannot meaningfully support every sentence. No extra audit website is required: the reading companion remains the default reader entry, with source checking available on demand.
