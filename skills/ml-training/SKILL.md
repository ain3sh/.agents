---
name: ml-training
description: LLM fine-tuning and alignment -- LoRA/QLoRA with PEFT, RLHF/DPO/GRPO with TRL, YAML-driven training with Axolotl. Use when fine-tuning language models, doing parameter-efficient training, preference alignment, reinforcement learning from human feedback, or configuring distributed training.
---

# LLM Fine-Tuning & Alignment

## Decision Tree

```
What are you trying to do?
├── Fine-tune with LoRA/QLoRA (parameter-efficient)?
│   └── references/peft.md
├── Align model with human preferences (DPO/RLHF)?
│   └── references/trl.md
├── Full RLHF pipeline (SFT → Reward Model → PPO)?
│   └── references/trl.md
├── YAML-based training config (Axolotl)?
│   └── references/axolotl.md
└── Not sure which method?
    └── See method selection below
```

## Method Selection

| Method | When to use | Memory (7B) | Reference |
|--------|------------|-------------|-----------|
| **PEFT/LoRA** | Fine-tune on limited GPU, train <1% params | 18 GB | [peft.md](./references/peft.md) |
| **QLoRA** | Fine-tune 70B on 24GB GPU | 6 GB | [peft.md](./references/peft.md) |
| **SFT** (TRL) | Instruction tuning from prompt-completion pairs | 16 GB | [trl.md](./references/trl.md) |
| **DPO** (TRL) | Preference alignment without reward model | 24 GB | [trl.md](./references/trl.md) |
| **PPO** (TRL) | Full RLHF with reward model | 40 GB | [trl.md](./references/trl.md) |
| **GRPO** (TRL) | Memory-efficient online RL | 24 GB | [trl.md](./references/trl.md) |
| **Axolotl** | YAML-driven multi-method training | varies | [axolotl.md](./references/axolotl.md) |

## Quick Starts

### LoRA fine-tuning (most common)

```python
from peft import get_peft_model, LoraConfig
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B", device_map="auto")
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, target_modules="all-linear"))
model.print_trainable_parameters()  # ~0.17%
```

### DPO alignment (simplest preference method)

```python
from trl import DPOTrainer, DPOConfig

trainer = DPOTrainer(
    model=model,
    args=DPOConfig(output_dir="model-dpo", beta=0.1),
    train_dataset=preference_dataset,  # needs chosen/rejected columns
    processing_class=tokenizer
)
trainer.train()
```

### Axolotl (YAML config)

```bash
accelerate launch -m axolotl.cli.train config.yaml
```
