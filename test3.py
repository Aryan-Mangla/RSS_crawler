import requests
from bs4 import BeautifulSoup
import feedparser
import json
from newsplease import NewsPlease
import certifi

# Function to fetch articles from a given RSS feed URL using news-please
def fetch_articles_from_feed(feed_url, article_limit=20):
    response = requests.get(feed_url, verify=certifi.where())  # Fetch the RSS feed with SSL verification
    feed = feedparser.parse(response.text)  # Parse the RSS feed

    articles = []
    for entry in feed.entries[:article_limit]:
        article_url = entry.link  # Extract article URL
        print(f"Fetching article from: {article_url}")
        
        # Extract full article content using news-please
        try:
            article = NewsPlease.from_url(article_url)

            # Dynamically structure the article data
            article_data = {
                'title': article.title,
                'link': article.url,
                'published': article.date_publish,
                'summary': article.description,
                'content': article.maintext,
            }

            # Add additional fields if available
            if article.language:
                article_data['language'] = article.language
            if article.authors:
                article_data['authors'] = article.authors
            if article.images:
                article_data['images'] = article.images
            if article.keywords:
                article_data['keywords'] = article.keywords
            if article.canonical:
                article_data['canonical'] = article.canonical

            articles.append(article_data)
        except Exception as e:
            print(f"Error fetching article from {article_url}: {e}")
            continue

    return articles

# Function to save articles to a JSON file
def save_articles_to_json(articles, feed_title):
    filename = f'{feed_title.replace(" ", "_").lower()}_articles.json'
    with open(filename, 'w') as f:
        json.dump(articles, f, indent=4)
    print(f"Saved {len(articles)} articles to {filename}.")

# Function to scrape RSS links from the main RSS page
def get_rss_links_from_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all anchor tags with href attribute that contains 'rss'
    rss_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'rss' in href:  # Check if the link contains 'rss' (as an indicator of RSS feed)
            rss_links.append(href)

    return rss_links

# Main function to crawl and fetch articles from all RSS feeds
def crawl_and_fetch_articles():
    # Step 1: Scrape the RSS links from the main RSS page
    rss_page_url = "https://www.ndtv.com/rss"
    print(f"Scraping RSS feed links from: {rss_page_url}")
    rss_feed_urls = get_rss_links_from_page(rss_page_url)

    if not rss_feed_urls:
        print("No RSS feed links found.")
        return

    # Step 2: Fetch articles from each RSS feed link
    for rss_feed_url in rss_feed_urls:
        # Check if the URL is absolute or relative and construct the full URL if necessary
        if not rss_feed_url.startswith("http"):
            rss_feed_url = "https://www.ndtv.com" + rss_feed_url

        print(f"Fetching articles from: {rss_feed_url}")
        feed_title = rss_feed_url.split("/")[-1].replace("-", " ").title()  # Get feed title based on URL

        # Fetch articles from each feed
        articles = fetch_articles_from_feed(rss_feed_url)

        # Save articles to a JSON file
        if articles:
            save_articles_to_json(articles, feed_title)
        else:
            print(f"No articles found in {rss_feed_url}.")

# Start the process of fetching and saving articles from all RSS feeds
crawl_and_fetch_articles()
