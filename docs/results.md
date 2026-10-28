# Verified activity results

The full dataset was indexed into **Elasticsearch 9.5.5**, then all 14 queries
were executed successfully on **28 October 2026**.
[Verification run](https://github.com/zaidmoen/airline-tweets-elasticsearch/actions/runs/40709322902)
uses commit `9d19eaf4ff9c0ddb80570559d91816741edc892d`.

The [four-page PDF report](../report.pdf) presents A1, B1, B2 and Q1-Q14.
The [query responses](evidence/results.json) are actual server responses,
with hit arrays limited to five examples for readability. The workflow artifact
contains the full responses. [Verification metadata](evidence/verification.json)
includes the dataset SHA-256 fingerprint.

## A1 and B1: dataset and indexing

| Metric | Value |
| --- | ---: |
| CSV rows | 14,640 |
| Non-empty coordinate rows | 1,019 |
| Placeholder `[0.0, 0.0]` rows | 164 |
| Valid coordinate rows | 855 |
| Repeated-ID surplus rows | 155 |
| Successful bulk actions | 14,640 |
| Failed bulk actions | 0 |
| Final index count | 14,485 |
| Unique geotagged documents | 847 |

Actual [indexer output](evidence/indexer-output.txt):

```text
Connected to cluster 'docker-cluster', Elasticsearch 9.5.5
Rows read: 14640, skipped: 0, indexed: 14640, failed: 0, with valid coordinates: 855
Documents now in 'tweets': 14485
```

`GET /tweets/_count` returned:

```json
{"count": 14485, "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0}}
```

Using `tweet_id` as `_id` means later duplicate rows replace earlier copies.
The number of successful bulk actions therefore exceeds the final document count.

## B2: indexing choices

The Bulk API groups 500 indexing actions per request, reducing network overhead.
Using `tweet_id` as `_id` makes repeated rows and repeated runs update the same
document. Removing `[0.0, 0.0]` prevents missing-location placeholders from
distorting geographic analysis. Tweets without a valid point are retained with
`has_location: false`.

## Q1-Q5: text and exact-value queries

| Query | Observed result |
| --- | --- |
| Q1 | 9,088 negative tweets; 2,633 have airline `United`. |
| Q2 | 231 hits requiring both a baggage term and a loss or delay term. Five most recent hits are in the PDF and JSON. |
| Q3 | 91 positive tweets match the English-analyzed phrase `customer service`. |
| Q4 | 25 negative Delta `Late Flight` tweets on 23 February 2015, Pacific time. |
| Q5 | Retweet counts: 44, 32, 31, 28 and 22, in that order. |

Q2 requires one match from `luggage bags baggage suitcase` and one from
`lost delayed missing`. Q3 uses the mapped English analyzer.
Original dataset airline labels are retained, including `Delta` on tweets
that mention `@JetBlue`.

## Q6: airline and sentiment counts

| Airline | Total | Negative | Neutral | Positive |
| --- | ---: | ---: | ---: | ---: |
| United | 3,822 | 2,633 | 697 | 492 |
| US Airways | 2,913 | 2,263 | 381 | 269 |
| American | 2,604 | 1,870 | 429 | 305 |
| Southwest | 2,420 | 1,186 | 664 | 570 |
| Delta | 2,222 | 955 | 723 | 544 |
| Virgin America | 504 | 181 | 171 | 152 |

US Airways has the highest negative share: 77.69%. These are shares within
this tweet dataset, not complaint rates per passenger or airline market shares.

## Q7: top three negative reasons

| Airline | First | Second | Third |
| --- | --- | --- | --- |
| United | Customer Service Issue (681) | Late Flight (525) | Can't Tell (379) |
| US Airways | Customer Service Issue (811) | Late Flight (453) | Can't Tell (246) |
| American | Customer Service Issue (741) | Late Flight (237) | Cancelled Flight (231) |
| Southwest | Customer Service Issue (391) | Cancelled Flight (162) | Can't Tell (159) |
| Delta | Late Flight (269) | Customer Service Issue (199) | Can't Tell (186) |
| Virgin America | Customer Service Issue (60) | Flight Booking Problems (28) | Can't Tell (22) |

## Q8: daily activity

Dates use `America/Los_Angeles`.

| Date (2015) | Tweets |
| --- | ---: |
| February 16 | 4 |
| February 17 | 1,408 |
| February 18 | 1,344 |
| February 19 | 1,376 |
| February 20 | 1,500 |
| February 21 | 1,557 |
| February 22 | 3,073 |
| February 23 | 3,026 |
| February 24 | 1,197 |

February 22 was busiest. The first and last dates are partial days in the source data.

## Q9: ten most frequent hashtags

| Hashtag | Documents |
| --- | ---: |
| `#destinationdragons` | 81 |
| `#fail` | 67 |
| `#jetblue` | 48 |
| `#unitedairlines` | 45 |
| `#customerservice` | 36 |
| `#usairways` | 28 |
| `#neveragain` | 27 |
| `#americanairlines` | 26 |
| `#united` | 26 |
| `#usairwaysfail` | 26 |

Hashtags are lowercased and counted once per document.

## Q10-Q14: geographic results

- **Q10:** 847 of 14,485 documents have a valid location: **5.85%**.
- **Q11:** 83 tweets are within 25 km of JFK, using arc distance from
  `(40.6413, -73.7781)`.
- **Q12:** The California box contains 80 negative tweets.
- **Q13:** O'Hare rings contain 47, 24 and 776 tweets.
- **Q14:** The centroid of 567 negative geotagged tweets is
  **`(37.16357098323189, -87.38189009890434)`** (latitude, longitude).

### Q11: five nearest tweets

| Distance (km) | Tweet ID | Airline | Sentiment |
| ---: | --- | --- | --- |
| 0.293 | `568611474416906240` | Delta | negative |
| 0.423 | `569967019958730753` | Virgin America | negative |
| 0.471 | `568216703055876096` | Delta | negative |
| 0.471 | `568204705861652480` | Delta | negative |
| 0.472 | `568196466503770112` | Delta | negative |

Distances are rounded for display; sorting uses the full precision returned by Elasticsearch.

### Q12: negative California tweets

| Airline | Tweets |
| --- | ---: |
| United | 43 |
| American | 13 |
| Southwest | 13 |
| US Airways | 6 |
| Delta | 4 |
| Virgin America | 1 |

The query uses a rectangle: latitude 32.5 to 42.0 and longitude -124.5 to -114.1.

### Q13: O'Hare rings

| Distance | Tweets |
| --- | ---: |
| 0 <= km < 50 | 47 |
| 50 <= km < 500 | 24 |
| km >= 500 | 776 |

Range upper bounds are exclusive; the final bucket includes 500 km.

### Q14: busiest cells

These are the actual response order at geotile precision 6 (`zoom/x/y`).

| Cell | Tweets |
| --- | ---: |
| `6/18/24` | 205 |
| `6/17/25` | 53 |
| `6/16/23` | 53 |
| `6/15/26` | 46 |
| `6/11/25` | 46 |

The centroid uses Elasticsearch's coordinate mean. Sparse location coverage
and the short time window limit what can be inferred about overall airline
service quality.
