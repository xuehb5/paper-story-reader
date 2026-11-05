# Shared reader generator and input contract

The Agent interprets sources and authors the explanation. Python checks records and files, then renders the same story map, argument graph and single-paper canvas in either language. It does not infer scientific meaning, select figures or call a model.

## Build and verify

```bash
python scripts/validate_evidence.py reader-input.json --init evidence-review.pending.json
# Complete actual source review; initialization alone does not pass.
python scripts/validate_evidence.py reader-input.json --review evidence-review.json --output evidence-checks.json
python scripts/validate_release.py reader-input.json --review evidence-review.json --context context-audit.json --output release-checks.json
python scripts/render_reader.py reader-input.json --review evidence-review.json --context-audit context-audit.json --output reader
python scripts/verify_delivery.py reader/PAPER-ID.html reader/PAPER-ID.md --language en --manifest reader/delivery-manifest.json
```

Use a fresh empty output directory. Final output includes HTML, Markdown, both graph JSON files, copied sources/assets, a build report and a frozen delivery manifest. Do not hand-edit final files; revise input and re-review changed meaning before rebuilding. `--draft` is an explicitly unreviewed preview and visibly marked as such.

Default output embeds images in the reader HTML. For static web hosting, add `--link-assets`: the **same** renderer uses relative local image files so the map and canvas start before large image downloads. Publish or download the whole directory together. No third-party CDN, account, Node runtime or model API is required to open a finished reader. Python 3.10+ is needed to generate it; PDF text checks use `pypdf`. Use available image/PDF tools for visual inspection.

## Top-level input

`reader-input.json` has `case`, `assets`, `sources` and optional `navigation`. Paths resolve relative to this input file. Use portable relative paths, not author-specific workstation paths. Case, section, figure and walkthrough IDs start with an ASCII letter and contain only letters, digits, `_` or `-`.

Set **`case.language: "en"`** for English output. This controls UI labels, graph word wrapping and language-aware checks; it does not translate authored scientific text. Write the content in English directly. An explicit setting travels safely between the English and Chinese packages; their edition default applies only when it is omitted. Supported language families are `en` and `zh`.

`case` needs nonempty strings `id`, `short`, `title`, `category`, `paper_title`, `doi`, `citation`, `thesis`, `audience`, `coverage`; `source_ids` matching source keys; `sections`; `figures`; and an authored `research_graph` or an explicit `omit_research_graph_reason`. Use original paper metadata and clear actual coverage, including what was not read or independently checked.

## Sections and nearby explanations

Each section has `id`, `title`, `refs` (original figures/pages/anchors) and `blocks`. A block can be:

```json
"A continuous explanatory paragraph."
{"figure":"figure-id"}
{"figure_row":["figure-a","figure-b"]}
{"detail":{"title":"A concrete reader question","kind":"figure-reading","side":"left","paragraphs":["A substantial explanation."],"figure":"figure-id"}}
{"walkthrough":{"id":"step-id","title":"What should we compare?","figure":"figure-id","lead":"Identify the samples and paired symbols first.","paragraphs":["The actual observation and its bounded meaning."]}}
```

The snippets illustrate individual block forms, not a complete valid input. `detail.kind` can be `si` for supporting-information evidence, and `side` can be `left` or `right`. A detail can use `figures` for multiple images and `blocks` containing walkthrough objects. Main-story observations and necessary SI must remain in the trunk. A branch needs genuine local teaching, not just a caution.

Each figure occurrence has its own ID. If the same source image is used twice, use two occurrence IDs pointing to the same file. Every declared figure must be used once in the block structure. Walkthrough IDs must be unique. Paragraph targets are generated from consecutive prose strings in a section, e.g. `design-p2`; figure blocks do not increment that counter.

## Figures, composites and sources

`case.figures[figure-id]` requires `label`, `title`, `role`, `caption`, all authored in the requested reading language except original figure identifiers. Optional `parent` points to a complete composite ID. Define that composite in `case.composites[parent]` with `label` and `title`, and supply its actual asset too. Local and complete images must belong to the same source/page. Do not fabricate an extra composite layer for an already complete figure.

`assets[id]` requires `source`, `page`, `locator`, `image`, `page_image`, `width`, `height`, `sha256`, `page_sha256`. `image` is the actual figure/crop; `page_image` is the complete PDF page or original complete JATS figure. Hash the actual files. Keep axes, legends, scale bars and paired comparisons where needed; validators do not decide whether a crop is scientifically reasonable.

`sources[source-id]` requires `file`, `sha256`, `format` (`pdf` or `jats`) and a truthful English `description`; PDFs also need `pages`. Match the supplied paper and its own SI. Asset `page` is a physical page integer for PDF, an actual source anchor string for JATS. For JATS use:

```json
{"full_view_label":"View complete original figure","full_view_description":"Complete original image"}
```

Do not invent PDF pages for JATS. English source-location labels are part of the authored metadata and must also be English. Preserve original English quotations, sample IDs, units and figure numbering. “SI downloaded” does not mean all pages or peaks were independently reviewed.

## Scientific argument graph

`case.research_graph.nodes` use `id`, `title`, `role`, `target`, `finding`, `row`, `column`, optional `figure_note`, and `claim_id`. In a final reader, `claim_id` points to the evidence ledger and `finding` exactly matches its canonical `statement`. Titles need separate semantic review. Use a concise English question/judgment that fits at most three wrapped lines of about 21 characters; keep detailed wording in `finding`. Do not abbreviate away scientific meaning to fit the card.

`target` is a real prose paragraph ID. `row` starts at 0; `column` is `left`, `right` or `center`. A row can have left/right nodes or one center node, not overlapping positions. Spatial position does not indicate evidence strength. `role` briefly states the argumentative use and `figure_note` retains a short original figure reference.

Edges use `from`, `to`, `label` and `kind`. Author a meaningful relationship such as “tests the chemical response,” “provides complementary evidence” or “limits the scope.” `kind: "interpretation"` renders a dashed line for a proposed explanation or next question. A next-test link is not already supporting evidence. Do not mechanically connect every reading stage as a causal sequence. If evidence cannot support a graph, disclose the reason instead of inventing links or silently removing the feature.

## Multiple papers and source indexing

Optional `navigation` has `home` and `papers` entries with `id`, `short`, `href`; include the current paper. Links are relative to the generated HTML and must point to actual generated readers. The caller supplies a real collection entry page; do not invent missing readers. Without this object, the single-paper index opens the reader directly.

`scripts/index_source.py article.xml --id PAPER-main --output work/index` creates traceable text and source metadata. Run separately for SI. PDF indexing requires `pypdf`; optional PDF page rendering uses available tools such as `pypdfium2`. JATS uses source anchors. Indexing assists retrieval and does not replace looking at the actual figures.
