"""Fetch a pinned public benchmark; raw text stays ignored by Git."""

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

SHA = "4fbd22cd78421f05b1ecdb4fc5725bc7a7bd8f66"
root = Path("data/tweeteval")
root.mkdir(parents=True, exist_ok=True)
manifest = {}
for split in ("train", "val", "test"):
    for kind in ("text", "labels"):
        name = f"{split}_{kind}.txt"
        url = f"https://raw.githubusercontent.com/cardiffnlp/tweeteval/{SHA}/datasets/sentiment/{name}"
        data = urlopen(url, timeout=30).read()
        (root / name).write_bytes(data)
        manifest[name] = dict(
            url=url,
            sha256=hashlib.sha256(data).hexdigest(),
            lines=len(data.splitlines()),
        )
(root / "manifest.json").write_text(
    json.dumps(dict(commit=SHA, files=manifest), indent=2)
)
print(
    "Downloaded pinned TweetEval splits. See data/tweeteval/README.md for upstream context."
)
