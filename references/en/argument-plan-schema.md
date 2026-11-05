# Optional argument-plan handoff

Use this only when a separate reasoning-design handoff is helpful. It does not replace the evidence ledger or context audit, and a short focused question need not create one.

Source text lines use `<source>-P001-L001<TAB>original text`. PDF pages are physical pages. For JATS, a logical text page convention may be used internally if `sources.description` states it; never present that convention as a real PDF page.

Top-level fields: `central_question`; `contribution` with `prior_limit`, `new_move`, `bounded_claim`; `entity_states` entries with `object` and `states`; unique ordered section IDs in `reading_route`; and `sources` keyed by source ID with `text_file` relative to the plan, `format` and `description`.

Each `argument_nodes` entry needs `id`, `question`, `claim`, `test_or_comparison`, `what_it_does_not_establish`, `remaining_question`; `inference_level` from `observation`, `design_rationale`, `author_interpretation`, `model_result`, `synthesis`; `story_sections` referencing the route; and `evidence` entries with `source`, integer `page`, `anchor_start`, `anchor_end`, `excerpt`. The excerpt must occur contiguously within actual same-page source anchors in valid order.

`transitions` must follow adjacent route pairs and record `from`, `to`, `resolved`, `still_unknown`, `why_next`. `reader_checks` contains at least two actual questions with `question`, `expected_answer` and valid `argument_ids`.

```bash
python scripts/validate_argument_plan.py argument-plan.json --output argument-checks.json
```

This checks fields, target references and source excerpts, not evidential strength, causal validity or reader understanding.
