"""Build the four-page report from saved Elasticsearch evidence."""

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "evidence"
RESULTS = json.loads((EVIDENCE / "results.json").read_text())
VERIFY = json.loads((EVIDENCE / "verification.json").read_text())
WIDTH, HEIGHT = A4
MARGIN = 42
BODY = WIDTH - 2 * MARGIN

INK = colors.HexColor("#19303B")
MUTED = colors.HexColor("#607480")
TEAL = colors.HexColor("#187D79")
NEGATIVE = colors.HexColor("#BC6551")
NEUTRAL = colors.HexColor("#BFCBD0")
PALE = colors.HexColor("#EDF4F3")
PAPER = colors.HexColor("#FDFCF9")
LINE = colors.HexColor("#D7E0E2")
WHITE = colors.white

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
for name, file in [
    ("Sans", "DejaVuSans.ttf"), ("Sans-Bold", "DejaVuSans-Bold.ttf"),
    ("Serif", "DejaVuSerif.ttf"), ("Mono", "DejaVuSansMono.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")


def p(text, x, top, width, size=9.1, leading=None, color=INK, font="Sans", align=TA_LEFT):
    """Draw a paragraph using a position measured from the top."""
    style = ParagraphStyle(
        "body", fontName=font, fontSize=size, leading=leading or size * 1.45,
        textColor=color, alignment=align, spaceBefore=0, spaceAfter=0,
    )
    item = Paragraph(text, style)
    _, height = item.wrap(width, HEIGHT)
    item.drawOn(C, x, HEIGHT - top - height)
    return top + height


def rect(x, top, width, height, fill, stroke=None):
    C.setFillColor(fill)
    C.setStrokeColor(stroke or fill)
    C.rect(x, HEIGHT - top - height, width, height, fill=1, stroke=bool(stroke))


def rule(top, x=MARGIN, width=BODY, color=LINE):
    C.setStrokeColor(color)
    C.setLineWidth(0.5)
    C.line(x, HEIGHT - top, x + width, HEIGHT - top)


def label(text, top, x=MARGIN, width=BODY):
    p(text, x, top, width, 8, color=TEAL, font="Sans-Bold")


def section(code, title, top, x=MARGIN, width=BODY):
    p(code, x, top + 1, 33, 9, color=TEAL, font="Sans-Bold")
    p(title, x + 35, top, width - 35, 11, font="Sans-Bold")


def table(headers, rows, widths, x, top, size=8.1, padding=6, min_height=23, right=()):
    """Use light horizontal rules so dense results remain readable."""
    total_width = sum(widths)
    for row_i, row in enumerate([headers] + rows):
        is_header = row_i == 0
        styles, heights = [], []
        for i, value in enumerate(row):
            style = ParagraphStyle(
                "cell", fontName="Sans-Bold" if is_header else "Sans",
                fontSize=size - 0.2 if is_header else size,
                leading=size * 1.32, textColor=INK,
                alignment=TA_RIGHT if i in right else TA_LEFT,
            )
            cell = Paragraph(str(value), style)
            _, height = cell.wrap(widths[i] - 2 * padding, HEIGHT)
            styles.append(cell)
            heights.append(height)
        row_height = max(min_height, max(heights) + 2 * padding)
        if is_header:
            rect(x, top, total_width, row_height, PALE)
        elif row_i % 2 == 0:
            rect(x, top, total_width, row_height, colors.HexColor("#F6F8F6"))
        left = x
        for i, cell in enumerate(styles):
            cell.drawOn(C, left + padding, HEIGHT - top - padding - heights[i])
            left += widths[i]
        top += row_height
        rule(top, x, total_width)
    return top


def page(number, topic):
    rect(0, 0, WIDTH, HEIGHT, PAPER)
    rect(MARGIN, 30, 28, 3, TEAL)
    p("AIRLINE TWEET ANALYSIS", MARGIN + 38, 27, 220, 7.7, font="Sans-Bold")
    p(topic.upper(), WIDTH - MARGIN - 235, 27, 235, 7.5, color=MUTED, align=TA_RIGHT)
    rule(51)
    rule(792)
    p("Zaid Mayyalleh  /  Elasticsearch activity", MARGIN, 803, 340, 7.3, color=MUTED)
    p(f"{number} / 4", WIDTH - MARGIN - 55, 801, 55, 8.5, color=TEAL, font="Sans-Bold", align=TA_RIGHT)


def heading(title, subtitle):
    p(title, MARGIN, 73, BODY, 27, leading=32, font="Serif")
    p(subtitle, MARGIN, 114, BODY, 9.1, color=MUTED)


def hits(query):
    return RESULTS[query]["hits"]["hits"]


def buckets(query, name):
    return RESULTS[query]["aggregations"][name]["buckets"]


def excerpt(text, limit):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "..."
    return escape(text)


def first_page():
    page(1, "Dataset & method")
    p("Airline Tweet Analysis", MARGIN, 73, BODY, 30, leading=36, font="Serif")
    p("Text search, sentiment and geospatial patterns in Elasticsearch", MARGIN, 119, BODY, 10.2, color=MUTED)
    p("Zaid Mayyalleh  |  Computer Science  |  An-Najah National University", MARGIN, 145, BODY, 8.5)
    p("Dataset: February 2015  ·  Verified: 28 October 2026  ·  Elasticsearch 9.5.5", MARGIN, 162, BODY, 8.2, color=MUTED)

    metrics = [("14,640", "SOURCE ROWS"), ("14,485", "INDEX DOCUMENTS"), ("62.74%", "NEGATIVE SENTIMENT")]
    for i, (value, name) in enumerate(metrics):
        x = MARGIN + i * BODY / 3
        rect(x, 194, BODY / 3 - 8, 66, PALE)
        p(value, x + 12, 203, BODY / 3 - 28, 22, leading=27, font="Serif", color=TEAL)
        p(name, x + 12, 239, BODY / 3 - 26, 7.1, font="Sans-Bold", color=MUTED)

    p("This study loads airline sentiment tweets into a strict Elasticsearch index and answers "
      "14 search, aggregation and geographic questions. Negative tweets account for 9,088 of "
      "14,485 documents. United has the largest volume, while the busiest day is 22 February. "
      "All query results below come from a successful live run; only 5.85% of documents have a valid location.",
      MARGIN, 278, BODY, 9.1)

    section("A1", "Dataset and preparation", 353)
    table(["CSV inspection", "Rows"], [
        ["Total rows", "14,640"], ["Non-empty tweet_coord", "1,019"],
        ["Placeholder [0.0, 0.0]", "164"], ["Valid coordinate rows", "855"],
    ], [183, 60], MARGIN, 379, size=8.4, min_height=23, right=(1,))
    x = MARGIN + 265
    p("Explicit mapping &amp; cleaning", x, 380, 245, 9.2, font="Sans-Bold")
    p("One shard, zero replicas and <b>dynamic: strict</b>. Text uses the English analyzer; "
      "airline, sentiment and hashtags are keywords. Dates use ISO 8601 and coordinates use "
      "<b>geo_point</b>. HTML is unescaped, tags are lowercased, and empty cells are omitted.",
      x, 402, 245, 8.5, leading=12.4)
    p("The CSV contains 155 repeated-ID surplus rows. Using tweet_id as _id replaces earlier copies, "
      "leaving 14,485 documents and 847 unique geotagged tweets.", MARGIN, 509, BODY, 8.6, color=MUTED)

    section("B1", "Observed indexing output", 548)
    rect(MARGIN, 576, BODY, 87, INK)
    lines = (EVIDENCE / "indexer-output.txt").read_text().splitlines()
    for i, line in enumerate(lines):
        p(escape(line), MARGIN + 12, 586 + i * 13, BODY - 24, 7.7, leading=10, color=WHITE, font="Mono")
    p('GET /tweets/_count  →  {"count": 14485, "_shards":', MARGIN + 12, 630, BODY - 24, 7.6, leading=10, color=WHITE, font="Mono")
    p('{"total": 1, "successful": 1, "skipped": 0, "failed": 0}}', MARGIN + 12, 643, BODY - 24, 7.6, leading=10, color=WHITE, font="Mono")
    p('Live evidence: <link href="' + VERIFY["workflow_url"] + '" color="#187D79">successful workflow run</link>. '
      'The sample dry run also read 5 rows, skipped 0, and kept 2 valid locations.', MARGIN, 670, BODY, 7.8, color=MUTED)

    section("B2", "Why these choices?", 702)
    p("The Bulk API groups 500 indexing actions per request, reducing network overhead. "
      "Using tweet_id as _id lets later rows and repeated runs update the same document. "
      "The point [0.0, 0.0] is removed because it is a missing-location placeholder that would distort "
      "distance and map results. Tweets without a valid point are kept with has_location set to false.",
      MARGIN, 728, BODY, 8.8, leading=12.5)
    C.showPage()


def search_page():
    page(2, "Search results · Q1-Q5")
    heading("Search results", "Exact filters, analyzed text and ranked tweet examples")

    cards = [
        ("Q1", "9,088", "negative tweets", "2,633 are labelled United*"),
        ("Q3", "91", "positive phrase matches", 'English-analyzed “customer service”'),
        ("Q4", "25", "Delta late-flight complaints", "23 February 2015 · Pacific time"),
    ]
    for i, (code, value, name, note) in enumerate(cards):
        x = MARGIN + i * BODY / 3
        rect(x, 147, BODY / 3 - 8, 103, PALE)
        label(code, 156, x + 11, 140)
        p(value, x + 11, 174, 145, 24, font="Serif", color=TEAL, leading=28)
        p(name, x + 11, 205, BODY / 3 - 29, 8.2, font="Sans-Bold")
        p(note, x + 11, 222, BODY / 3 - 29, 7.2, leading=10, color=MUTED)
    p("*Q1 filters the dataset's airline label. Q4 filters negative sentiment, Delta and Late Flight within "
      "[23 Feb 00:00, 24 Feb 00:00), America/Los_Angeles. Original airline labels are retained.",
      MARGIN, 259, BODY, 7.8, leading=11.3, color=MUTED)

    section("Q2", "Lost or delayed baggage", 298)
    p("231 matches. Two required match clauses combine a baggage term with a loss or delay term. "
      "The five most recent hits are shown below; ties use tweet_id ascending.", MARGIN, 321, BODY, 8.5, leading=12)
    rows = []
    for hit in hits("q2"):
        source = hit["_source"]
        rows.append([source["airline"], source["airline_sentiment"], excerpt(source["text"], 200)])
    end = table(["Airline", "Sentiment", "Tweet text"], rows, [78, 65, BODY - 143], MARGIN, 354,
                size=8.0, padding=4, min_height=22)
    p("Original wording with whitespace normalized. English analysis matches terms even when they are not adjacent.",
      MARGIN, end + 7, BODY, 7.3, color=MUTED)

    top = end + 35
    section("Q5", "The five most-retweeted tweets", top)
    rows = []
    for hit in hits("q5"):
        source = hit["_source"]
        rows.append([source["airline"], str(source["retweet_count"]), excerpt(source["text"], 108)])
    bottom = table(["Airline", "Retweets", "Tweet excerpt"], rows, [78, 65, BODY - 143], MARGIN,
                   top + 26, size=8.0, padding=4, min_height=22, right=(1,))
    p("Sorted by retweet_count descending, then tweet_id ascending. The requested _source fields are text, airline and retweet_count.",
      MARGIN, bottom + 8, BODY, 7.5, leading=11, color=MUTED)
    if bottom + 30 > 788:
        raise ValueError(f"Search page is too long: {bottom}")
    C.showPage()


def sentiment_table(top):
    rows = buckets("q6", "airlines")
    widths = [100, 47, 55, 50, 50, BODY - 302]
    table(["Airline", "Total", "Negative", "Neutral", "Positive", "Sentiment share"], [], widths,
          MARGIN, top, size=7.4, padding=5, min_height=24, right=(1, 2, 3, 4))
    top += 24
    for index, row in enumerate(rows):
        if index % 2:
            rect(MARGIN, top, BODY, 24, colors.HexColor("#F6F8F6"))
        sentiment = {b["key"]: b["doc_count"] for b in row["sentiments"]["buckets"]}
        values = [row["key"], f'{row["doc_count"]:,}'] + [f'{sentiment[s]:,}' for s in ["negative", "neutral", "positive"]]
        x = MARGIN
        for i, value in enumerate(values):
            p(escape(value), x + 5, top + 6, widths[i] - 10, 8, align=TA_LEFT if i == 0 else TA_RIGHT)
            x += widths[i]
        bar_width = widths[-1] - 12
        for sentiment_name, color in [("negative", NEGATIVE), ("neutral", NEUTRAL), ("positive", TEAL)]:
            width = bar_width * sentiment[sentiment_name] / row["doc_count"]
            rect(x + 6, top + 7, width, 10, color)
            x += width
        rule(top + 24)
        top += 24
    x = MARGIN + 302
    for name, color, width in [("Negative", NEGATIVE, 72), ("Neutral", NEUTRAL, 65), ("Positive", TEAL, 68)]:
        rect(x + 6, top + 8, 6, 6, color)
        p(name, x + 16, top + 5, width - 16, 7.2, color=MUTED)
        x += width


def daily_chart(x, top, width):
    daily = buckets("q8", "tweets_per_day")
    base = top + 99
    unit = width / len(daily)
    rule(base, x, width)
    for i, row in enumerate(daily):
        value = row["doc_count"]
        height = value / 3200 * 80
        left = x + i * unit
        rect(left + 6, base - max(height, 1), unit - 12, max(height, 1), TEAL if value == 3073 else NEUTRAL)
        p(f"{value:,}", left - 1, base - height - 17, unit + 2, 6.8, font="Sans-Bold", align=TA_CENTER)
        p(row["key_as_string"][8:10], left, base + 7, unit, 7.5, color=MUTED, align=TA_CENTER)
    p("February 2015 · Pacific time", x, base + 26, width, 7.4, color=MUTED)
    p("22 February was busiest: <b>3,073 tweets</b>. The first and last dates are partial days in this dataset.",
      x, base + 47, width, 8.1, leading=11.7)


def aggregation_page():
    page(3, "Aggregations · Q6-Q9")
    heading("Patterns across airlines", "Counts describe this tweet sample, using the original sentiment labels.")
    section("Q6", "Tweet volume and sentiment", 147)
    sentiment_table(174)
    p("United has the most tweets (3,822). US Airways has the highest negative share (77.69%).", MARGIN, 362, BODY, 8.2, color=MUTED)

    section("Q7", "Top three negative reasons per airline", 390)
    rows = []
    for row in buckets("q7", "airlines"):
        rows.append([row["key"]] + [escape(b["key"]) + f' <b>({b["doc_count"]:,})</b>' for b in row["reasons"]["buckets"]])
    table(["Airline", "1st reason", "2nd reason", "3rd reason"], rows,
          [87, (BODY - 87) / 3, (BODY - 87) / 3, (BODY - 87) / 3], MARGIN, 415,
          size=7.5, padding=5, min_height=22)

    left_width = 289
    right_x = MARGIN + left_width + 22
    right_width = BODY - left_width - 22
    section("Q8", "Daily activity", 589, width=left_width)
    daily_chart(MARGIN, 611, left_width)
    section("Q9", "Top hashtags", 589, x=right_x, width=right_width)
    rows = [["#" + row["key"], str(row["doc_count"])] for row in buckets("q9", "top_hashtags")]
    table(["Hashtag", "Docs"], rows, [right_width - 35, 35], right_x, 613,
          size=7.5, padding=2.2, min_height=13.3, right=(1,))
    C.showPage()


def geo_page():
    page(4, "Geographic analysis · Q10-Q14")
    heading("Where tweets originate", "Location coverage is sparse; geographic findings apply to geotagged tweets only.")
    section("Q10", "Location coverage", 150)
    p("<b>847 of 14,485 documents (5.85%)</b> have a valid geo_point. The remaining 13,638 tweets "
      "are retained for text and sentiment analysis.", MARGIN, 175, BODY, 9.1)

    section("Q11", "Within 25 km of JFK", 219)
    p("83 hits around (40.6413, -73.7781). First five results, sorted by arc distance:", MARGIN, 242, BODY, 8.5)
    rows = [[f'{hit["sort"][0]:.3f}', hit["_source"]["airline"], hit["_source"]["airline_sentiment"], hit["_id"]] for hit in hits("q11")]
    table(["Distance (km)", "Airline", "Sentiment", "Tweet ID"], rows,
          [83, 110, 85, BODY - 278], MARGIN, 266, size=8.1, padding=5, min_height=22, right=(0,))

    half = (BODY - 24) / 2
    right_x = MARGIN + half + 24
    section("Q12", "California box", 418, width=half)
    p("80 negative tweets. United leads with 43.", MARGIN, 441, half, 8.3)
    ca_rows = [[b["key"], str(b["doc_count"])] for b in buckets("q12", "airlines")]
    table(["Airline", "Negative"], ca_rows, [half - 65, 65], MARGIN, 463,
          size=8.0, padding=4, min_height=20, right=(1,))
    p("Box: 32.5° to 42.0° N; 124.5° to 114.1° W.", MARGIN, 610, half, 7.4, color=MUTED)

    section("Q13", "O'Hare distance rings", 418, x=right_x, width=half)
    p("Origin: (41.9742, -87.9073). All 847 geotweets.", right_x, 441, half, 8.3)
    rings = buckets("q13", "distance_rings")
    rows = [[name, str(row["doc_count"]), f'{100 * row["doc_count"] / 847:.2f}%']
            for name, row in zip(["0 ≤ km &lt; 50", "50 ≤ km &lt; 500", "km ≥ 500"], rings)]
    table(["Ring", "Tweets", "Share"], rows, [half - 111, 51, 60], right_x, 463,
          size=8.0, padding=4, min_height=23, right=(1, 2))
    p("776 tweets (91.62%) are at least 500 km away. Range upper bounds are exclusive; the last bucket includes 500 km.",
      right_x, 568, half, 8.0, leading=11.5, color=MUTED)

    section("Q14", "Busiest map cells and negative centroid", 641)
    tiles = buckets("q14", "busiest_cells")
    # Show tied cells in the order returned by Elasticsearch.
    cell_text = " &nbsp; · &nbsp; ".join(f'<b>{b["key"]}</b>: {b["doc_count"]}' for b in tiles)
    p("Geotile precision 6 (zoom/x/y), ranked by document count:", MARGIN, 664, BODY, 8.3)
    p(cell_text, MARGIN, 681, BODY, 8.4, leading=13)
    centroid = RESULTS["q14"]["aggregations"]["negative_centroid"]["center"]
    lat, lon = centroid["location"]["lat"], centroid["location"]["lon"]
    rect(MARGIN, 707, BODY, 34, PALE)
    p(f'Negative centroid: <b>({lat:.6f}, {lon:.6f})</b> · {centroid["count"]} geotagged negative tweets',
      MARGIN + 10, 717, BODY - 20, 8.8)

    p('<b>Sources &amp; reproducibility.</b> [1] <link href="' + VERIFY["dataset_url"] + '" color="#187D79">CrowdFlower, Twitter US Airline Sentiment</link> '
      '(2015), CC BY-NC-SA 4.0. [2] Elastic reference: '
      '<link href="https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-match-query" color="#187D79">match query</link>; '
      '<link href="https://www.elastic.co/docs/reference/aggregations/search-aggregations-metrics-geocentroid-aggregation" color="#187D79">geo-centroid</link>. '
      '[3] <link href="https://github.com/zaidmoen/airline-tweets-elasticsearch/blob/main/queries.txt" color="#187D79">Submitted queries</link> and '
      '<link href="https://github.com/zaidmoen/airline-tweets-elasticsearch/tree/main/docs/evidence" color="#187D79">saved live responses</link>. '
      'Verified 28 Oct 2026; source commit 9d19eaf. Centroid is the coordinate mean, not an airport or a complaint-rate measure.',
      MARGIN, 751, BODY, 7.0, leading=9.2, color=MUTED)
    C.showPage()


def main():
    global C
    output = ROOT / "report.pdf"
    C = canvas.Canvas(str(output), pagesize=A4, pageCompression=1)
    C.setTitle("Airline Tweet Analysis - Elasticsearch Activity Report")
    C.setAuthor("Zaid Mayyalleh")
    C.setSubject("A1, B1, B2 and Q1-Q14 with verified Elasticsearch 9.5.5 responses")
    first_page()
    search_page()
    aggregation_page()
    geo_page()
    C.save()
    print(output)


if __name__ == "__main__":
    main()
