---
name: paperclip
description: Search, grep, map, and query millions of biomedical and arXiv papers via the Paperclip CLI/MCP from gxl.ai. Use for literature review, biomedical and life-sciences research, drug/target/mechanism mining, citation grounding during paper writing, related-work surveys before implementation, "what does the literature say about X", or any task that benefits from corpus-wide regex over scientific full text. Teaches the stateful-handle chaining pattern (search → from → grep/map/cat) that makes agents more accurate and cheaper than abstract-only MCPs like PubMed and Semantic Scholar.
---

# Paperclip — agent-native scientific literature CLI

Paperclip exposes ~11M biomedical and arXiv papers plus 50M OpenAlex abstracts as a virtual filesystem. Every paper is a directory, every section an addressable file, every figure server-side VLM-queryable. Six primitives (`search`, `grep`, `map`, `cat`, `ask-image`, `sql`) compose through stateful handles. Corpus-wide regex in milliseconds and parallel `map` over papers are the differentiators vs abstract-only MCPs (PubMed, Semantic Scholar, Crossref).

## When to use

- Lit review, scoping a research area, "what does the literature say about X"
- Mechanism mining: resistance mechanisms, failure modes, side effects
- Multi-paper structured extraction
- Corpus-wide regex over methods/results sections
- Citation grounding while writing (pair with `code2paper`)
- Related-work survey before reimplementing (pair with `paper2code`)
- Cross-corpus jumps: bio limitation → arXiv solution

## When NOT to use

- Single arxiv ID → implement: use `paper2code`
- Writing a paper from a research repo: use `code2paper`
- Non-bio/non-arXiv journals (Wiley, Springer, Elsevier closed access): `paper-search` MCP
- Need a downloadable PDF, not in-place reading: `paper-search` `download_paper`

## Install

MCP (preferred for in-droid use):

```bash
claude mcp add --transport http paperclip https://paperclip.gxl.ai/mcp
```

CLI fallback:

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
paperclip login && paperclip config
```

## Mental model

Every result set has a stable handle (`s_<8 hex>`). Subsequent calls reference it via `--from`. **Anchor once, refine many times:**

```
search ──▶ s_74db6679 ──▶ grep --from s_74db6679 ──▶ s_a1b2c3d4 (narrower)
                       ──▶ map  --from s_74db6679 ──▶ structured table
                       ──▶ cat  PMC.../sections/Methods.lines
```

The corpus is also a literal filesystem at `/papers/<paper_id>/`:

```
meta.json                     # title, authors, date, DOI, abstract, source
sections/{Abstract,Introduction,Methods,Results,Discussion}.lines
supplements/*.csv
figures/*.png
```

Section names are PascalCase. Paper IDs: `PMC<digits>`, `bio_<hex>`, `med_<hex>`, `arxiv_<id>`.

## Primitives

`search "query" -n 5 [-s pmc|biorxiv|medrxiv|arxiv|abstracts]`
Returns 1–2 sentence TL;DRs (not full abstracts) and a handle. Default sources are indexed full text; `-s abstracts` widens to 50M OpenAlex abstracts for landscape mapping.

`grep "regex" [--from <handle>]`
Corpus-wide or handle-scoped regex; returns a narrowed handle. Filesystem globs work: `paperclip grep "IC50" /papers/*/sections/Results.lines`.

`map --from <handle> --query "..."`
Parallel structured extraction across the working set; returns a table. ~15s for 20 papers vs ~2min sequentially. `--reduce <prompt>` synthesizes across rows (flag varies by version — check `--help`).

`cat <paper_id> [--section <Section>]`
Filesystem read. Section-scoped reads are surgical (~hundreds of tokens vs ~40K full).

`ask-image <figure_path> "question"`
Server-side VLM Q&A on a paper figure. No download.

`sql "SELECT ..."`
Structured queries over corpus metadata; reaches the 100M unindexed OpenAlex abstracts. Check `paperclip sql --help` for the current schema.

## Token discipline

1. Always pass `-n` on `search` (5–50 depending on whether you'll filter via `grep` after).
2. After the first `search`, every follow-up uses `--from <handle>`. **More than two top-level `search` calls per question is a failure mode.**
3. Use `map`, never a `for` loop over papers.
4. `grep` before `cat`. A grep returns ~200 tokens; a full `cat` returns ~40K.
5. `ask-image` over downloading figures — it's server-side.
6. The TL;DR in `search` output stands in for the abstract. Don't `cat --section Abstract` to re-read it.

## Worked recipes

See `references/cookbook.md` for the six end-to-end transcripts (KRAS resistance, AlphaFold failures, GRPO hyperparameters, bioRxiv→arXiv bridge, citation grounding, pre-implementation survey) plus troubleshooting.

## Composes with

- **`code2paper`** — verifies citation claims against full text, not just abstracts. Hand verified results back for BibTeX retrieval.
- **`paper2code`** — pre-implementation pass to surface official-code claims and comparable implementations.
- **`paper-search` MCP** — breadth fallback for non-bio/non-arXiv journals and PDF downloads. Worse for full-text grep and multi-paper extraction.
- **WebSearch** — complementary for blog posts, tutorials, and benchmark write-ups not in any paper corpus.

## Disambiguation

Different product from `paperclipai/paperclip` on GitHub (orchestration framework). This skill is gxl.ai's literature CLI at https://paperclip.gxl.ai. Source posts: [launch](https://gxl.ai/blog/paperclip/), [arXiv addition](https://gxl.ai/blog/adding-arxiv-and-abstracts/), [filesystem rationale](https://gxl.ai/blog/biomedical-literature-as-a-filesystem/).
