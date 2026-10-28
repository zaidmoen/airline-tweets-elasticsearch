# Results Summary

These values were calculated from the complete Twitter US Airline Sentiment
CSV after applying the indexer's last-write-wins behavior for repeated
`tweet_id` values.

## Dataset and indexing

| Metric | Value |
| --- | ---: |
| Source rows | 14,640 |
| Repeated tweet IDs | 155 |
| Unique indexed documents | 14,485 |
| Non-empty coordinate rows | 1,019 |
| Placeholder `[0.0, 0.0]` rows | 164 |
| Valid geotagged documents after ID updates | 847 |

## Query results

| Query | Key result |
| --- | --- |
| Q1 | 9,088 negative tweets; 2,633 are about United. |
| Q2 | 1,925 tweets match the luggage and bag search. |
| Q3 | 90 positive tweets contain the phrase `customer service`. |
| Q4 | 25 negative Delta late-flight tweets were posted on February 23, 2015, Pacific time. |
| Q5 | Top retweet counts: 44, 32, 31, 28, and 22. |
| Q8 | February 22 was the busiest day with 3,073 tweets. |
| Q10 | 847 of 14,485 documents are geotagged: 5.85%. |
| Q11 | 83 tweets are within 25 km of JFK. |
| Q12 | United leads the negative California geotweets with 43. |
| Q13 | O'Hare rings: 47 within 50 km, 24 within 50-500 km, and 776 over 500 km. |
| Q14 | Negative geotweet centroid: `39.1647, -89.0527`. |

## Tweets by airline and sentiment

| Airline | Total | Negative | Neutral | Positive |
| --- | ---: | ---: | ---: | ---: |
| American | 2,604 | 1,870 | 429 | 305 |
| Delta | 2,222 | 955 | 723 | 544 |
| Southwest | 2,420 | 1,186 | 664 | 570 |
| US Airways | 2,913 | 2,263 | 381 | 269 |
| United | 3,822 | 2,633 | 697 | 492 |
| Virgin America | 504 | 181 | 171 | 152 |

## Most frequent hashtags

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

The completed [`report.pdf`](../report.pdf) contains the full answers and
examples for Q1-Q14. The executable query bodies are in
[`queries.txt`](../queries.txt).
