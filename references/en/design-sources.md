# Design choices and attribution

PaperStory is an independent reading workflow focused on experimental materials and chemistry. Its central choice is prose-first explanation: a research story remains readable on its own, a shared story map locates its stages and branches, and a separate scientific argument graph makes evidence relationships explicit. Main paper and matching SI are read together where they answer the same question.

The persistent canvas, connection-aware camera movement, nearby close-reading branches, source-page views and current-location synchronization respond to concrete reading and navigation needs. The renderer is shared between English and Chinese editions; an English demo must retain the actual canvas rather than substitute a simplified page.

This edition does not ship a language model or proprietary paper-reading service. It uses the user's chosen Agent for source interpretation and a deterministic local renderer for reviewed content. Hash checks establish byte identity, not scientific truth. Source review records, software tests and human reading outcomes are separate forms of evidence.

The original project records broader design references in the repository's Chinese `references/design-sources.md`. The English edition does not claim those external projects were freshly tested or independently benchmarked. Original code and instructions use the repository's MIT license; example papers, SI and figures retain their stated third-party licenses.
