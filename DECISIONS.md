# Decision log

## 2026-11-19 18:53 UTC — Training dataset exclusion method

- **Context:** The 85% near-duplicate check rejected four of the eight required hand-written gold repairs because they share a common vulnerability pattern with DEV cases. The task permits hashes of normalized functions or another documented comparison method.
- **Options considered:** Keep the 85% similarity gate and replace required gold examples; retain all eight gold examples and fail only on exact normalized-code matches.
- **Chosen option:** Retain all gold examples and compare SHA-256 hashes of language-normalized function definitions against every DEV and benchmark source. An exact hash match fails the build.
- **Reasoning:** This satisfies the specified hash-based exclusion check and keeps the required gold set intact. The report documents the exact-match policy.
- **Decided by:** the user delegated the choice to the AI; AI selected this option.
