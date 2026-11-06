# Select a reading route from the paper's actual reasoning

Identify the study type from the question, methods and evidence, not its title, venue or discipline alone. Set `case.reading_profile` with `study_types` (first is primary), `disciplines` and a brief source-informed `rationale`. Allowed routes are `experimental`, `computational`, `observational`, `theoretical`, `evidence_synthesis` and `interpretive`. Compose routes only where each contributes actual reasoning; do not write separate duplicate stories for a mixed paper.

The route guides reading and checks; it is not a template for headings or a declaration that the paper is correct. These are candidate cross-disciplinary routes. Existing materials/chemistry examples provide regression coverage; other areas need actual source-based transfer tests and subject-reader evaluation before broad reliability claims.

## Shared core

Find the specific unresolved question, the author's move, the evidence or reasoning needed for it, the conclusion actually supported, and the remaining boundary. Organize adjacent stages by what is now understood and why the next argument matters. Preserve alternative explanations and contradictions. Explanatory reading order must not be presented as the authors' documented chronology of discovery.

Identify objects consistently: these may be specimens, populations, datasets, models, constructs, concepts or texts. Preserve their conditions, definitions, versions and scope. Keep observation, estimation, model output, assumption, formal result and interpretation distinct. The main story must be understandable without opening branches. A branch teaches a local difficulty using relevant evidence, then reconnects to the current judgment.

## Experimental

Follow the question through intervention/design, specimen identity, controls, measured observations and bounded explanation. Several measurements can answer one question; a composite can serve several questions. Explain what is held fixed and changed, which units are independent, and whether a result is representative or quantified. Distinguish preparation from treatment, a proxy stress from the target environment, and an in-vitro or heterologous model from the original organism/system.

For materials/chemistry, also read [the established domain guide](materials-chemistry.md): preparation/product identity, normalization, specimen state, structure–property inference and indirect mechanistic evidence. Set discipline `materials_chemistry` when those checks apply, including mixed biological/materials studies. Do not omit a relevant profile to avoid a failure.

For biological experiments, identify species/cell line, construct/tag, expression context, treatment, controls and biological versus technical replication. Follow phenotypes to the actual intervention and comparison. Overexpression, colocalization and an in-vitro assay can support different parts of an interpretation; none automatically establishes native-organism necessity or a unique molecular mechanism. Read the actual statistical and image descriptions rather than promoting one representative micrograph into a population result. Missing methodological information remains unknown.

## Computational

Explain the task and bottleneck, model or algorithm, why its design could help, and how evaluation tests that proposal. Read model/data versions, train/validation/test use, baselines, tuning, metrics and compute conditions wherever they affect a comparison. For simulations, track model assumptions, boundary/initial conditions, numerical resolution and validation; a language-model benchmark checklist is not universal simulation methodology.

For machine learning, distinguish total, trainable and task-specific stored parameters; training memory/time from inference latency; and adaptation from original pretraining. Explain a formula through the quantity it changes and each variable's role. For a result table, establish dataset/split, metric direction, uncertainty and compared configurations before interpreting a row. An ablation concerns the tested setup; a low-rank empirical pattern is not a theorem about every task. No claim of reproduced training, fresh benchmark results or code execution without actually doing it.

## Observational

Follow the target question through sampling, measurements, analysis, observed associations and interpretive scope. Explain population, observation unit, selection, time order, confounders, missingness and uncertainty when material. Distinguish an association, a predictive result and a causal estimate. For an explicit causal design, explain its actual identifying assumptions and available checks rather than deleting all causal language. A small p-value is not the effect size or practical importance. Do not add unreported adjustments.

## Theoretical

Start from the problem, definitions and assumptions; expose the central construction or insight, the dependencies of the argument and what the conclusion quantifies over. Read a key proof transition rather than substituting an intuitive story. Distinguish theorem, conjecture, heuristic, numerical illustration and a result stated without proof. Preserve quantifiers, parameter ranges and regularity conditions; an analogy is teaching, not proof.

Use `formal_result` only with the theoretical route, `formal_status` (`proved_in_source`, `stated_without_proof`, `conjecture`), actual `assumptions`, and source text evidence. `proved_in_source` reports the source's proof status; it does not certify an independent formal verification. `assumption` identifies an explicit premise. An empirical model result cannot become a theorem by relabeling its ledger entry. Use equation blocks for readable expressions and definitions; optional validated MathML supports offline typesetting.

## Evidence synthesis

Establish the review question, retrieval/selection process, included evidence, synthesis approach, agreements/disagreements and what uncertainty remains. Separate a systematic review, meta-analysis, scoping review and narrative review; do not invent a search or screening process for the last. Explain selection/measurement heterogeneity and the assumptions behind pooled results where relevant. A study count or pooled p-value does not replace interpretation. Use reporting standards applicable to the actual design as reading aids; do not apply a clinical checklist to all reviews.

## Interpretive

Identify the question, conceptual lens, corpus/materials and interpretive steps. Preserve quotation context, speaker/source identity, translation decisions and plausible competing readings. Qualitative empirical findings, historical source claims and the author's theoretical interpretation are distinct. Explain why a passage or case bears on the argument and what a competing interpretation changes. Do not invent experimental controls, statistical representativeness or causal identification for a textual argument. Use `qualitative_finding` or `textual_interpretation` where appropriate, backed by original sources and the paper's actual method.

## Honest fallback

When the route is uncertain, read the relevant methods and decisive evidence before choosing; briefly ask the user only if the ambiguity materially changes the deliverable. If required material is unavailable, offer a clearly scoped draft or a missing-material note. A known attachment that was not supplied is not an attachment the paper never published. Maintain both the prose and navigational experience without fabricating stages, figures or missing evidence.

Useful source-specific reading aids: [EQUATOR study-design directory](https://www.equator-network.org/) for health research and [PRISMA](https://www.prisma-statement.org/) for systematic reviews. These standards address reporting, not automatic truth certification.
