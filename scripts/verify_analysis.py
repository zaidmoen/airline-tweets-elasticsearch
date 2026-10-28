"""Run the activity against a local Elasticsearch service and save evidence."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
DATA_URL = (
    "https://huggingface.co/datasets/osanseviero/"
    "twitter-airline-sentiment/resolve/main/Tweets.csv"
)
DATA_SHA256 = "ea94b23f41892b290dec3330bb8cf9cb6b8bc669eaae5f3a84c40f7b0de8f15e"


def request(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = Request(
        "http://localhost:9200" + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    with urlopen(req, timeout=120) as response:
        return json.load(response)


def main():
    EVIDENCE.mkdir(exist_ok=True)
    with urlopen(DATA_URL, timeout=120) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != DATA_SHA256:
        raise ValueError("The dataset changed. Review it before updating the report.")
    csv_path = EVIDENCE / "Tweets.csv"
    csv_path.write_bytes(data)

    # Save the real indexer output before querying the index.
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tweets_indexer.py"), "--csv", str(csv_path),
         "--es-url", "http://localhost:9200", "--recreate"],
        check=True, text=True, capture_output=True,
    )
    print(completed.stdout, end="")
    (EVIDENCE / "indexer.log").write_text(completed.stdout, encoding="utf-8")
    results = {"server": request("/"), "count": request("/tweets/_count")}
    (EVIDENCE / "mapping.json").write_text(
        json.dumps(request("/tweets/_mapping"), indent=2), encoding="utf-8"
    )

    # Use the submitted query bodies directly.
    query_text = (ROOT / "queries.txt").read_text(encoding="utf-8")
    blocks = list(re.finditer(r"(?m)^# Q(\d+)\b[^\n]*\nGET (/tweets/_search)\n", query_text))
    if len(blocks) != 14:
        raise ValueError("Expected exactly 14 activity queries.")
    for i, block in enumerate(blocks):
        end = blocks[i + 1].start() if i + 1 < len(blocks) else len(query_text)
        body = json.loads(query_text[block.end():end].strip())
        response = request(block.group(2), body)
        if response.get("timed_out") or response["_shards"]["failed"]:
            raise RuntimeError(f"Q{block.group(1)} did not finish successfully.")
        (EVIDENCE / f"q{block.group(1)}.json").write_text(
            json.dumps(response, indent=2), encoding="utf-8"
        )
        # Keep console evidence small; full responses are in the artifact.
        response["hits"]["hits"] = response["hits"]["hits"][:5]
        results["q" + block.group(1)] = response

    csv_path.unlink()  # The source dataset is available from its original host.
    (EVIDENCE / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("REPORT_RESULTS_JSON=" + json.dumps(results, ensure_ascii=True))


if __name__ == "__main__":
    main()
