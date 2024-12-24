import requests
from bs4 import BeautifulSoup
import feedparser
from newsplease import NewsPlease
import datetime
import json
from datetime import timedelta
import re
from urllib.parse import urljoin, urlparse

class RSSCrawler:
    def __init__(self, root_url, days_limit=2):
        self.root_url = root_url
        self.domain = urlparse(root_url).netloc
        self.days_limit = days_limit
        self.feed_urls = set()
        
    def is_valid_feed(self, url):
        """Check if URL is a valid RSS/Atom feed"""
        try:
            feed = feedparser.parse(url)
            return bool(feed.entries) and hasattr(feed, 'version') and feed.version != ''
        except:
            return False

    def is_same_domain(self, url):
        """Check if URL belongs to same domain"""
        return urlparse(url).netloc == self.domain

    def get_all_rss_feeds(self):
        """Extract all RSS feed URLs from the root page"""
        try:
            response = requests.get(self.root_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find potential feed URLs using common patterns
            feed_patterns = [
                # Links ending with RSS-related extensions
                r'.*\.(rss|xml|atom)$',
                # Links containing RSS-related keywords
                r'.*(rss|feed|atom|syndication).*'
            ]
            
            # Look for common RSS link types
            for link in soup.find_all(['a', 'link']):
                href = link.get('href', '')
                type_attr = link.get('type', '')
                
                # Skip if no href
                if not href:
                    continue
                    
                # Make URL absolute
                absolute_url = urljoin(self.root_url, href)
                
                # Skip if different domain
                if not self.is_same_domain(absolute_url):
                    continue
                
                # Check if it's a feed link
                is_feed = False
                
                # Check type attribute
                if any(feed_type in type_attr.lower() for feed_type in ['rss', 'atom', 'xml']):
                    is_feed = True
                    
                # Check URL patterns
                if any(re.match(pattern, href.lower()) for pattern in feed_patterns):
                    is_feed = True
                    
                if is_feed:
                    self.feed_urls.add(absolute_url)
            
            # Validate each feed
            valid_feeds = set()
            for url in self.feed_urls:
                if self.is_valid_feed(url):
                    valid_feeds.add(url)
                    
            print(f"Found {len(valid_feeds)} valid RSS feeds")
            return valid_feeds
            
        except Exception as e:
            print(f"Error fetching RSS feeds: {str(e)}")
            return set()

    def is_within_days_limit(self, pub_date):
        """Check if article is within days limit"""
        if not pub_date:
            return False
        
        now = datetime.datetime.now(datetime.timezone.utc)
        limit_date = now - timedelta(days=self.days_limit)
        return pub_date >= limit_date

    def parse_date(self, date_str):
        """Parse date string to datetime object"""
        try:
            # Try common date formats
            date_formats = [
                '%a, %d %b %Y %H:%M:%S %z',  # RFC 822
                '%Y-%m-%dT%H:%M:%S%z',       # ISO 8601
                '%Y-%m-%d %H:%M:%S',         # Basic format
                '%a, %d %b %Y %H:%M:%S %Z',  # Alternative RFC 822
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.datetime.strptime(date_str, fmt)
                except:
                    continue
                    
            return None
        except:
            return None

    def crawl_feed(self, feed_url):
        """Crawl a single RSS feed"""
        articles = []
        
        print(f"\nProcessing feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            print(f"No entries found in feed: {feed_url}")
            return []
        
        print(f"Found {len(feed.entries)} entries")
        
        for entry in feed.entries:
            try:
                # Try different date fields
                pub_date = None
                for date_field in ['published', 'updated', 'pubDate']:
                    if hasattr(entry, date_field):
                        pub_date = self.parse_date(getattr(entry, date_field))
                        if pub_date:
                            break
                
                # Skip if article is older than limit
                if not self.is_within_days_limit(pub_date):
                    continue
                
                # Extract article content
                article = NewsPlease.from_url(entry.link)
                
                if article:
                    article_data = {
                        'title': article.title or entry.get('title', ''),
                        'text': article.text,
                        'description': entry.get('description', ''),
                        'link': entry.link,
                        'published_date': pub_date.isoformat() if pub_date else None,
                        'authors': article.authors or entry.get('authors', []),
                        'category': entry.get('category', ''),
                        'source_feed': feed_url,
                        'source_domain': self.domain
                    }
                    articles.append(article_data)
                    print(f"Processed: {article_data['title']}")
                    
            except Exception as e:
                print(f"Error processing article {entry.get('link', 'unknown')}: {str(e)}")
                continue
                
        return articles

    def crawl(self):
        """Main crawling method"""
        # Get all RSS feed URLs
        feed_urls = self.get_all_rss_feeds()
        if not feed_urls:
            print("No RSS feeds found!")
            return []
            
        # Process all feeds
        all_articles = []
        for feed_url in feed_urls:
            articles = self.crawl_feed(feed_url)
            all_articles.extend(articles)
            
        return all_articles

def main():
    # Get input from user
    root_url = input("Enter the news website's RSS page URL: ")
    days_limit = int(input("Enter number of days to crawl (default 2): ") or 2)
    
    # Initialize crawler
    crawler = RSSCrawler(root_url, days_limit)
    
    # Crawl articles
    print(f"\nCrawling articles from the last {days_limit} days...")
    articles = crawler.crawl()
    
    # Save results
    if articles:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = urlparse(root_url).netloc.replace('.', '_')
        output_file = f"{domain}_articles_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
            
        print(f"\nCompleted! Saved {len(articles)} articles to {output_file}")
    else:
        print("\nNo articles found in the specified time period.")

if __name__ == "__main__":
    main()