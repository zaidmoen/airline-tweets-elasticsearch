#!/usr/bin/env python3
"""Clean airline tweets and load them into Elasticsearch."""

import argparse
import csv
import html
import json
import re
import sys
from datetime import datetime


INDEX_SETTINGS = {"number_of_shards": 1, "number_of_replicas": 0}
INDEX_MAPPINGS = {
    "dynamic": "strict",
    "properties": {
        "tweet_id": {"type": "keyword"},
        "text": {
            "type": "text",
            "analyzer": "english",
            "fields": {"std": {"type": "text", "analyzer": "standard"}},
        },
        "airline": {"type": "keyword"},
        "airline_sentiment": {"type": "keyword"},
        "airline_sentiment_confidence": {"type": "float"},
        "negativereason": {"type": "keyword"},
        "negativereason_confidence": {"type": "float"},
        "user_name": {"type": "keyword"},
        "retweet_count": {"type": "integer"},
        "created_at": {"type": "date"},
        "user_location": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
        },
        "user_timezone": {"type": "keyword"},
        "hashtags": {"type": "keyword"},
        "mentions": {"type": "keyword"},
        "location": {"type": "geo_point"},
        "has_location": {"type": "boolean"},
    },
}

HASHTAG_RE = re.compile(r"#(\w+)")
MENTION_RE = re.compile(r"@(\w+)")


def clean(value):
    """Return stripped text, or None for an empty cell."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def to_float(value):
    value = clean(value)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_int(value):
    value = clean(value)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def parse_coord(value):
    """Convert a valid [latitude, longitude] cell into an Elasticsearch point."""
    value = clean(value)
    if value is None:
        return None
    try:
        parts = value.strip().strip("[]").split(",")
        if len(parts) != 2:
            return None
        lat, lon = float(parts[0]), float(parts[1])
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    if lat == 0.0 and lon == 0.0:
        return None
    return {"lat": lat, "lon": lon}


def parse_date(value):
    """Return the timestamp in ISO 8601 format, preserving its UTC offset."""
    value = clean(value)
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z").isoformat()
    except ValueError:
        return None


def row_to_doc(row):
    """Map a CSV row to the fields allowed by the strict index mapping."""
    raw_text = clean(row.get("text"))
    tweet_text = html.unescape(raw_text) if raw_text is not None else None
    hashtags = list(dict.fromkeys(tag.lower() for tag in HASHTAG_RE.findall(tweet_text or "")))
    mentions = list(dict.fromkeys(name.lower() for name in MENTION_RE.findall(tweet_text or "")))
    location = parse_coord(row.get("tweet_coord"))

    values = {
        "tweet_id": clean(row.get("tweet_id")),
        "text": tweet_text,
        "airline": clean(row.get("airline")),
        "airline_sentiment": clean(row.get("airline_sentiment")),
        "airline_sentiment_confidence": to_float(row.get("airline_sentiment_confidence")),
        "negativereason": clean(row.get("negativereason")),
        "negativereason_confidence": to_float(row.get("negativereason_confidence")),
        "user_name": clean(row.get("name")),
        "retweet_count": to_int(row.get("retweet_count")),
        "created_at": parse_date(row.get("tweet_created")),
        "user_location": clean(row.get("tweet_location")),
        "user_timezone": clean(row.get("user_timezone")),
        "hashtags": hashtags or None,
        "mentions": mentions or None,
        "location": location,
        "has_location": location is not None,
    }
    return {key: value for key, value in values.items() if value is not None}


def generate_actions(csv_path, index_name, stats):
    """Yield index actions using tweet IDs so reruns replace the same documents."""
    with open(csv_path, newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            stats["read"] += 1
            document = row_to_doc(row)
            tweet_id = document.get("tweet_id")
            if not tweet_id:
                stats["skipped"] += 1
                continue
            if document["has_location"]:
                stats["with_location"] += 1
            yield {
                "_op_type": "index",
                "_index": index_name,
                "_id": tweet_id,
                "_source": document,
            }


def connect(args):
    from elasticsearch import Elasticsearch

    options = {"request_timeout": 60}
    if args.api_key:
        options["api_key"] = args.api_key
    elif args.user:
        options["basic_auth"] = (args.user, args.password or "")
    if args.ca_cert:
        options["ca_certs"] = args.ca_cert
    client = Elasticsearch(args.es_url, **options)
    info = client.info()
    print(f"Connected to cluster '{info['cluster_name']}', Elasticsearch {info['version']['number']}")
    return client


def prepare_index(client, index_name, recreate):
    """Create the index with its explicit mapping, optionally starting fresh."""
    if recreate and client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
    if not client.indices.exists(index=index_name):
        client.indices.create(
            index=index_name,
            settings=INDEX_SETTINGS,
            mappings=INDEX_MAPPINGS,
        )


def dry_run(args):
    stats = {"read": 0, "skipped": 0, "with_location": 0}
    with open(args.dry_run, "w", encoding="utf-8") as output:
        for action in generate_actions(args.csv, args.index, stats):
            header = {"index": {"_index": action["_index"], "_id": action["_id"]}}
            output.write(json.dumps(header) + "\n")
            output.write(json.dumps(action["_source"], ensure_ascii=False) + "\n")
    print(
        f"Rows read: {stats['read']}, skipped: {stats['skipped']}, "
        f"with valid coordinates: {stats['with_location']}"
    )
    print(f"Bulk body written to {args.dry_run}")


def main():
    parser = argparse.ArgumentParser(description="Bulk-index geotagged airline tweets.")
    parser.add_argument("--csv", required=True, help="path to Tweets.csv")
    parser.add_argument("--index", default="tweets", help="index name")
    parser.add_argument("--es-url", default="http://localhost:9200")
    parser.add_argument("--user", help="Elasticsearch username")
    parser.add_argument("--password", help="Elasticsearch password")
    parser.add_argument("--api-key", help="encoded API key")
    parser.add_argument("--ca-cert", help="CA certificate for HTTPS")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--recreate", action="store_true", help="delete and recreate the index")
    parser.add_argument("--dry-run", metavar="FILE", help="write bulk NDJSON without connecting")
    args = parser.parse_args()

    if args.chunk_size < 1:
        parser.error("--chunk-size must be greater than zero")
    if args.dry_run:
        dry_run(args)
        return

    from elasticsearch import helpers

    client = connect(args)
    prepare_index(client, args.index, args.recreate)
    stats = {"read": 0, "skipped": 0, "with_location": 0}
    indexed = failed = 0
    shown_failures = 0
    for success, result in helpers.streaming_bulk(
        client,
        generate_actions(args.csv, args.index, stats),
        chunk_size=args.chunk_size,
        raise_on_error=False,
    ):
        if success:
            indexed += 1
        else:
            failed += 1
            if shown_failures < 5:
                print(f"Bulk item failed: {result}", file=sys.stderr)
                shown_failures += 1

    client.indices.refresh(index=args.index)
    count = client.count(index=args.index)["count"]
    print(
        f"Rows read: {stats['read']}, skipped: {stats['skipped']}, "
        f"indexed: {indexed}, failed: {failed}, "
        f"with valid coordinates: {stats['with_location']}"
    )
    print(f"Documents now in '{args.index}': {count}")


if __name__ == "__main__":
    main()
