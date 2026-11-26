"""Start the local demo with a hidden credential prompt; no benchmark calls."""

import argparse
import getpass
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://car.cheng-x.online/v1")
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parents[1])
    key = os.getenv("FYP_API_KEY") or getpass.getpass("API key (hidden): ")
    if not key:
        raise SystemExit("No API key supplied")
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
            "--server.address",
            "127.0.0.1",
            "--server.port",
            "8501",
            "--server.headless",
            "true",
        ],
    )


if __name__ == "__main__":
    main()
