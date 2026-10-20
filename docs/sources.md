# Sources

This file lists the external sources behind the numbers in `docs/costs.md`, `docs/training.md`, and `docs/model.md`. Each row has the page, the date it was opened, and the claim it supports. They can be merged into the shared sources page.

| # | Title | URL | Date opened | Claim |
| --- | --- | --- | --- | --- |
| 1 | Runpod pricing | https://www.runpod.io/pricing | 20 Oct 2026 | An RTX 4090 (24 GB) pod costs $0.34 per hour on Community Cloud and $0.89 per hour on Secure Cloud. Volume disk is $0.10 per GB per month while running and $0.20 while idle. |
| 2 | Vast.ai pricing | https://vast.ai/pricing | 20 Oct 2026 | Prices are set by the market. On-demand is billed per second. Interruptible is advertised as 50% or more cheaper but may be reclaimed. The page shows no RTX 4090 price. |
| 3 | Google Colab FAQ | https://research.google.com/colaboratory/faq.html | 20 Oct 2026 | Free notebooks run at most 12 hours. Web service offerings not related to interactive compute are prohibited. Using more than one account to get around limits is prohibited. Storage-only Google One plans do not include Colab compute units. |
| 4 | GitHub Student Developer Pack | https://education.github.com/pack | 20 Oct 2026 | Camber gives 40 CPU hours and 5 GPU hours. Azure gives $100 credit for students 18 and over. |
| 5 | Qwen2.5-Coder-3B-Instruct | https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct | 20 Oct 2026 | The 3B model is under the qwen-research license. |
| 6 | Qwen2.5-Coder-7B-Instruct | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct | 20 Oct 2026 | The 7B model is under Apache-2.0. |
| 7 | Ollama on macOS | https://docs.ollama.com/macos | 19 Oct 2026 | Intel Macs work but CPU only, on macOS 14 or newer. |
| 8 | Kaggle, Efficient GPU Usage Tips | https://www.kaggle.com/docs/efficient-gpu-usage | 20 Oct 2026 | Free access to Tesla P100 GPUs. The weekly quota resets weekly and is 30 hours or sometimes higher. Interactive sessions stay active until a 60 minute idle timeout. |
| 9 | Kaggle, Notebooks Documentation | https://www.kaggle.com/docs/notebooks | 20 Oct 2026 | One free Tesla P100 per notebook. Free GPUs can queue at busy times. "Save & Run All" must finish within 12 hours. |
| 10 | Colab T4 check | our own `nvidia-smi` run | 19 Oct 2026 | A Tesla T4 with 15360 MiB. The Resources panel reported up to 5 hours 30 minutes. This is our own observation, not a web page. |

## Not used

- Hourly Vast.ai prices from comparison blogs, because Vast's own page does not show them.
- Colab compute-unit numbers for Google AI plans, because they were reported as unverified.
