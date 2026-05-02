# Paperclip cookbook

Six recipes. Each follows: anchor → refine → extract.

---

## 1. Drug-target lit review (KRAS G12C resistance)

Goal: "What resistance mechanisms have been reported for KRAS G12C inhibitors?"

```bash
paperclip search "KRAS G12C resistance mechanisms" -n 5
# → Found 5 papers  [s_74db6679]

# Optional narrow to mechanism-discussing papers
paperclip grep "secondary mutation|switch-II|MET amplification" --from s_74db6679

# Structured extraction across all 5
paperclip map --from s_74db6679 \
  --query "What resistance mechanism was reported? Class: mutation/amplification/bypass/co-mutation. Gene if applicable."

# Outlier zoom (one paper claimed CIC loss; every other was on-target)
paperclip cat PMC11364849 --section Methods
paperclip ask-image /papers/PMC11364849/figures/figure_2.png \
  "Does this support CIC loss as primary, or correlative?"
```

Example `map` output (per the blog):

| Paper        | Mechanism                                          | Type                       |
|--------------|----------------------------------------------------|----------------------------|
| PMC7795113   | Y96D, H95D secondary mutations; MET amplification  | on-target, RTK bypass      |
| PMC9399772   | Q99L switch-II pocket mutation                     | on-target                  |
| PMC11364849  | CIC loss-of-function via NFκB reactivation         | tumor suppressor           |
| PMC8843735   | KRAS amplification (18%), RAS switching, KEAP1     | amplification, co-mutation |

3–5 calls, ~5–10K tokens. Naive equivalent (20 sequential abstract reads + extraction) is ~80K.

---

## 2. Stateful mechanism mining (AlphaFold failure modes)

Goal: "What are the documented failure modes of AlphaFold?"

```bash
paperclip search "AlphaFold failure modes limitations" -n 50
# → Found 50 papers  [s_8a4f2e91]   # high -n is fine when grep will filter

paperclip grep "fold switching"          --from s_8a4f2e91   # 8 matches
paperclip grep "intrinsically disordered" --from s_8a4f2e91  # 12 matches
paperclip grep "training data|MSA"        --from s_8a4f2e91  # 10 matches

paperclip cat <top_match_id> --section Discussion
```

Findings reported in the blog, none of which appear in any abstract:

- **XCL1 (lymphotactin)** — body text, surfaced by "fold switching"
- **β-solenoid hallucination** — Results, surfaced by "intrinsically disordered"
- **Adversarial invariance** — Methods, surfaced by "training data|MSA"

A standard MCP-backed agent finds the canonical training-data examples (KaiB, RfaH, p53) and misses all three. Full-text grep is the difference.

---

## 3. Methods-section recon (GRPO hyperparameters)

Goal: "What batch size × learning rate combinations do GRPO papers actually use?"

Pattern: broad grep → narrow grep → structured `map` → aggregate client-side.

```bash
paperclip grep -i "GRPO|group relative policy optimization" -s arxiv
# → 6,477 papers  [s_grpo_main]

paperclip grep "learning rate.*1e-[0-9]" --from s_grpo_main
# → 1,145 papers, 2,079 paragraphs  [s_grpo_lr]

paperclip map --from s_grpo_lr \
  --query "Extract batch_size (int) and learning_rate (sci notation) from Methods. Null if not stated."
```

10 queries, ~3s wall-clock per the blog. Modal config: batch_size=128, lr=1e-6 (52 papers).

---

## 4. Cross-corpus limitation → solution (scRNA-seq → arXiv)

Goal: a bioRxiv paper has a stated limitation; find an arXiv paper that addresses it.

```bash
# 1. Resolve the source paper to a Paperclip ID
paperclip search "Erasure of Biologically Meaningful Signal scRNA batch correction" \
  -s biorxiv -n 1
# → bio_<id>  [s_src]

# 2. Read its limitation
paperclip cat bio_<id> --section Discussion
# "Unsupervised batch correction (Harmony, scVI) erases real biological
#  signal when batch and biology are confounded."

# 3. Translate bio framing → ML framing, search arXiv
paperclip search "disentangled representations correlated factors weak supervision" \
  -s arxiv -n 10
# → s_disentangle

# 4. Confirm the link
paperclip cat arxiv_2006.07886 --section Abstract
```

The arXiv hit (Träuble et al., 2020) proves unsupervised methods can't disentangle correlated factors and proposes weak supervision — applicable directly to the bio problem. ~6 calls, ~1.4s. Pattern works in either direction; translation between field vocabularies is the actual work.

---

## 5. Citation grounding (for code2paper)

When `code2paper` is drafting and you need to cite prior work, verify the claim against full text. Abstract-only lookups confirm a paper exists, not that it supports your specific claim.

```bash
paperclip search "{claim being made}" -n 10
# → s_cite_set

paperclip map --from s_cite_set \
  --query "Does this paper actually demonstrate or claim: '{specific claim}'? Quote the supporting sentence if yes."

# Cite only papers where the answer is yes-with-quote.
```

Hand verified citations to `code2paper`'s BibTeX-fetching workflow.

---

## 6. Pre-implementation related-work (for paper2code)

Before `paper2code` implements an arXiv paper, surface prior implementations and comparable methods.

```bash
paperclip search "{target_paper_title} {core_method}" -s arxiv -n 20
# → s_related

paperclip grep "github\.com|huggingface\.co|zenodo\.org" --from s_related
# → s_with_code

paperclip map --from s_with_code \
  --query "Does this paper implement {core_method}? If yes: framework (pytorch/jax), key hyperparameters, code link."
```

Hand the table to `paper2code` Stage 1 to cross-reference design decisions.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `search` returns nothing useful | Query too jargon-heavy or too narrow | Try `-s abstracts` for breadth, or rephrase in lay terms |
| `grep --from` returns 0 | Working set genuinely lacks the term | Re-anchor with broader `search`; absence in handle ≠ absence in corpus |
| `map` returns mostly null | Query too specific for paper population | Loosen, or split into two narrower `map`s |
| `ask-image` hedges | Figure is genuinely ambiguous | `cat --section Results` for the figure caption first |
| Need a feature outside the six primitives | Surface evolves | `paperclip --help` |
