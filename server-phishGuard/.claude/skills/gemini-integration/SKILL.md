---
name: gemini-integration
description: Expert in Google Gemini Vision API integration, prompt engineering, and LLM output parsing.
---

When invoked as the Gemini Integration Expert:

1. **AI Engine (Section 2)**: Integrate the Google Gemini API (Vision-Language Model; currently `gemini-3.5-flash-lite`, set once in `MODEL_NAME`) using the official Google GenAI SDK. Read the API key securely from a `.env` file.
2. **System Prompt Strategy (Sections 3 & 5)**: Design a robust prompt instructing the AI to perform both Visual Analysis (brand inconsistency, UI patterns) and Textual/OCR Analysis (social engineering tactics, urgency, grammar). 
3. **Output Forcing (Section 5)**: You must force the Gemini model to return a strict, raw JSON object (or use Structured Outputs if supported by the SDK) containing ONLY:
   - `score` (Integer 1-10)
   - `verdict` (String: "Safe", "Suspicious", or "Phishing")
   - `red_flags` (List of Strings)
   - `recommendation` (String)
4. **Error Handling**: No automatic retries, since each retry spends quota and time. Malformed JSON or an invalid answer returns 502; no answer within `REQUEST_TIMEOUT_SECONDS` returns 504.