# Source-linked tables, equations and quotations

The existing figure, walkthrough and detail blocks remain valid. A section or `detail.blocks` may additionally contain one `table`, `equation` or `quotation` object. Give every rich block a globally unique safe `id`, original `label`, explanatory `title`, actual `source` ID and `locator`. PDF evidence also needs a 1-based physical `page`; non-PDF evidence must not invent a PDF page. The source is included locally with a checked hash. All visible cell text, expressions, definitions, titles and explanations enter the source-review inventory.

```json
{"table":{"id":"result-table","label":"Table 2 (selected rows)","title":"Compare the actual configurations","source":"paper-main","page":6,"locator":"physical p. 6, Table 2","columns":["Method","Metric (higher is better)"],"rows":[["Actual source row","Actual source value"]],"caption":"State the actual dataset, split, configuration and row-selection scope."}}
```

The snippet is a schema illustration, not source-backed numerical evidence. A selective table is labeled selective. Preserve units, uncertainty, metric direction and meaningful footnotes. Do not silently combine separate tasks or reconstruct precision from an image. The original-source link opens the source PDF at the declared physical page. Original table images may also be retained through ordinary figure blocks when visual inspection benefits the reader.

```json
{"equation":{"id":"update-rule","label":"Eq. 3","title":"Explain what the update changes","source":"paper-main","page":4,"locator":"physical p. 4, Eq. 3","expression":"h = W₀x + BAx","variables":[{"symbol":"W₀","meaning":"Frozen pretrained weight matrix."},{"symbol":"BA","meaning":"The factored weight update; use the paper's actual dimensions and scaling."},{"symbol":"x, h","meaning":"Input and output of the described operation."}],"explanation":"Connect this expression to the current research question, preserving assumptions and scale conventions."}}
```

`expression` is always required as a readable/accessible text alternative. Optional `mathml` is a complete `<math>` element using only the whitelisted presentation elements and attributes; scripts, links, styling, foreign elements and declarations are rejected. Verify rendered symbols against the original. A representation of an equation does not validate its derivation.

```json
{"quotation":{"id":"key-passage","label":"Original passage","title":"Read this claim in its source context","source":"paper-main","page":3,"locator":"physical p. 3, second paragraph","text":"Exact original source wording.","explanation":"Explain its argumentative role without changing its scope."}}
```

Quotation text must exactly match a source-checked `kind: "text"` evidence record for the same source and page. Keep copyrighted quotations brief and respect source permissions. Explanations remain the main deliverable; long quotations are not a substitute for teaching.

New inputs use typed research-graph edges: `support`, `comparison`, `interpretation`, `deduction`, `assumption`, `contradiction`, `association`, `next_question`, `limitation` or legacy `evidence`. Give each a source-grounded label. Direction must express the actual relation; reading order remains a separate graph. Formal dependency, association and experimental evidence must not be collapsed into causality. Rich-block links join the evidence index, with exact targets on the same canvas, including side branches.

## Material inventory and optional identifiers

DOI is optional. Preserve the real citation and use an actual HTTPS `case.source_url` when appropriate; otherwise the reader links to the locally supplied source. Never fabricate an identifier.

Optional `case.materials` records use `id`, `role` (`main`, `supplement`, `appendix`, `extended_data`, `code`, `data`, `other`), `status` (`available`, `not_provided`, `not_published`, `not_applicable`) and a truthful `note`. `available` requires a `source` ID whose local file is hashed. `not_published`/`not_applicable` need a source-informed `basis`. Known remote code/data links are not local available sources. Availability and actually reviewed coverage are distinct; disclose scope in the companion's prose/coverage.

Sources may be `pdf`, `jats`, `text` (UTF-8 source with explicit locators) or `image` (original standalone supplementary image, actual-view records only). Never convert a website summary into a claimed publisher original. Preserve original downloaded source files alongside any reading extraction. Unsupported inputs need a documented conversion or a clearly limited draft.
