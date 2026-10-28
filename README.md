# Repo suggestion

**Repository name:** `airline-tweets-elasticsearch`

**Description:** A Python bulk indexer and Elasticsearch queries for exploring airline sentiment tweets, including geospatial analysis.

## Files

- `tweets_indexer.py` cleans the CSV and indexes it with Elasticsearch 9.
- `queries.txt` contains all 14 Kibana Console queries.
- `report.pdf` summarizes the dataset and indexing approach and provides a place to record live Elasticsearch results.

## Run

```bash
pip install -r requirements.txt
python tweets_indexer.py --csv sample_tweets.csv --dry-run preview.ndjson
python tweets_indexer.py --csv Tweets.csv --es-url http://localhost:9200 --user elastic --password "YOUR_PASSWORD" --recreate
```

Use `--ca-cert PATH` for HTTPS with a CA certificate, or `--api-key KEY` for API key authentication. Query results in the report must be filled from the Elasticsearch instance where the full dataset is indexed.
