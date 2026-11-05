# English hydrogel-paper companion

This is the full English adaptation of the PaperStory hydrogel worked example: 7 stages, 61 explanatory paragraphs including close reading, 25 figure occurrences, 11 substantial branches, 14 close-reading tasks, 5 complete-composite views and a separate scientific argument graph. It uses the same renderer and source images as the Chinese companion.

Source: Rui Chen et al., *Photo-regulated disulfide crosslinking: a versatile approach to construct mucus-inspired hydrogels*, Chemical Science 2025, 16, 5528–5537, DOI [10.1039/d4sc08284b](https://doi.org/10.1039/d4sc08284b). Original article, matching SI and images retain CC BY 3.0; see [third-party notices](../../THIRD_PARTY_NOTICES.md).

The input references the original files in `../hydrogel/`; they are not duplicated or redrawn. Keep both example directories in a checkout. Source hashes and original-language quotations are unchanged. English visible statements were checked for the same sample identities, conditions, metric limits and inferential level. The internal ledger retains earlier original-language detailed source/visual observations for provenance and explicitly records the English adaptation review as `same_agent_second_pass`. It does not claim a new independent reviewer, fresh image measurement, experimental replication, cross-model evaluation or human comprehension study.

```bash
python scripts/render_reader.py examples/hydrogel-en/reader-input.json --review examples/hydrogel-en/evidence-review.json --context-audit examples/hydrogel-en/context-audit.json --output build/hydrogel-en
python scripts/verify_delivery.py build/hydrogel-en/A.html build/hydrogel-en/A.md --language en --manifest build/hydrogel-en/delivery-manifest.json
```

Run from the repository root. Open the generated `index.html`. Rebuilding replays the saved adaptation and review records; it does not ask a model to read a new paper. The scientific explanation still needs source-based scrutiny.
