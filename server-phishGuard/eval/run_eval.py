"""
Run the evaluation set through GeminiService and report how well phishing is detected.

Calls the service directly (not over HTTP), so the API rate limiter is not involved.

Usage, from server-phishGuard/:
    .venv/Scripts/python eval/run_eval.py --limit 3
    .venv/Scripts/python eval/run_eval.py
    .venv/Scripts/python eval/run_eval.py --model gemini-2.5-flash-lite
    .venv/Scripts/python eval/run_eval.py --dir eval/holdout
"""
import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google.genai import types

EVAL_DIR = Path(__file__).resolve().parent
SERVER_DIR = EVAL_DIR.parent

# Same setup as main.py: load .env before importing the service, which reads the key at import time
sys.path.insert(0, str(SERVER_DIR))
load_dotenv(SERVER_DIR / ".env")

from services.gemini_service import MODEL_NAME, SUPPORTED_LANGUAGES, gemini_service  # noqa: E402

# USD per 1M tokens as (input, output), copied from Google's pricing page.
# Left empty on purpose: fill them in yourself, never guess. Thinking tokens are billed as output.
PRICES_PER_1M = {
    "gemini-3.5-flash-lite": (None, None),
}

ALLOWED = {
    "label": {"phishing", "legit"},
    "source": {"internet", "own"},
    "type": {"sms", "email", "web"},
}

# Strict: only Phishing counts as detected. Suspicious is a soft warning, so it is a miss on
# phishing and not a false alarm on legit. Same cut on both sides, or "always Suspicious" would score 100%.
DETECTED_VERDICTS = {"Phishing"}

# Same magic bytes check as the API (main.py)
IMAGE_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}

RESULT_COLUMNS = [
    "filename", "label", "source", "type", "model", "language", "score", "verdict", "detected", "correct",
    "latency_s", "input_tokens", "image_tokens", "output_tokens", "thinking_tokens", "cost_usd", "error",
]


