# Context audit and final-delivery gate

This JSON is an internal record. It does not constitute a second reading companion or certify that software understood the science.

## Workflow

Record real groups, individual conditions, object/state, preparation/measurement stage, panel identity and metrics before writing the story. After drafting, reopen sources for all key claims. Save genuine findings and reader-visible revisions. Independent review must actually be independent; otherwise report `same_agent_second_pass`.

```bash
python scripts/validate_release.py reader-input.json --review evidence-review.json --init context-audit.pending.json
python scripts/validate_evidence.py reader-input.json --review evidence-review.json --output evidence-checks.json
python scripts/validate_release.py reader-input.json --review evidence-review.json --context context-audit.json --output release-checks.json
python scripts/render_reader.py reader-input.json --review evidence-review.json --context-audit context-audit.json --output reader
python scripts/verify_delivery.py reader/PAPER-ID.html reader/PAPER-ID.md --language en --manifest reader/delivery-manifest.json
```

Replace `PAPER-ID` with the actual `case.id`. `--init` only creates a pending inventory. A final build requires completed evidence and context records. Revise source-grounded wording, not just hashes or evidence levels, when blocked. Write a new empty output directory for each revision; never silently patch final HTML/Markdown.

## `context-audit.json`

Use `schema_version: 1`, `input_sha256` and `review_sha256` bound to the exact current files, plus these records:

- `comparisons`: each has `id`, `pointers`, at least two `groups` with `label` and a `conditions` object, `classification` (`controlled`, `multi_condition`, `descriptive`) and `source_claim_ids`. Use the same real condition keys across groups and values with units. Do not hide several changes inside a single “formulation” field. More than one differing key cannot be `controlled`; unknown conditions cannot certify control. A multi-condition comparison needs `qualification: {pointer, quote}` quoting an exact current reader-visible limitation. Internal acknowledgment does not excuse prose claiming an “only difference” or a single-variable cause. If the paper truly has no comparison, give a specific `no_comparisons_reason` of at least 30 characters.
- `scopes`: each has `claim_id`, the actual `stage`, and `visible_scope: {pointer, quote}`. Keep a terminal crosslinking advantage separate from precursor synthesis, pretreatment and measurement. Put the qualification beside the relevant reader-visible claim.
- `panels`: cover every displayed figure with `asset`, actual `panel`, `subject_state`, `metrics` (array; empty for a nonquantitative scheme), `conditions`, `source_locator` and explanatory `pointers`. Use separate records where panel metrics or identities differ. A G′-only panel cannot be described as measuring G′ and G″; a dry SEM image cannot directly reveal a hydrated network or identify a specific bond topology. Magnify unclear labels and narrow unresolved claims.
- `source_first_review`: `method` (`independent_agent` or `same_agent_second_pass`), all `checked_claim_ids`, a substantive `summary` of at least 30 characters and actual `findings`. A finding has `id`, `issue`, `resolution` (`revised` or `retained_qualified`), `visible_resolution: {pointer, quote}` and `evidence_claim_ids`. Unresolved findings block final output. Do not invent findings to fill a quota.
- Optional `waivers`: for a demonstrated lexical false positive only, record `pointer`, current `text_sha256`, `source_claim_id` and a specific `source_reason` of at least 30 characters. A waiver does not establish scientific truth. Do not bulk-waive errors or turn author interpretation into observation to pass a gate.

Pointers refer to the evidence ledger's visible units. Thesis, titles, captions, branches, graph findings and arrows need the same scientific discipline as body paragraphs. Indirect spectroscopy, microscopy or a bulk modulus does not automatically identify every covalent linkage or exclude every alternative mechanism. Preserve a real source inconsistency rather than deciding a unique answer without evidence.

## English checks and limits

The renderer supports `case.language: "en"`. The English distribution also defaults to English when the field is omitted; explicit language is recommended for portable input. Lexical checks include English proof/exclusion wording, isolated-variable descriptions, some stage expansion, indirect-measurement claims and negation. These rules have omissions and false positives: passing is not a scientific-semantic certification. Quote and hash verification are language-independent.

If necessary sources are missing, deliver an honest materials-gap note or an explicitly limited draft. Do not fabricate review records. Save UTF-8, read the resulting files back and check key conditions and requests; an existing file or parseable JSON is not proof that prose survived encoding.
