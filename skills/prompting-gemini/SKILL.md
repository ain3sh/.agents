---
name: prompting-gemini
description: Precision prompting techniques for Gemini 3 Pro's unique characteristics and quirks. Use when crafting prompts for Gemini 3 to avoid common failures and leverage unintuitive strengths.
license: MIT
---

Critical rules for Gemini 3 Pro that violate typical LLM assumptions.

## Non-Negotiable Settings

```
temperature: 1.0  # NEVER CHANGE - causes loops/degradation at <1.0
top_k: default    # Let model handle
top_p: default    # Let model handle
```

## Unintuitive Strengths to Exploit

### Structure Beats Prose
```xml
<!-- THIS WORKS -->
<context>
[data here]
</context>
<task>
Analyze the data above
</task>

<!-- NOT THIS -->
Please analyze the following data: [data]
```

### Planning Directives Transform Performance
For ANY complex task, prepend:
```
Before answering:
1. Decompose the problem into components
2. Create a step-by-step plan
3. Validate your approach
Then execute.
```

### Few-Shot Can Replace Instructions
Instead of explaining what you want, show 2-3 examples. Model infers patterns better than following descriptions.

### Context Dumping Works
Put ALL context first, instruction last. Even 50K tokens of context. Model handles it better than interleaved instructions.

## Unintuitive Failures to Avoid

### Terse by Default
Without explicit verbosity control, expect telegram-style responses.
```xml
<constraints>
Verbosity: High  <!-- REQUIRED for detailed answers -->
</constraints>
```

### Politeness Degrades Performance
```
❌ "Could you please help me understand..."
✅ "Explain X."
```

### Mixed Instructions Cause Chaos
```
❌ Context, instruction, more context, another instruction
✅ ALL context → ALL instructions
```

### Natural Language < Structured Commands
```
❌ "Write something creative but not too long"
✅ "Output: 500-word story. Style: surrealist."
```

## Task-Specific Patterns

### Complex Analysis
```xml
<system>
<reasoning>explicit_chain_of_thought</reasoning>
</system>

<data>[all context]</data>

<analysis_directive>
1. Parse all entities
2. Map relationships  
3. Identify patterns
4. Draw conclusions
Output format: Structured findings with evidence
</analysis_directive>
```

### Creative Generation
```xml
<parameters>
Style: [specific aesthetic]
Constraints: [exact limits]
Avoid: [anti-patterns list]
</parameters>

<directive>
First: Commit to ONE bold direction
Then: Execute fully without hedging
</directive>
```

### Code/Technical
```xml
<requirements>
- Complete implementation only
- No placeholders/TODOs
- Production-ready
- Include error handling
</requirements>

<task>[specific ask]</task>
```

### Multimodal
```
[Image/PDF/Media FIRST]

<task>
Describe what you see, then [specific analysis]
</task>
```

## Quick Optimization Checklist

- [ ] Temperature = 1.0?
- [ ] Used XML/Markdown tags?
- [ ] All context BEFORE instructions?
- [ ] Explicit verbosity setting?
- [ ] Removed all politeness?
- [ ] Added planning directive for complex tasks?
- [ ] Specified exact output format?
- [ ] One clear task, not multiple?
- [ ] Examples instead of explanations?

## Emergency Fixes

| Symptom | Fix |
|---------|-----|
| Looping output | Check temperature (must be 1.0) |
| Too brief | Add `<constraints>Verbosity: High</constraints>` |
| Confused execution | Restructure: context→task→output spec |
| Generic output | Add anti-patterns list + "be distinctive" |
| Misses instructions | Use XML tags, not prose |
| Poor reasoning | Add explicit planning phase |

## The Golden Template

```xml
<role>[If needed - domain expert]</role>

<context>
[EVERYTHING relevant - frontload it all]
</context>

<planning>
Before executing, create step-by-step approach
</planning>

<task>
[ONE clear directive]
</task>

<constraints>
- Verbosity: [Low/Medium/High]
- Format: [Exact specification]
- Avoid: [Anti-patterns]
</constraints>
```

Remember: Gemini 3 is a precision instrument, not a conversation partner. Treat it like a powerful but literal compiler that rewards structure and punishes ambiguity.