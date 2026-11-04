# PaperStory · Read papers as research stories

[**Live demo**](https://xuehb5.github.io/paper-story-reader/demo/) · [**Download Skill**](https://github.com/xuehb5/paper-story-reader/releases/latest) · [中文说明](README.md)

A local Agent Skill and offline reader generator for experimental materials and chemistry papers. It connects the main article and its own Supporting Information into a source-grounded research story: motivation, design, key comparisons, observations and bounded conclusions.

![Actual reader interface](docs/images/reader.png)

The explanatory prose is the main deliverable. A synchronized reading map, a separate scientific argument graph, and left/right branches help readers locate explanations. The reader uses one pannable, zoomable canvas with animated camera movement. Original figures and source files remain available locally.

The Agent reads and interprets the paper. Python validates evidence records and renders the reader; this repository does not bundle a language model or automatically certify scientific correctness. The current interface and worked example are primarily Chinese.

## Run the worked example

Python 3.10+; `pypdf` is needed for PDF text checks. JATS parsing and the core renderer use the standard library. Work inside a virtual environment.

```bash
git clone https://github.com/xuehb5/paper-story-reader.git
cd paper-story-reader
python -m pip install -r requirements.txt
python scripts/render_reader.py examples/hydrogel/reader-input.json --review examples/hydrogel/evidence-review.json --context-audit examples/hydrogel/context-audit.json --output build/hydrogel
python scripts/verify_delivery.py build/hydrogel/A.html build/hydrogel/A.md --manifest build/hydrogel/delivery-manifest.json
```

Open `build/hydrogel/index.html`. Use a new empty output directory for every revision. Rebuilding this example replays saved, reviewed content; it is not a new model run or an experimental reproduction.

## Use with an Agent

Import the complete repository as a local skill or provide its `SKILL.md`, `references/`, `scripts/`, and `assets/` to an Agent that can read files and images and execute Python. Supply the main paper, its matching SI and clear original figures. Ask for a continuous explanation first, with evidence-linked navigation and source-first review. See [usage](docs/usage.md) and the [data contract](references/portable-reader.md).

Complete builds require actual evidence records. `--draft` explicitly marks an unreviewed preview. Hashes, coverage checks and condition checks do not determine scientific entailment or prove that a reader understood the paper.

## Development and licensing

Run `python -m unittest discover -s tests -v`. See [CONTRIBUTING.md](CONTRIBUTING.md).

Original code, skill instructions and project documentation are MIT licensed. Article/SI/figure materials in the hydrogel example retain their original CC BY 3.0 license. See [third-party notices](THIRD_PARTY_NOTICES.md). No affiliation with the paper authors, publisher or Agent platforms is implied.