def load_labels(labels_path: Path, images_dir: Path) -> list[dict]:
    """Read labels.csv and stop with a clear message if anything is wrong, before any API call."""
    with open(labels_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    problems = []
    seen = set()
    for line_no, row in enumerate(rows, start=2):
        name = row.get("filename", "")
        if name in seen:
            problems.append(f"line {line_no}: duplicate filename {name}")
        seen.add(name)
        if not (images_dir / name).is_file():
            problems.append(f"line {line_no}: image not found: {name}")
        for column, allowed in ALLOWED.items():
            if row.get(column) not in allowed:
                problems.append(f"line {line_no}: {column}={row.get(column)!r}, expected one of {sorted(allowed)}")

    if problems:
        sys.exit("labels.csv has problems:\n  " + "\n  ".join(problems))
    return rows


def detect_mime_type(data: bytes) -> str | None:
    for signature, mime_type in IMAGE_SIGNATURES.items():
        if data.startswith(signature):
            return mime_type
    return None


def token_counts(usage: types.GenerateContentResponseUsageMetadata | None) -> dict:
    """Pull the token numbers out of Gemini's usage metadata (None when Gemini didn't report them)."""
    if usage is None:
        return {"input_tokens": None, "image_tokens": None, "output_tokens": None, "thinking_tokens": None}

    # prompt_token_count covers the prompt text and the image; the details split it by modality
    image_tokens = sum(
        detail.token_count or 0
        for detail in usage.prompt_tokens_details or []
        if detail.modality == types.MediaModality.IMAGE
    )
    return {
        "input_tokens": usage.prompt_token_count,
        "image_tokens": image_tokens,
        "output_tokens": usage.candidates_token_count,
        "thinking_tokens": usage.thoughts_token_count or 0,
    }


def cost_usd(tokens: dict, model: str) -> float | None:
    """Cost of one scan, or None if the prices for this model are not filled in."""
    price_in, price_out = PRICES_PER_1M.get(model, (None, None))
    if price_in is None or price_out is None or tokens["input_tokens"] is None:
        return None
    billed_output = (tokens["output_tokens"] or 0) + tokens["thinking_tokens"]
    return (tokens["input_tokens"] * price_in + billed_output * price_out) / 1_000_000


async def evaluate_image(row: dict, images_dir: Path, model: str, language: str) -> dict:
    """Analyze one image and return a result row. Errors are recorded, not raised."""
    result = {**row, "model": model, "language": language}
    data = (images_dir / row["filename"]).read_bytes()
    mime_type = detect_mime_type(data)
    if mime_type is None:
        return {**result, "error": "not a PNG or JPEG file"}

    start = time.perf_counter()
    try:
        analysis, usage = await gemini_service.analyze_image_with_usage(data, mime_type, language, model)
    except Exception as e:  # HTTPException from the service, or anything unexpected
        return {**result, "latency_s": round(time.perf_counter() - start, 2), "error": getattr(e, "detail", str(e))}
    latency = time.perf_counter() - start

    tokens = token_counts(usage)
    detected = analysis.verdict in DETECTED_VERDICTS
    cost = cost_usd(tokens, model)
    return {
        **result,
        **tokens,
        "score": analysis.score,
        "verdict": analysis.verdict,
        "detected": detected,
        "correct": detected == (row["label"] == "phishing"),
        "latency_s": round(latency, 2),
        "cost_usd": None if cost is None else round(cost, 8),
        "error": "",
    }


def percent(part: int, whole: int) -> str:
    return f"{part / whole:.0%} ({part}/{whole})" if whole else "n/a"


def average(values: list) -> str:
    values = [v for v in values if v is not None]
    return f"{sum(values) / len(values):,.1f}" if values else "n/a"


def print_summary(results: list[dict], model: str) -> None:
    ok = [r for r in results if not r["error"]]
    failed = [r for r in results if r["error"]]
    tp = sum(r["label"] == "phishing" and r["detected"] for r in ok)
    fn = sum(r["label"] == "phishing" and not r["detected"] for r in ok)
    fp = sum(r["label"] == "legit" and r["detected"] for r in ok)
    tn = sum(r["label"] == "legit" and not r["detected"] for r in ok)

    print(f"\n=== Summary: {model} ===")
    print(f"Images analyzed: {len(ok)}, failed: {len(failed)}")
    for r in failed:
        print(f"  FAILED {r['filename']}: {r['error']}")
    if not ok:
        return

    print("\nConfusion matrix (detected = Phishing)")
    print(f"{'':18}{'detected':>10}{'missed':>10}")
    print(f"{'actual phishing':18}{tp:>10}{fn:>10}")
    print(f"{'actual legit':18}{fp:>10}{tn:>10}")

    print(f"\nAccuracy:  {percent(tp + tn, len(ok))}")
    print(f"Precision: {percent(tp, tp + fp)}   of everything flagged, how much was really phishing")
    print(f"Recall:    {percent(tp, tp + fn)}   of the real phishing, how much was caught")
    print(f"False alarms on legit: {percent(fp, fp + tn)}")

    print("\nVerdicts per label")
    for label in ("phishing", "legit"):
        counts = {v: sum(r["label"] == label and r["verdict"] == v for r in ok) for v in ("Safe", "Suspicious", "Phishing")}
        print(f"  {label:9} " + "  ".join(f"{v}: {n}" for v, n in counts.items()))

    for column in ("type", "source"):
        print(f"\nAccuracy by {column}")
        for value in sorted({r[column] for r in ok}):
            group = [r for r in ok if r[column] == value]
            print(f"  {value:9} {percent(sum(r['correct'] for r in group), len(group))}")

    print("\nPer scan (average)")
    print(f"  Latency (s):     {average([r['latency_s'] for r in ok])}")
    print(f"  Input tokens:    {average([r['input_tokens'] for r in ok])}  (of which image: {average([r['image_tokens'] for r in ok])})")
    print(f"  Output tokens:   {average([r['output_tokens'] for r in ok])}")
    print(f"  Thinking tokens: {average([r['thinking_tokens'] for r in ok])}")
    costs = [r["cost_usd"] for r in ok if r["cost_usd"] is not None]
    if costs:
        print(f"  Cost (USD):      {sum(costs) / len(costs):.6f}")
    else:
        print(f"  Cost (USD):      prices for {model} are not set in PRICES_PER_1M")


def write_results(results: list[dict], output: Path) -> None:
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PhishGuard on the labeled image set.")
    parser.add_argument("--model", default=MODEL_NAME, help=f"Gemini model (default: {MODEL_NAME})")
    parser.add_argument("--language", default="he", choices=sorted(SUPPORTED_LANGUAGES), help="Answer language (default: he)")
    parser.add_argument("--delay", type=float, default=5.0, help="Seconds to wait between calls, for free-tier limits (default: 5)")
    parser.add_argument("--limit", type=int, help="Only run the first N images, for a quick test")
    parser.add_argument("--dir", type=Path, default=EVAL_DIR, help="Folder with labels.csv and images/, e.g. eval/holdout (default: eval/)")
    parser.add_argument("--output", type=Path, help="Results file (default: results.csv in --dir, or results_<model>.csv for other models)")
    args = parser.parse_args()

    if not gemini_service.is_available():
        sys.exit("GEMINI_API_KEY is not set. Put it in server-phishGuard/.env like for the server.")

    images_dir = args.dir / "images"
    rows = load_labels(args.dir / "labels.csv", images_dir)[: args.limit]
    output = args.output or args.dir / ("results.csv" if args.model == MODEL_NAME else f"results_{args.model}.csv")

    results = []
    for i, row in enumerate(rows, start=1):
        if i > 1:
            await asyncio.sleep(args.delay)
        result = await evaluate_image(row, images_dir, args.model, args.language)
        results.append(result)
        outcome = f"ERROR {result['error']}" if result["error"] else f"{result['verdict']} ({result['score']})"
        print(f"[{i}/{len(rows)}] {row['filename']:32} {row['label']:9} -> {outcome}  {result.get('latency_s', '')}s")

    write_results(results, output)
    print_summary(results, args.model)
    print(f"\nSaved {output}")


if __name__ == "__main__":
    asyncio.run(main())
