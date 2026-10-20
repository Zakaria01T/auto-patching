# Costs

This file records how the optional LoRA adapter is trained, what running the model costs, and which numbers are assumptions.

No model is served by the pipeline yet. Where the demo model is hosted is decided after the demo is built, so both options stay here.

## Build versus train

The prototype ships with a prompted local code model. A small LoRA adapter is trained offline as a comparison. It replaces the prompted model only if it scores higher on the dev set before the sealed benchmark run. The official fix rate is always reported for the path that was frozen before that run. If the adapter does not help, the report says so, with the numbers.

## What training costs

Training uses a free Colab or Kaggle GPU, so it has no cash cost.

- Colab: a Tesla T4 with about 15 GB of memory was opened and checked on 19 October 2026 (see `docs/training.md`). Free notebooks run at most 12 hours.
- Kaggle: two Tesla T4 GPUs (15 GB each) were opened and checked on 20 October 2026, with 30 GiB of RAM and a 12 hour session. Kaggle's documentation names a free Tesla P100 and a weekly quota of 30 hours or sometimes higher, so the T4 option is what this account showed.

The free tiers are meant for interactive work. Colab prohibits web service offerings not related to interactive compute, so they are not used to serve the model to the team.

## What running the model costs

Option A, one rented GPU for the benchmark and the live demo. RunPod lists an RTX 4090 (24 GB) at $0.34 per hour on Community Cloud and $0.89 per hour on Secure Cloud. Assumption: 15 to 40 hours over the twelve weeks. That is about $5 to $36 in total, or under $1 to about $5 per person for seven people. A disk for the model files costs $0.10 per GB per month while it runs, about $5 a month for 50 GB, so it is deleted between sessions.

Option B, a team laptop with the 3B model. No fee. It is slower, and the 7B model is not an option on the laptops we have.

The Vast.ai pricing page does not show an RTX 4090 price, so no Vast number is used.

## Course cost total

Student time, plus free tools, plus the assumed GPU rental if option A is chosen. Nothing extra for option B. The course prototype has no revenue.

## What this changes in the plan

Sections 4.9 and 4.11 of the plan say the model runs on a team laptop at no fee. That stays true for option B. If option A is chosen after the demo is built, those two sections change to say the model is served from a rented GPU.

Sources for every price and limit above are in `docs/sources.md`.
