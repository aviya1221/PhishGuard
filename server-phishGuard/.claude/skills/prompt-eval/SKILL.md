---
name: prompt-eval
description: Rules for changing the Gemini prompt, model or temperature. Measure on the eval sets before and after, and never tune on the held-out set.
---

When invoked as the Prompt Evaluator:

1. **Baseline first**: Before changing the prompt, the model or the temperature, run `eval/run_eval.py` on the dev set and keep its results file.
2. **One change at a time**: Change one thing, run again with `--output` to a new file, and compare accuracy, false alarms and tokens per scan.
3. **Held-out stays held out**: Run `--dir eval/holdout` only to check a finished change. Never tune the prompt to fix a held-out mistake; that needs a new set.
4. **Strict metric**: Only a "Phishing" verdict counts as detected (`DETECTED_VERDICTS`). Report Suspicious answers separately, and never move the cut to improve a number.
5. **Privacy**: Eval images are personal messages. Never commit them; only labels, scripts and results go to git.
