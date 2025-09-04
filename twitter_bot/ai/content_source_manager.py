#!/usr/bin/env python3
"""
Content Source Manager
Coordinates RSS feeds, Twitter API reads, and web scraper for optimal content discovery
"""

import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ContentSource(Enum):
    RSS_INSPIRATION = "rss_inspiration"
    API_VIRAL_REPLY = "api_viral_reply"  
    WEB_SCRAPER_TRENDING = "web_scraper_trending"

class ContentSourceManager:
    """Manages and balances all content discovery sources"""
    
    def __init__(self, config, twitter_api, rss_engagement, trend_analyzer, api_tracker, content_tracker):
        self.config = config
        self.twitter_api = twitter_api
        self.rss_engagement = rss_engagement
        self.trend_analyzer = trend_analyzer
        self.api_tracker = api_tracker
        self.content_tracker = content_tracker
        
        # Optimal content distribution strategy (CORRECTED)
        self.content_distribution = {
            'posts': {
                ContentSource.WEB_SCRAPER_TRENDING: 1.0   # 100% web scraper for standalone posts
            },
            'engagements': {
                ContentSource.RSS_INSPIRATION: 0.70,      # 70% RSS feeds for reply discovery
                ContentSource.API_VIRAL_REPLY: 0.30       # 30% Twitter API viral reply discovery
            }
        }
        
        logger.info("🎯 Content Source Manager initialized with optimal strategy")
    
    def get_content_for_posting(self, content_type: str = "post") -> Dict[str, Any]:
        """Get content for posting using optimal source distribution"""
        
        if content_type == "post":
            return self._get_post_content()
        elif content_type == "engagement":
            return self._get_engagement_content()
        else:
            raise ValueError(f"Unknown content type: {content_type}")
    
    def _get_post_content(self) -> Dict[str, Any]:
        """Get content for standalone posts (100% web scraper trending topics)"""
        
        # Always use web scraper for standalone posts
        return self._get_web_scraper_post()
    
    def _get_engagement_content(self) -> Dict[str, Any]:
        """Get content for engagements/replies (RSS + API viral discovery)"""
        
        # Determine source based on distribution  
        rand = random.random()
        
        if rand < self.content_distribution['engagements'][ContentSource.RSS_INSPIRATION]:
            return self._get_rss_reply_opportunity()
        else:
            return self._get_viral_reply_engagement()
    
    def _get_rss_reply_opportunity(self) -> Dict[str, Any]:
        """Find RSS posts to reply to (not for standalone content inspiration)"""
        try:
            opportunities = self.rss_engagement.discover_engagement_opportunities(max_opportunities=5)
            
            # Filter out used content  
            fresh_opportunities = [
                opp for opp in opportunities 
                if not self.content_tracker.has_used_rss_post(opp['source_username'], opp['content'])
            ]
            
            if not fresh_opportunities:
                return {'success': False, 'error': 'No fresh RSS opportunities', 'source': ContentSource.RSS_INSPIRATION}
            
            # Select best opportunity for reply
            opportunity = max(fresh_opportunities, key=lambda x: x['engagement_score'])
            
            return {
                'success': True,
                'source': ContentSource.RSS_INSPIRATION,
                'opportunity': opportunity,
                'action_type': 'rss_reply',  # Reply to RSS content, not standalone post
                'target_user': opportunity['source_username']
            }
            
        except Exception as e:
            logger.error(f"RSS reply discovery failed: {e}")
            return {'success': False, 'error': str(e), 'source': ContentSource.RSS_INSPIRATION}
    
    def _get_web_scraper_post(self) -> Dict[str, Any]:
        """Generate web scraper trending post"""
        try:
            # Analyze current trends
            trends = self.trend_analyzer.analyze_current_trends()
            
            if not trends or not trends.get('ai_analysis'):
                return {'success': False, 'error': 'No trending topics found', 'source': ContentSource.WEB_SCRAPER_TRENDING}
            
            # Get top trending opportunity
            top_opportunities = trends['ai_analysis'].get('top_opportunities', [])
            if not top_opportunities:
                return {'success': False, 'error': 'No trending opportunities', 'source': ContentSource.WEB_SCRAPER_TRENDING}
            
            top_trend = top_opportunities[0]
            
            return {
                'success': True,
                'source': ContentSource.WEB_SCRAPER_TRENDING,
                'trend_topic': top_trend.get('trend_topic'),
                'trend_context': top_trend.get('context'),
                'action_type': 'trending_post',
                'viral_potential': top_trend.get('viral_potential', 'medium')
            }
            
        except Exception as e:
            logger.error(f"Web scraper trending failed: {e}")
            return {'success': False, 'error': str(e), 'source': ContentSource.WEB_SCRAPER_TRENDING}
    
    def _get_rss_inspired_engagement(self) -> Dict[str, Any]:
        """Generate RSS-inspired engagement (DEPRECATED - use _get_rss_reply_opportunity)"""
        return self._get_rss_reply_opportunity()
    
    def _get_viral_reply_engagement(self) -> Dict[str, Any]:
        """Find viral posts for direct replies using Twitter API"""
        try:
            # Check if we can use precious API reads
            if not self.api_tracker.can_read():
                logger.warning("⚠️ Cannot use API reads - limit reached")
                return {'success': False, 'error': 'API read limit reached', 'source': ContentSource.API_VIRAL_REPLY}
            
            # Search for viral posts using strategic terms
            viral_search_terms = [
                "AI startup", "SaaS growth", "product launch", "funding round", 
                "viral", "breaking", "milestone", "achievement"
            ]
            
            # Select one term strategically
            search_term = random.choice(viral_search_terms)
            
            logger.info(f"🔍 Searching for viral posts with term: '{search_term}'")
            
            # Use Twitter API to find viral posts
            tweets = self.twitter_api.search_tweets(
                query=f"{search_term}",  # Basic search without premium operators
                max_results=10,
                exclude_replies=True
            )
            
            # Track the API read
            self.api_tracker.record_read()
            
            # Filter for truly viral posts
            viral_tweets = []
            for tweet in tweets:
                # Check if we've already replied to this tweet
                if self.content_tracker.has_replied_to_tweet(tweet['id']):
                    continue
                
                # Score viral potential
                engagement_score = self._calculate_viral_score(tweet)
                
                if engagement_score > 8.0:  # High viral threshold
                    viral_tweets.append({
                        'tweet_id': tweet['id'],
                        'author': tweet['author']['username'],
                        'content': tweet['text'],
                        'engagement_score': engagement_score,
                        'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                        'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0),
                        'replies': tweet.get('public_metrics', {}).get('reply_count', 0),
                        'created_at': tweet.get('created_at')
                    })
            
            if not viral_tweets:
                return {'success': False, 'error': 'No viral posts found', 'source': ContentSource.API_VIRAL_REPLY}
            
            # Select the most viral post
            best_viral_tweet = max(viral_tweets, key=lambda x: x['engagement_score'])
            
            return {
                'success': True,
                'source': ContentSource.API_VIRAL_REPLY,
                'viral_tweet': best_viral_tweet,
                'action_type': 'direct_viral_reply',
                'search_term': search_term
            }
            
        except Exception as e:
            logger.error(f"Viral reply discovery failed: {e}")
            return {'success': False, 'error': str(e), 'source': ContentSource.API_VIRAL_REPLY}
    
    def _calculate_viral_score(self, tweet: Dict[str, Any]) -> float:
        """Calculate viral potential score for a tweet"""
        metrics = tweet.get('public_metrics', {})
        
        likes = metrics.get('like_count', 0)
        retweets = metrics.get('retweet_count', 0)
        replies = metrics.get('reply_count', 0)
        
        # Weighted scoring for viral potential
        score = (likes * 0.4) + (retweets * 1.0) + (replies * 0.6)
        
        # Normalize to 0-10 scale
        normalized_score = min(score / 100, 10.0)
        
        # Boost for recency
        try:
            created_at = datetime.fromisoformat(tweet.get('created_at', '').replace('Z', '+00:00'))
            hours_old = (datetime.now() - created_at).total_seconds() / 3600
            
            if hours_old < 24:  # Recent posts get boost
                normalized_score *= 1.2
        except:
            pass
        
        return min(normalized_score, 10.0)
    
    def _calculate_enhanced_viral_score(self, content: Dict[str, Any]) -> float:
        """Enhanced viral score calculation with multiple factors"""
        
        try:
            score = 0.0
            title = content.get('title', '').lower()
            text_content = content.get('content', '').lower()
            url = content.get('url', '')
            
            # Base quality score
            quality_score = content.get('quality_score', 0)
            score += min(quality_score, 5)
            
            # Trending potential
            trending_potential = content.get('trending_potential', 0)
            score += min(trending_potential * 0.3, 3)
            
            # Engagement likelihood
            engagement_likelihood = content.get('engagement_likelihood', 0)
            score += min(engagement_likelihood * 0.2, 2)
            
            # Domain authority boost
            authoritative_domains = ['techcrunch.com', 'theverge.com', 'wired.com', 'reuters.com']
            if any(domain in url for domain in authoritative_domains):
                score += 1.5
            
            # Content category boost
            content_category = content.get('content_category', {})
            if content_category.get('primary') in ['ai_breakthrough', 'startup_funding']:
                score += 1.0
            
            # Time relevance
            time_indicators = ['today', 'breaking', 'just announced', 'latest']
            time_matches = sum(1 for indicator in time_indicators if indicator in text_content)
            score += min(time_matches * 0.5, 1)
            
            return min(score, 10.0)
            
        except:
            return 6.0  # Default score
    
    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate hash for content deduplication"""
        import hashlib
        
        title = content.get('title', '')
        url = content.get('url', '')
        content_text = content.get('content', '')[:100]  # First 100 chars
        
        combined = f"{title}{url}{content_text}".lower()
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            if '//' in url:
                return url.split('/')[2]
            return url.split('/')[0] if '/' in url else url
        except:
            return 'unknown'
    
    def get_content_for_email(self, count: int = 3) -> Dict[str, Any]:
        """Get diverse content suggestions for email from all sources"""
        
        email_content = {
            'rss_inspired': [],
            'trending_topics': [],
            'viral_opportunities': [],
            'sources_used': []
        }
        
        try:
            # Get RSS reply opportunities  
            rss_result = self._get_rss_reply_opportunity()
            if rss_result['success']:
                email_content['rss_inspired'].append(rss_result)
                email_content['sources_used'].append('RSS feeds (reply opportunities)')
            
            # Get trending topics from web scraper for standalone posts
            web_result = self._get_web_scraper_post()
            if web_result['success']:
                email_content['trending_topics'].append(web_result)
                email_content['sources_used'].append('Web scraper (standalone posts)')
            
            # Get viral opportunities (only if we have API reads available)
            if self.api_tracker.can_read():
                viral_result = self._get_viral_reply_engagement()
                if viral_result['success']:
                    email_content['viral_opportunities'].append(viral_result)
                    email_content['sources_used'].append('Twitter API (viral replies)')
            
            return email_content
            
        except Exception as e:
            logger.error(f"Email content generation failed: {e}")
            return email_content
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """Get statistics about content source usage"""
        
        return {
            'rss_feeds': {
                'total_feeds': len(self.rss_engagement.rss_feeds),
                'cache_size': len(self.rss_engagement.recent_posts),
                'status': 'active'
            },
            'api_usage': {
                'can_read': self.api_tracker.can_read(),
                'reads_remaining': self.api_tracker.get_usage_stats()['monthly_usage']['reads_remaining'],
                'status': 'limited' if not self.api_tracker.can_read() else 'active'
            },
            'web_scraper': {
                'status': 'active',
                'search_enabled': hasattr(self.trend_analyzer, 'web_scraper') and self.trend_analyzer.web_scraper is not None
            },
            'content_distribution': self.content_distribution
        }
