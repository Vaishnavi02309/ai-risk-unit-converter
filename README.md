On each PR, the workflow:

Computes a diff,

Scores risk using rules.yml (paths, keywords, size),

Optionally asks Gemini once for a sanity check (nudges score by ±1/±2),

Posts a single PR comment with the risk summary,

Blocks the PR when risk is HIGH and tests weren’t touched.

Set GEMINI_API_KEY in repo secrets to enable the AI nudge. Without it, the tool still works using rules only (no rate-limit headaches).