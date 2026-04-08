---
name: ml-evaluation
description: ML model evaluation and experiment tracking -- LLM benchmarking with lm-evaluation-harness (MMLU, GSM8K, HumanEval, 60+ tasks), experiment tracking and hyperparameter sweeps with Weights & Biases. Use when benchmarking models, comparing training runs, tracking experiments, or reporting evaluation results.
---

# ML Evaluation & Experiment Tracking

## Decision Tree

```
What do you need?
├── Benchmark model quality on standard tasks (MMLU, GSM8K, HumanEval)?
│   └── references/lm-eval-harness.md
├── Track training metrics, compare runs, visualize progress?
│   └── references/weights-and-biases.md
├── Optimize hyperparameters with automated sweeps?
│   └── references/weights-and-biases.md (Sweeps section)
└── Compare multiple models side-by-side on benchmarks?
    └── references/lm-eval-harness.md (Workflow 3)
```

## Quick Reference

| Tool | Purpose | Install |
|------|---------|---------|
| [lm-eval-harness](./references/lm-eval-harness.md) | Benchmark LLMs on 60+ academic tasks | `pip install lm-eval` |
| [Weights & Biases](./references/weights-and-biases.md) | Experiment tracking, sweeps, model registry | `pip install wandb` |

### lm-eval-harness -- one-liner

```bash
lm_eval --model hf --model_args pretrained=meta-llama/Llama-2-7b-hf --tasks mmlu,gsm8k,hellaswag --batch_size auto
```

### W&B -- minimal integration

```python
import wandb
wandb.init(project="my-project", config={"lr": 0.001, "epochs": 10})
for epoch in range(10):
    wandb.log({"loss": train_loss, "val_acc": val_acc})
wandb.finish()
```
