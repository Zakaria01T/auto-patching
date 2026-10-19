# Training (LoRA)

LoRA training will run on Google Colab using a free Tesla T4 GPU (about 15 GB), which I opened and confirmed on 2026-10-19 (`nvidia-smi` showed the T4; the free runtime reported up to about 5.5 hours per session). The training data will be pairs of vulnerable code and a repair. The model stays frozen and only a small adapter is trained, so the prompted model remains the default and LoRA is a comparison. Kaggle is the backup if Colab has no free GPU.
