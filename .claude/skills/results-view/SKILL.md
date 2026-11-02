---
name: results-view
description: Expert in data visualization, creating the Phishing Gauge, and rendering AI analysis reports.
---

When invoked as the Results View Expert:

1. **Data Mapping (Section 5)**: Strictly expect and handle this JSON structure from the API: `{ "score": number, "verdict": string, "red_flags": array, "recommendation": string }`.
2. **Phishing Score (Section 3 & 6)**: Create a dynamic, color-coded Gauge component ranging from 1 to 10. Colors must transition: Green (Safe) -> Yellow (Suspicious) -> Red (Critical Phishing), with the same cut points as the verdicts in the prompt: 1–3 green, 4–7 yellow, 8–10 red.
3. **Reasoning Report**: Render the `red_flags` array as a clear, bulleted list of warnings.
4. **Actionable Advice**: Display the `recommendation` string prominently so the non-technical user knows exactly what to do next (e.g., "Block sender").
