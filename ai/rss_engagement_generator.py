#!/usr/bin/env python3
"""
RSS-Based Engagement Generator
Generates engagement content from RSS feeds instead of using Twitter API reads
"""

import logging
import requests
import feedparser
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
from pathlib import Path

logger = logging.getLogger(__name__)

class RSSEngagementGenerator:
    """Generate engagement content from RSS feeds to conserve Twitter API reads"""
    
    def __init__(self, config, content_tracker=None):
        """Initialize RSS engagement generator"""
        self.config = config
        self.content_tracker = content_tracker
        
        # Load RSS feeds configuration
        self.rss_feeds = self._load_rss_feeds()
        
        # Cache for recent posts to avoid duplicates
        self.recent_posts = set()
        self.cache_duration = timedelta(hours=72)  # Extended for more opportunities
        self.last_cache_clear = datetime.now()
        
        logger.info(f"📡 RSS Engagement Generator initialized with {len(self.rss_feeds)} feeds")
    
    def has_used_rss_post(self, username: str, content: str) -> bool:
        """Check if RSS post has been used"""
        if self.content_tracker:
            return self.content_tracker.has_used_rss_post(username, content)
        return False
    
    def mark_rss_post_used(self, username: str, content: str):
        """Mark RSS post as used"""
        if self.content_tracker:
            self.content_tracker.mark_rss_post_used(username, content)
    
    def _load_rss_feeds(self) -> Dict[str, str]:
        """Load RSS feeds from configuration file"""
        try:
            config_path = Path("config/rss_feeds.yml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    return config_data.get('rss_feeds', {})
            else:
                logger.warning("RSS feeds configuration file not found")
                return {}
        except Exception as e:
            logger.error(f"Failed to load RSS feeds configuration: {e}")
            return {}
    
    def _clear_old_cache(self):
        """Clear old cached posts"""
        if datetime.now() - self.last_cache_clear > self.cache_duration:
            self.recent_posts.clear()
            self.last_cache_clear = datetime.now()
            logger.debug("🧹 Cleared RSS post cache")
    
    def _fetch_rss_feed(self, username: str, feed_url: str) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed for a specific user"""
        try:
            logger.debug(f"📡 Fetching RSS feed for @{username}")
            
            # Set reasonable timeout and user agent
            headers = {
                'User-Agent': 'TwitterBot/1.0 (Content Discovery; +https://github.com/Rakesh1002/AutoTwitter)'
            }
            
            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            posts = []
            for entry in feed.entries:
                # Get post content
                content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                title = getattr(entry, 'title', '')
                
                # Combine title and content
                full_content = f"{title}\n\n{content}" if title != content else content
                
                # Clean up content (remove HTML tags, etc.)
                full_content = self._clean_content(full_content)
                
                # Skip if too short or already processed
                if len(full_content) < 50 or full_content in self.recent_posts:
                    continue
                
                # Get published date
                published = getattr(entry, 'published_parsed', None)
                published_date = datetime(*published[:6]) if published else datetime.now()
                
                # Only include recent posts (last 72 hours for better engagement opportunities)
                if datetime.now() - published_date > timedelta(hours=72):
                    continue
                
                post_data = {
                    'username': username,
                    'content': full_content,
                    'published': published_date,
                    'link': getattr(entry, 'link', ''),
                    'source': 'rss'
                }
                
                posts.append(post_data)
                self.recent_posts.add(full_content)
            
            logger.debug(f"📡 Found {len(posts)} recent posts from @{username}")
            return posts
            
        except Exception as e:
            logger.warning(f"Failed to fetch RSS feed for @{username}: {e}")
            return []
    
    def _clean_content(self, content: str) -> str:
        """Clean RSS content by removing HTML tags and excess whitespace"""
        import re
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove URLs (they're often duplicated in RSS)
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Remove "RT" and other Twitter artifacts that might be in RSS
        content = re.sub(r'\bRT\b', '', content)
        
        return content
    
    def discover_engagement_opportunities(self, max_opportunities: int = 5) -> List[Dict[str, Any]]:
        """Discover engagement opportunities from RSS feeds instead of Twitter API"""
        self._clear_old_cache()
        
        opportunities = []
        
        # Randomly select RSS feeds to check (to vary content)
        available_feeds = list(self.rss_feeds.items())
        random.shuffle(available_feeds)
        
        # Limit to 3-4 feeds per check to avoid overwhelming
        selected_feeds = available_feeds[:4]
        
        for username, feed_url in selected_feeds:
            posts = self._fetch_rss_feed(username, feed_url)
            
            for post in posts:
                if len(opportunities) >= max_opportunities:
                    break
                
                # Score the engagement opportunity
                score = self._score_rss_post(post)
                
                if score > 5.5:  # More realistic threshold for Twitter engagement
                    # Extract tweet ID from link if available
                    tweet_id = None
                    if 'link' in post:
                        import re
                        tweet_id_match = re.search(r'status/(\d+)', post['link'])
                        if tweet_id_match:
                            tweet_id = tweet_id_match.group(1)
                    
                    opportunity = {
                        'type': 'rss_based',
                        'source_username': post['username'],
                        'content': post['content'],
                        'published': post['published'],
                        'engagement_score': score,
                        'suggested_response_type': self._suggest_response_type(post['content']),
                        'original_tweet_id': tweet_id,
                        'original_link': post.get('link', '')
                    }
                    opportunities.append(opportunity)
            
            if len(opportunities) >= max_opportunities:
                break
        
        logger.info(f"📡 Found {len(opportunities)} RSS-based engagement opportunities")
        return opportunities
    
    def _score_rss_post(self, post: Dict[str, Any]) -> float:
        """Score an RSS post for engagement potential"""
        content = post['content'].lower()
        score = 5.0  # Base score
        
        # Boost for trending topics
        trending_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'startup', 'saas',
            'product', 'growth', 'strategy', 'funding', 'launch', 'build', 'scale'
        ]
        
        for keyword in trending_keywords:
            if keyword in content:
                score += 0.5
        
        # Boost for engagement indicators
        engagement_indicators = [
            'how to', 'why', 'mistake', 'lesson', 'tip', 'strategy', 'framework',
            'just launched', 'just shipped', 'announcing', 'excited to share'
        ]
        
        for indicator in engagement_indicators:
            if indicator in content:
                score += 0.7
        
        # Boost for influential authors
        influential_users = ['naval', 'sama', 'paulg', 'balajis', 'levelsio']
        if post['username'] in influential_users:
            score += 1.0
        
        # Penalize for too long content (Twitter is concise)
        if len(content) > 1000:
            score -= 1.0
        
        # Boost for recent posts
        hours_old = (datetime.now() - post['published']).total_seconds() / 3600
        if hours_old < 6:
            score += 1.0
        elif hours_old < 12:
            score += 0.5
        
        return min(score, 10.0)  # Cap at 10
    
    def _suggest_response_type(self, content: str) -> str:
        """Suggest the type of response based on content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['how to', 'tutorial', 'guide', 'steps']):
            return 'add_insight'
        elif any(word in content_lower for word in ['mistake', 'wrong', 'avoid', 'error']):
            return 'share_experience'
        elif any(word in content_lower for word in ['launch', 'ship', 'announce', 'release']):
            return 'congratulate_and_ask'
        elif any(word in content_lower for word in ['strategy', 'framework', 'approach']):
            return 'build_upon'
        else:
            return 'thoughtful_comment'
    
    def generate_response_content(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response content based on RSS opportunity"""
        
        response_type = opportunity.get('suggested_response_type', 'thoughtful_comment')
        original_content = opportunity['content']
        source_user = opportunity['source_username']
        
        # Create prompt for AI to generate response
        prompt_templates = {
            'add_insight': f"""
            Based on this post from @{source_user}: "{original_content[:200]}..."
            
            Generate a thoughtful Twitter post that adds a complementary insight or practical tip related to this topic. 
            Don't directly quote or mention the original post. 
            Make it valuable and actionable for a startup/SaaS audience.
            """,
            
            'share_experience': f"""
            Based on this post from @{source_user} about challenges/mistakes: "{original_content[:200]}..."
            
            Generate a Twitter post sharing a related experience or lesson learned in the startup/SaaS space.
            Make it personal but professional, with specific insights.
            """,
            
            'congratulate_and_ask': f"""
            Based on this launch/announcement from @{source_user}: "{original_content[:200]}..."
            
            Generate a Twitter post discussing trends, strategies, or insights related to product launches or announcements in the SaaS/startup space.
            Focus on valuable insights for founders and builders.
            """,
            
            'build_upon': f"""
            Based on this strategic post from @{source_user}: "{original_content[:200]}..."
            
            Generate a Twitter post that builds upon this strategy or framework with additional insights, 
            practical implementation tips, or related concepts that would be valuable for startup founders.
            """,
            
            'thoughtful_comment': f"""
            Based on this post from @{source_user}: "{original_content[:200]}..."
            
            Generate a thoughtful Twitter post that discusses related themes or insights in the startup/SaaS/AI space.
            Make it valuable and insightful for entrepreneurs and builders.
            """
        }
        
        return {
            'type': 'rss_inspired_post',
            'prompt': prompt_templates.get(response_type, prompt_templates['thoughtful_comment']),
            'source_username': source_user,
            'response_type': response_type,
            'inspiration_score': opportunity['engagement_score']
        }
    
    def get_rss_status(self) -> Dict[str, Any]:
        """Get status of RSS feeds"""
        working_feeds = 0
        total_feeds = len(self.rss_feeds)
        
        for username, feed_url in list(self.rss_feeds.items())[:3]:  # Test first 3
            try:
                response = requests.head(feed_url, timeout=5)
                if response.status_code == 200:
                    working_feeds += 1
            except:
                pass
        
        return {
            'total_feeds': total_feeds,
            'tested_feeds': min(3, total_feeds),
            'working_feeds': working_feeds,
            'cache_size': len(self.recent_posts),
            'last_cache_clear': self.last_cache_clear
        }
