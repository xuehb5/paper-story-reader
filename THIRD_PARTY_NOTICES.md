# Third-party materials and design references

The root MIT license applies to this project's original code, skill instructions and explanatory documentation. It does not replace licenses on scientific source materials.

## Hydrogel worked example — CC BY 3.0

Rui Chen, Krishnendu Das, Jun Feng, Boonya Thongrom and Rainer Haag. **Photo-regulated disulfide crosslinking: a versatile approach to construct mucus-inspired hydrogels.** Chemical Science, 2025, 16, 5528–5537. [DOI: 10.1039/d4sc08284b](https://doi.org/10.1039/d4sc08284b).

The supplied article's own license statement says: “This article is licensed under a Creative Commons Attribution 3.0 Unported Licence.” See [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).

The original article XML, same-paper Supporting Information PDF, full figures, source-page images, and figure crops in `examples/hydrogel/sources/` and `examples/hydrogel/figures/` retain that license and their original attribution. These materials come from the article and its SI. Some page images are rendered from the PDF and some images are cropped for explanation; the source files, original full-view links and hashes are retained. Figures were not redrawn and numerical data were not altered.

The Chinese and English reading text and evidence annotations are AI-assisted explanatory work by this project. They are not the paper authors' endorsement or independent experimental validation. Reuse must retain the attribution for the underlying article materials.

The English worked example in `examples/hydrogel-en/` adapts the same source-grounded story and reuses the hash-identical images and original quotations. It introduces no new experimental data. Its internal ledger retains earlier original-language source/visual observations for provenance and records the English adaptation review separately.

## Design references

[references/design-sources.md](references/design-sources.md) names reading-skill projects and domain guidance consulted during design. Their source code is not vendored here, and they are not runtime dependencies. Their own licenses and trademarks remain with their authors.

## Optional dependencies

`pypdf` and optional `pypdfium2` are separately installed packages with their own licenses. They are not vendored in this repository. The generated reader uses this repository's JavaScript/CSS and the browser's native APIs; it does not load external JavaScript libraries or fonts.
