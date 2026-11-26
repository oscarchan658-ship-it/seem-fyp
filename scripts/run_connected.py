"""Prompt for a key without echo, run fixed fictional cases, optionally serve app."""

import argparse
import getpass
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from terra_client import TerraClient, SENTIMENT_PROMPT
from research.sentiment_pilot import cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    key = getpass.getpass("API key (hidden; not saved): ")
    client = TerraClient(key, args.base_url)
    try:
        label, meta = client.sentiment("This fictional example describes a happy day.")
        print("Connection:", label, meta, flush=True)
    except Exception as e:
        print("Connection failed:", str(e), flush=True)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    data = cases()
    (args.output / "cases.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in data)
    )
    (args.output / "prompt.txt").write_text(SENTIMENT_PROMPT)

    def predict(case):
        try:
            value, metadata = client.sentiment(case["text"])
            return {**case, "predicted": value, **metadata, "error": None}
        except Exception as e:
            return {**case, "predicted": None, "error": str(e)}

    with (args.output / "predictions.jsonl").open("w") as f:
        for i, row in enumerate(ThreadPoolExecutor(2).map(predict, data), 1):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"Completed {i}/{len(data)}", flush=True)
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "requested_model": "gpt-6.1-terra",
                "base_url": args.base_url,
                "mode": "AI-authored diagnostic; not clinical or independent gold",
                "n": len(data),
                "repetitions": 1,
                "reasoning_effort": "low",
                "store": False,
            },
            indent=2,
        )
    )
    if args.serve:
        os.environ["FYP_API_KEY"] = key
        os.environ["FYP_API_BASE"] = args.base_url
        os.execv(
            sys.executable,
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                "8501",
                "--server.address",
                "127.0.0.1",
                "--server.headless",
                "true",
            ],
        )


if __name__ == "__main__":
    main()
