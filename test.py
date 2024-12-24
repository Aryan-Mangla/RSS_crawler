import feedparser
import requests
import certifi

# Define the RSS feed URL and the number of articles to fetch
rss_feed_url = "https://feeds.feedburner.com/ndtvnews-top-stories"
article_limit = 20  # Change this value to fetch more or fewer articles

# Fetch the RSS feed with SSL verification using certifi
response = requests.get(rss_feed_url, verify=certifi.where())

# Parse the feed
feed = feedparser.parse(response.text)

# Check feed content
print("Feed Title:", feed.feed.get("title", "No Title"))
print("Number of Entries in Feed:", len(feed.entries))

# Extract and display article details
if len(feed.entries) > 0:
    articles = []
    for i, entry in enumerate(feed.entries[:article_limit]):
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary,
        })

    # Save articles to a JSON file
    import json
    with open('ndtv_articles.json', 'w') as f:
        json.dump(articles, f, indent=4)

    print(f"Saved {len(articles)} articles to ndtv_articles.json.")
else:
    print("No articles found in the RSS feed.")
