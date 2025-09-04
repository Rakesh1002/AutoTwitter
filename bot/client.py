#!/usr/bin/env python3
"""
Twitter Bot Client
Unified Twitter automation with AI-powered content and engagement
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import schedule
from ai.content_generator import ContentGenerator
from ai.trend_analyzer import TrendAnalyzer
from ai.rss_engagement_generator import RSSEngagementGenerator
from ai.content_source_manager import ContentSourceManager
from integrations.twitter_api import TwitterAPI
from core.database import session_scope
from core.content_tracker import ContentTracker
from api_usage_tracker import APIUsageTracker

logger = logging.getLogger(__name__)

class TwitterBotClient:
    """Main Twitter bot automation client"""
    
    def __init__(self, config):
        """Initialize Twitter bot client"""
        self.config = config
        
        # Validate required configurations
        if not config.twitter.is_valid():
            raise ValueError("Invalid Twitter API configuration")
        if not config.gemini.is_valid():
            raise ValueError("Invalid Gemini AI configuration")
        
        # Initialize components
        self.content_generator = ContentGenerator(config)
        self.trend_analyzer = TrendAnalyzer(config)
        self.rss_engagement = RSSEngagementGenerator(config)
        self.twitter_api = TwitterAPI(config.twitter)
        self.api_tracker = APIUsageTracker()
        self.content_tracker = ContentTracker()
        
        # Initialize content source manager for optimal strategy
        self.content_source_manager = ContentSourceManager(
            config, self.twitter_api, self.rss_engagement, 
            self.trend_analyzer, self.api_tracker, self.content_tracker
        )
        
        # Bot state
        self.is_running = False
        self.last_post_time = None
        self.daily_post_count = 0
        self.daily_engagement_count = 0
        
        # Configuration - CORRECTED Twitter API v2 free tier limits
        # API Limits: 100 reads/month, 500 writes/month
        self.max_daily_posts = 16  # ~480 posts/month (safe buffer)
        self.max_daily_engagements = 16  # Same limit pool as posts
        self.min_post_interval = 3600  # 1 hour (conservative)
        self.min_engagement_interval = 3600  # 1 hour (conservative)
        
        logger.info("🤖 Twitter Bot Client initialized")
    
    def start_scheduler(self, dry_run: bool = False):
        """Start automated scheduling"""
        self.is_running = True
        
        logger.info("📅 Starting Twitter Bot Scheduler")
        if dry_run:
            logger.info("🧪 Running in DRY RUN mode - no actual posting")
        
        # Schedule posting times (spread throughout the day)
        posting_times = [
            "09:00", "11:30", "14:00", "16:30", 
            "19:00", "21:00", "22:30"
        ]
        
        for time_str in posting_times:
            schedule.every().day.at(time_str).do(
                self._scheduled_post_task, dry_run=dry_run
            )
        
        # Schedule engagement checks every 30 minutes
        schedule.every(30).minutes.do(
            self._scheduled_engagement_task, dry_run=dry_run
        )
        
        # Daily reset at midnight
        schedule.every().day.at("00:00").do(self._daily_reset)
        
        logger.info(f"📅 Scheduled {len(posting_times)} daily posts and engagement checks")
        
        # Run scheduler loop
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Bot scheduler stopped by user")
            self.stop()
    
    def stop(self):
        """Stop the bot"""
        self.is_running = False
        logger.info("🛑 Twitter Bot stopped")
    
    def create_and_post_content(self, 
                               content_pillar: Optional[str] = None,
                               custom_content: Optional[str] = None,
                               dry_run: bool = False) -> Dict[str, Any]:
        """Create and post content"""
        
        try:
            if custom_content:
                # Use custom content
                post_data = {
                    'content': custom_content,
                    'content_pillar': 'custom',
                    'viral_score': 7.0,
                    'hashtags': self.config.brand.target_hashtags[:2]
                }
            else:
                # Generate AI content
                posts = self.content_generator.generate_viral_posts(
                    content_pillar=content_pillar, count=1
                )
                
                if not posts:
                    raise Exception("Failed to generate content")
                
                post_data = posts[0]
            
            # Validate content
            if not self._validate_post_content(post_data):
                raise Exception("Content validation failed")
            
            if dry_run:
                logger.info("🧪 DRY RUN - Content generated but not posted")
                return {
                    'success': True,
                    'content': post_data['content'],
                    'viral_score': post_data.get('viral_score'),
                    'posted': False,
                    'tweet_id': None
                }
            
            # Check rate limits AND API usage limits
            if not self._check_posting_limits():
                raise Exception("Daily posting limit reached")
            
            if not self.api_tracker.can_post():
                raise Exception("API monthly/daily posting limit reached")
            
            # Check for duplicate content before posting
            if self.content_tracker.has_posted_similar_content(
                content=post_data['content'], 
                content_type=post_data.get('content_pillar', 'insight'),
                context=''  # No trending context in direct posting
            ):
                logger.info(f"⏭️ Skipping similar content - already posted recently")
                return {
                    'success': True,
                    'content': post_data['content'],
                    'skipped': True,
                    'reason': 'duplicate_content',
                    'posted': False
                }
            
            # Post to Twitter
            tweet_id = self.twitter_api.post_tweet(post_data['content'])
            
            if tweet_id:
                # Record successful post
                self._record_post(post_data, tweet_id)
                self.daily_post_count += 1
                self.last_post_time = datetime.utcnow()
                
                # Track API usage
                self.api_tracker.record_post()
                
                # Track the posted content to prevent duplicates
                self.content_tracker.mark_content_posted(
                    content=post_data['content'],
                    content_type=post_data.get('content_pillar', 'insight'),
                    context=''  # No trending context in direct posting
                )
                
                logger.info(f"✅ Posted tweet: {tweet_id}")
                logger.info(f"📝 Content: {post_data['content'][:50]}...")
                
                return {
                    'success': True,
                    'content': post_data['content'],
                    'viral_score': post_data.get('viral_score'),
                    'posted': True,
                    'tweet_id': tweet_id
                }
            else:
                raise Exception("Failed to post to Twitter")
                
        except Exception as e:
            logger.error(f"❌ Error creating/posting content: {e}")
            return {
                'success': False,
                'error': str(e),
                'posted': False
            }
    
    def discover_and_engage(self, dry_run: bool = False) -> Dict[str, Any]:
        """Discover and engage using optimal content source strategy"""
        
        try:
            # Check rate limits AND API usage limits
            if not self._check_engagement_limits():
                return {
                    'success': False,
                    'error': 'Daily engagement limit reached'
                }
            
            if not self.api_tracker.can_engage():
                return {
                    'success': False,
                    'error': 'API monthly/daily engagement limit reached'
                }
            
            logger.info("🎯 Using optimal content source strategy for engagement...")
            
            # Check API limits first - if reached, force RSS-only mode
            api_usage = self.api_tracker.get_usage_stats()
            daily_reads = api_usage.get('daily_reads', 0)
            max_daily_reads = 3  # Conservative limit for Twitter API v2 Free Tier
            
            if daily_reads >= max_daily_reads:
                logger.warning(f"⚠️ Daily read limit reached: {daily_reads}/{max_daily_reads}")
                logger.info("🔄 Switching to RSS-only content discovery for automation")
                
                # Force RSS-only discovery
                content_result = self.content_source_manager._get_rss_reply_opportunity()
                if content_result.get('success'):
                    logger.info("✅ Found RSS opportunity, proceeding with reply")
                    return self._handle_rss_reply(content_result)
                else:
                    logger.warning("⚠️ RSS-only discovery also failed - no content available")
                    return {
                        'success': True,
                        'engaged': 0,
                        'skipped_reason': 'api_limit_reached_and_no_rss'
                    }
            
            # Get content from optimal source manager (includes API calls)
            content_result = self.content_source_manager.get_content_for_posting(content_type="engagement")
            
            if not content_result['success']:
                logger.info(f"⚠️ Content discovery failed: {content_result['error']}")
                return {
                    'success': True,
                    'opportunities_found': 0,
                    'engaged': 0,
                    'source': content_result['source'].value
                }
            
            if dry_run:
                logger.info("🧪 DRY RUN - Optimal engagement opportunity found but not acted upon")
                return {
                    'success': True,
                    'content_result': content_result,
                    'engaged': False,
                    'dry_run': True,
                    'source': content_result['source'].value
                }
            
            # Handle different content source types
            return self._execute_engagement_strategy(content_result)
                
        except Exception as e:
            logger.error(f"❌ Error in optimal engagement strategy: {e}")
            return {
                'success': False,
                'error': str(e),
                'engaged': False
            }
    
    def _execute_engagement_strategy(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate engagement strategy based on content source"""
        
        action_type = content_result.get('action_type')
        source = content_result['source']
        
        if action_type == 'direct_viral_reply':
            return self._handle_viral_reply(content_result)
        elif action_type == 'rss_reply':
            return self._handle_rss_reply(content_result)
        elif action_type == 'trending_post':
            return self._handle_trending_content(content_result)
        elif action_type in ['inspired_engagement', 'standalone_post']:  # Legacy support
            return self._handle_inspired_content(content_result)
        else:
            raise Exception(f"Unknown action type: {action_type}")
    
    def _handle_viral_reply(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct reply to viral tweet"""
        
        viral_tweet = content_result['viral_tweet']
        
        logger.info(f"💬 Replying to viral tweet from @{viral_tweet['author']} (score: {viral_tweet['engagement_score']:.1f})")
        
        # Generate AI reply for viral tweet
        reply_prompt = f"""
        Generate a thoughtful, engaging reply to this viral tweet:
        
        Author: @{viral_tweet['author']}
        Content: {viral_tweet['content']}
        Engagement: {viral_tweet['likes']} likes, {viral_tweet['retweets']} retweets
        
        Guidelines:
        - Be authentic and add genuine value
        - Ask insightful questions or share relevant experience
        - Keep under 280 characters
        - Match the professional, analytical tone
        - Don't be promotional - focus on meaningful contribution
        
        Generate only the reply text, no quotes or attribution.
        """
        
        ai_response = self.content_generator.ai_client.generate_content(reply_prompt)
        
        if not ai_response or not ai_response.get('content'):
            raise Exception("Failed to generate viral reply")
        
        reply_content = ai_response['content'].strip()
        
        # Check for duplicate content
        if self.content_tracker.has_posted_similar_content(
            content=reply_content,
            content_type='reply',
            context=opportunity.get('original_content', '')
        ):
            logger.info("⏭️ Skipping similar reply content")
            return {
                'success': True,
                'engaged': 0,
                'skipped_reason': 'duplicate_content'
            }
        
        # Post the reply
        reply_id = self.twitter_api.reply_to_tweet(viral_tweet['tweet_id'], reply_content)
        
        if reply_id:
            # Track engagement
            self.daily_engagement_count += 1
            self.api_tracker.record_write()
            self.content_tracker.mark_tweet_replied(viral_tweet['tweet_id'])
            self.content_tracker.mark_content_posted(
                content=reply_content,
                content_type='reply', 
                context=opportunity.get('original_content', '')
            )
            
            logger.info(f"✅ Posted viral reply to @{viral_tweet['author']}")
            logger.info(f"💬 Reply: {reply_content[:50]}...")
            
            return {
                'success': True,
                'engaged': 1,
                'reply_id': reply_id,
                'reply_content': reply_content,
                'source': 'api_viral_reply',
                'target_tweet': viral_tweet['tweet_id']
            }
        else:
            raise Exception("Failed to post viral reply")
    
    def _handle_inspired_content(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RSS-inspired content creation"""
        
        opportunity = content_result['opportunity']
        
        # Check if content already used
        if self.content_tracker.has_used_rss_post(
            opportunity['source_username'], 
            opportunity['content']
        ):
            logger.info("⏭️ RSS content already used")
            return {
                'success': True,
                'engaged': 0,
                'skipped_reason': 'content_already_used'
            }
        
        # Generate inspired content
        response_content = self.rss_engagement.generate_response_content(opportunity)
        
        logger.info(f"🤖 Generating RSS-inspired content (source: @{opportunity['source_username']})")
        ai_response = self.content_generator.ai_client.generate_content(response_content['prompt'])
        
        if not ai_response or not ai_response.get('content'):
            raise Exception("Failed to generate RSS-inspired content")
        
        tweet_content = ai_response['content'].strip()
        
        # Check for duplicate content
        if self.content_tracker.has_posted_similar_content(
            content=tweet_content,
            content_type='insight',
            context=opportunity.get('original_content', '')
        ):
            logger.info("⏭️ Skipping similar inspired content")
            return {
                'success': True,
                'engaged': 0,
                'skipped_reason': 'duplicate_content'
            }
        
        # Post as reply to original tweet if tweet ID is available, otherwise as standalone
        original_tweet_id = opportunity.get('original_tweet_id')
        
        if original_tweet_id:
            logger.info(f"💬 Replying to original tweet: {original_tweet_id}")
            tweet_id = self.twitter_api.reply_to_tweet(original_tweet_id, tweet_content)
            
            if tweet_id:
                # Track engagement and return success with reply info
                self.daily_engagement_count += 1
                self.api_tracker.record_write()
                self.content_tracker.mark_rss_post_used(
                    opportunity['source_username'], 
                    opportunity['content']
                )
                
                logger.info(f"✅ Posted RSS reply to @{opportunity['source_username']}")
                
                return {
                    'success': True,
                    'engaged': 1,
                    'posted': True,
                    'tweet_id': tweet_id,
                    'content': tweet_content,
                    'source_username': opportunity['source_username'],
                    'original_tweet_id': original_tweet_id,
                    'is_reply': True
                }
        else:
            logger.info(f"📝 Posting as standalone tweet (no original tweet ID)")
            tweet_id = self.twitter_api.post_tweet(tweet_content)
        
        if tweet_id:
            # Track engagement
            self.daily_engagement_count += 1
            self.api_tracker.record_write()
            self.content_tracker.mark_rss_post_used(
                opportunity['source_username'], 
                opportunity['content']
            )
            self.content_tracker.mark_content_posted(
                content=tweet_content,
                content_type='insight',
                context=opportunity.get('original_content', '')
            )
            
            logger.info(f"✅ Posted RSS-inspired tweet (source: @{opportunity['source_username']})")
            logger.info(f"📝 Content: {tweet_content[:50]}...")
            
            return {
                'success': True,
                'engaged': 1,
                'tweet_id': tweet_id,
                'tweet_content': tweet_content,
                'source': 'rss_inspiration',
                'inspiration_user': opportunity['source_username']
            }
        else:
            raise Exception("Failed to post RSS-inspired tweet")
    
    def _handle_rss_reply(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RSS reply generation (posts actual replies to original tweets)"""
        
        opportunity = content_result['opportunity']
        target_user = opportunity['source_username']
        
        # Check if content already used
        if self.content_tracker.has_used_rss_post(
            opportunity['source_username'], 
            opportunity['content']
        ):
            logger.info("⏭️ RSS content already used")
            return {
                'success': True,
                'engaged': 0,
                'skipped_reason': 'content_already_used'
            }
        
        # Generate response content
        response_content = self.rss_engagement.generate_response_content(opportunity)
        
        logger.info(f"🤖 Generating RSS-inspired content (source: @{opportunity['source_username']})")
        ai_response = self.content_generator.ai_client.generate_content(response_content['prompt'])
        
        if not ai_response or not (ai_response.get('content') or ai_response.get('tweet') or ai_response.get('post')):
            raise Exception("Failed to generate RSS-inspired content")
        
        tweet_content = (ai_response.get('content') or ai_response.get('tweet') or ai_response.get('post', '')).strip()
        
        # Check for duplicate content
        if self.content_tracker.has_posted_similar_content(
            content=tweet_content,
            content_type='insight',
            context=opportunity.get('original_content', '')
        ):
            logger.info("⏭️ Skipping similar inspired content")
            return {
                'success': True,
                'engaged': 0,
                'skipped_reason': 'duplicate_content'
            }
        
        # Post as reply to original tweet if tweet ID is available, otherwise as standalone
        original_tweet_id = opportunity.get('original_tweet_id')
        
        if original_tweet_id:
            logger.info(f"💬 Replying to original tweet: {original_tweet_id}")
            tweet_id = self.twitter_api.reply_to_tweet(original_tweet_id, tweet_content)
            
            if tweet_id:
                # Track engagement and return success with reply info
                self.daily_engagement_count += 1
                self.api_tracker.record_write()
                self.content_tracker.mark_rss_post_used(
                    opportunity['source_username'], 
                    opportunity['content']
                )
                
                logger.info(f"✅ Posted RSS reply to @{opportunity['source_username']}")
                
                return {
                    'success': True,
                    'engaged': 1,
                    'posted': True,
                    'tweet_id': tweet_id,
                    'content': tweet_content,
                    'source_username': opportunity['source_username'],
                    'original_tweet_id': original_tweet_id,
                    'is_reply': True
                }
        else:
            logger.info(f"📝 Posting as standalone tweet (no original tweet ID)")
            tweet_id = self.twitter_api.post_tweet(tweet_content)
        
        if tweet_id:
            # Track engagement
            self.daily_engagement_count += 1
            self.api_tracker.record_write()
            self.content_tracker.mark_rss_post_used(
                opportunity['source_username'], 
                opportunity['content']
            )
            
            logger.info(f"✅ Posted RSS-inspired tweet (inspired by @{target_user})")
            logger.info(f"📝 Content: {tweet_content[:50]}...")
            
            return {
                'success': True,
                'engaged': 1,
                'tweet_id': tweet_id,
                'tweet_content': tweet_content,
                'source': 'rss_reply',
                'inspiration_user': target_user
            }
        else:
            raise Exception("Failed to post RSS-inspired tweet")
    
    def _handle_trending_content(self, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web scraper trending content"""
        
        trend_topic = content_result['trend_topic']
        trend_context = content_result.get('trend_context', '')
        
        logger.info(f"📈 Creating trending content about: {trend_topic}")
        
        # Generate trending post
        trending_prompt = f"""
        Create a viral Twitter post about this trending topic:
        
        Topic: {trend_topic}
        Context: {trend_context}
        
        Guidelines:
        - Make it relevant to SaaS/startup audience
        - Add unique insights or fresh perspective
        - Keep under 280 characters
        - Include actionable advice or thought-provoking question
        - Be authentic and valuable
        
        Generate only the tweet content.
        """
        
        ai_response = self.content_generator.ai_client.generate_content(trending_prompt)
        
        if not ai_response or not ai_response.get('content'):
            raise Exception("Failed to generate trending content")
        
        tweet_content = ai_response['content'].strip()
        
        # Check for duplicate content
        if self.content_tracker.has_posted_similar_content(
            content=tweet_content,
            content_type='insight',
            context=opportunity.get('original_content', '')
        ):
            logger.info("⏭️ Skipping similar trending content")
            return {
                'success': True,
                'engaged': 0,
                'skipped_reason': 'duplicate_content'
            }
        
        # Post trending tweet
        tweet_id = self.twitter_api.post_tweet(tweet_content)
        
        if tweet_id:
            # Track engagement
            self.daily_engagement_count += 1
            self.api_tracker.record_write()
            self.content_tracker.mark_content_posted(
                content=tweet_content,
                content_type='insight',
                context=opportunity.get('original_content', '')
            )
            
            logger.info(f"✅ Posted trending tweet about: {trend_topic}")
            logger.info(f"📝 Content: {tweet_content[:50]}...")
            
            return {
                'success': True,
                'engaged': 1,
                'tweet_id': tweet_id,
                'tweet_content': tweet_content,
                'source': 'web_scraper_trending',
                'trend_topic': trend_topic
            }
        else:
            raise Exception("Failed to post trending tweet")
    
    def _generate_content_from_source(self, content_result: Dict[str, Any], content_pillar: Optional[str]) -> Dict[str, Any]:
        """Generate content based on optimal source result"""
        
        source = content_result['source']
        
        if source.value == 'rss_inspiration':
            # Generate content inspired by RSS
            opportunity = content_result['opportunity']
            response_content = self.rss_engagement.generate_response_content(opportunity)
            
            ai_response = self.content_generator.ai_client.generate_content(response_content['prompt'])
            
            if ai_response and ai_response.get('content'):
                return {
                    'content': ai_response['content'].strip(),
                    'content_pillar': content_pillar or 'rss_inspired',
                    'viral_score': opportunity.get('engagement_score', 7.0),
                    'hashtags': self.config.brand.target_hashtags[:2],
                    'source': 'rss_inspiration',
                    'inspiration_user': opportunity['source_username']
                }
        
        elif source.value == 'web_scraper_trending':
            # Generate content based on trending topics (standalone posts only)
            trend_topic = content_result['trend_topic']
            trend_context = content_result.get('trend_context', '')
            
            trending_prompt = f"""
            Create a viral standalone Twitter post about this trending topic:
            
            Topic: {trend_topic}
            Context: {trend_context}
            Pillar: {content_pillar or 'trending'}
            
            Guidelines:
            - Make it relevant to SaaS/startup audience
            - Add unique insights or fresh perspective
            - Keep under 280 characters
            - Include actionable advice or thought-provoking question
            - Be authentic and valuable
            - This is a standalone post, not a reply
            
            Generate only the tweet content.
            """
            
            ai_response = self.content_generator.ai_client.generate_content(trending_prompt)
            
            if ai_response and ai_response.get('content'):
                return {
                    'content': ai_response['content'].strip(),
                    'content_pillar': content_pillar or 'trending',
                    'viral_score': content_result.get('viral_potential', 7.5),
                    'hashtags': self.config.brand.target_hashtags[:2],
                    'source': 'web_scraper_trending',
                    'trend_topic': trend_topic
                }
        
        # Fallback to regular AI content if source-specific generation fails
        logger.warning(f"Source-specific content generation failed for {source.value}, using fallback")
        return self.content_generator.create_content(content_pillar)
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get bot analytics and performance"""
        
        with session_scope() as session:
            # This would query the database for analytics
            # For now, return current session stats
            
            return {
                'daily_stats': {
                    'posts_today': self.daily_post_count,
                    'engagements_today': self.daily_engagement_count,
                    'last_post': self.last_post_time.isoformat() if self.last_post_time else None
                },
                'limits': {
                    'max_daily_posts': self.max_daily_posts,
                    'max_daily_engagements': self.max_daily_engagements,
                    'posts_remaining': self.max_daily_posts - self.daily_post_count,
                    'engagements_remaining': self.max_daily_engagements - self.daily_engagement_count
                },
                'bot_status': {
                    'is_running': self.is_running,
                    'can_post': self._check_posting_limits(),
                    'can_engage': self._check_engagement_limits()
                }
            }
    
    def _scheduled_post_task(self, dry_run: bool = False):
        """Scheduled posting task"""
        logger.info("📅 Executing scheduled post task")
        
        # Analyze trends for content pillar selection
        try:
            trends = self.trend_analyzer.analyze_current_trends()
            
            # Select content pillar based on trends
            content_pillar = self._select_content_pillar_from_trends(trends)
            
        except Exception as e:
            logger.warning(f"Trend analysis failed: {e}")
            content_pillar = None
        
        # Create and post content
        result = self.create_and_post_content(
            content_pillar=content_pillar, 
            dry_run=dry_run
        )
        
        if result['success']:
            logger.info("✅ Scheduled post completed successfully")
        else:
            logger.error(f"❌ Scheduled post failed: {result.get('error')}")
    
    def _scheduled_engagement_task(self, dry_run: bool = False):
        """Scheduled engagement task"""
        logger.info("📅 Executing scheduled engagement task")
        
        result = self.discover_and_engage(dry_run=dry_run)
        
        if result['success']:
            if result.get('engaged'):
                logger.info("✅ Scheduled engagement completed successfully")
            else:
                logger.info("ℹ️ No engagement opportunities found")
        else:
            logger.error(f"❌ Scheduled engagement failed: {result.get('error')}")
    
    def _daily_reset(self):
        """Reset daily counters"""
        self.daily_post_count = 0
        self.daily_engagement_count = 0
        logger.info("🔄 Daily counters reset")
    
    def _discover_engagement_opportunities_legacy(self) -> List[Dict[str, Any]]:
        """Legacy Twitter API-based discovery (DEPRECATED - use RSS instead)"""
        
        try:
            # Search for relevant tweets
            search_terms = self.config.brand.target_hashtags + [
                "startup", "saas", "ai", "tech"
            ]
            
            opportunities = []
            rate_limit_hit = False
            
            for term in search_terms[:1]:  # ONLY 1 search term to conserve API reads
                if rate_limit_hit:
                    logger.info(f"⚠️ Skipping remaining search terms due to rate limit")
                    break
                    
                try:
                    # Check if we can perform read operation
                    if not self.api_tracker.can_read():
                        logger.warning(f"⚠️ Skipping search for '{term}' - read limit reached")
                        continue
                    
                    tweets = self.twitter_api.search_tweets(
                        query=term,
                        max_results=10,
                        exclude_replies=True
                    )
                    
                    # Track the read operation
                    self.api_tracker.record_read()
                    
                    for tweet in tweets:
                        # Score engagement potential
                        score = self._score_engagement_opportunity(tweet)
                        
                        if score > 7.0:  # Only high-quality opportunities
                            opportunity = {
                                'tweet_id': tweet['id'],
                                'author': tweet['author']['username'],
                                'content': tweet['text'],
                                'created_at': tweet['created_at'],
                                'engagement_score': score,
                                'search_term': term,
                                'source': 'twitter_api_legacy'
                            }
                            opportunities.append(opportunity)
                            
                except Exception as e:
                    error_str = str(e).lower()
                    if 'rate limit' in error_str or '429' in error_str or 'unauthorized' in error_str:
                        logger.warning(f"⚠️ Rate limit hit for term '{term}': {e}")
                        rate_limit_hit = True
                        # Don't raise exception, just skip remaining terms
                        break
                    else:
                        logger.warning(f"Search failed for term '{term}': {e}")
                        continue
            
            # Sort by engagement score
            opportunities.sort(key=lambda x: x['engagement_score'], reverse=True)
            
            if rate_limit_hit and not opportunities:
                # If we hit rate limits and found no opportunities, raise an exception
                # so the calling method can handle it gracefully
                raise Exception("Rate limit exceeded during engagement discovery")
            
            return opportunities[:3]  # Return only top 3 to conserve API reads
            
        except Exception as e:
            # Re-raise for the calling method to handle
            raise e
    
    def _score_engagement_opportunity(self, tweet: Dict[str, Any]) -> float:
        """Score an engagement opportunity"""
        score = 5.0  # Base score
        
        text = tweet.get('text', '').lower()
        metrics = tweet.get('public_metrics', {})
        
        # Engagement metrics boost
        likes = metrics.get('like_count', 0)
        retweets = metrics.get('retweet_count', 0)
        replies = metrics.get('reply_count', 0)
        
        # Score based on engagement (logarithmic scale)
        if likes > 0:
            score += min(2.0, likes / 50)
        if retweets > 0:
            score += min(1.5, retweets / 25)
        if replies > 0:
            score += min(1.0, replies / 10)
        
        # Content relevance boost
        relevant_terms = [area.lower() for area in self.config.brand.expertise_areas]
        for term in relevant_terms:
            if term in text:
                score += 1.0
        
        # Question boost (good for replies)
        if '?' in text:
            score += 1.0
        
        # Recency boost
        created_at = tweet.get('created_at', '')
        # Would parse timestamp and boost recent tweets
        
        return min(10.0, score)  # Cap at 10
    
    def _validate_post_content(self, post_data: Dict[str, Any]) -> bool:
        """Validate post content"""
        
        content = post_data.get('content', '')
        
        # Basic validation
        if not content or len(content) < 10:
            return False
        
        if len(content) > 280:
            return False
        
        # Safety checks
        inappropriate_terms = ['spam', 'scam', 'hate']
        if any(term in content.lower() for term in inappropriate_terms):
            return False
        
        return True
    
    def _check_posting_limits(self) -> bool:
        """Check if posting is within limits"""
        
        # Daily limit check
        if self.daily_post_count >= self.max_daily_posts:
            return False
        
        # Time interval check
        if self.last_post_time:
            time_since_last = (datetime.utcnow() - self.last_post_time).total_seconds()
            if time_since_last < self.min_post_interval:
                return False
        
        return True
    
    def _check_engagement_limits(self) -> bool:
        """Check if engagement is within limits"""
        
        # Daily limit check
        if self.daily_engagement_count >= self.max_daily_engagements:
            return False
        
        return True
    
    def _select_content_pillar_from_trends(self, trends: Dict[str, Any]) -> Optional[str]:
        """Select content pillar based on trend analysis"""
        
        try:
            ai_analysis = trends.get('ai_analysis', {})
            opportunities = ai_analysis.get('top_opportunities', [])
            
            if opportunities:
                # Map trending topics to content pillars
                top_opportunity = opportunities[0]
                topic = top_opportunity.get('trend_topic', '').lower()
                
                if 'education' in topic or 'learn' in topic:
                    return 'educational'
                elif 'personal' in topic or 'story' in topic:
                    return 'personal'
                elif 'prediction' in topic or 'future' in topic:
                    return 'insight'
                else:
                    return 'interactive'
            
        except Exception as e:
            logger.warning(f"Error selecting content pillar: {e}")
        
        return None
    
    def _record_post(self, post_data: Dict[str, Any], tweet_id: str):
        """Record successful post to database"""
        
        # This would insert into database
        # For now, just log
        logger.info(f"📊 Recording post: {tweet_id}")
        
        # Would save:
        # - tweet_id
        # - content
        # - viral_score
        # - content_pillar
        # - timestamp
        # - hashtags
        
    def _record_engagement(self, opportunity: Dict[str, Any], 
                          reply_data: Dict[str, Any], reply_id: str):
        """Record successful engagement to database"""
        
        # This would insert into database
        # For now, just log
        logger.info(f"📊 Recording engagement: {reply_id}")
        
        # Would save:
        # - original_tweet_id
        # - reply_id
        # - reply_content
        # - engagement_score
        # - timestamp
