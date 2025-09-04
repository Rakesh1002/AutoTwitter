#!/usr/bin/env python3
"""
Email Content Pipeline
Unified email automation with AI-powered content suggestions
"""

import logging
import schedule
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
from ai.content_generator import ContentGenerator
from ai.trend_analyzer import TrendAnalyzer
from .smtp_client import SMTPClient
from .profile_analyzer import ProfileAnalyzer
from core.content_tracker import ContentTracker

logger = logging.getLogger(__name__)

class EmailPipeline:
    """AI-powered email content pipeline"""
    
    def __init__(self, config):
        """Initialize email pipeline"""
        self.config = config
        
        # Validate required configurations
        if not config.email.is_valid():
            raise ValueError("Invalid email configuration")
        if not config.ai.is_valid():
            raise ValueError("Invalid AI configuration")
        
        # Initialize components
        self.content_generator = ContentGenerator(config)
        self.trend_analyzer = TrendAnalyzer(config)
        
        # Use mock SMTP client for testing if no real SMTP configured
        if config.email.smtp_password == "demo_password_16chars":
            from .mock_smtp_client import MockSMTPClient
            self.smtp_client = MockSMTPClient(config)
        else:
            self.smtp_client = SMTPClient(config)
            
        # Initialize profile analyzer with web scraper from trend analyzer
        self.profile_analyzer = ProfileAnalyzer(self.trend_analyzer.web_scraper)
        
        # Initialize content tracker to prevent duplicates
        self.content_tracker = ContentTracker()
        
        # IST timezone for scheduling
        self.ist = pytz.timezone('Asia/Kolkata')
        
        # Pipeline state
        self.is_running = False
        self.emails_sent_today = 0
        self.max_daily_emails = 18
        
        logger.info("📧 Email Pipeline initialized with AI-powered content")
    
    def start_scheduler(self):
        """Start automated email scheduling"""
        self.is_running = True
        
        logger.info("📅 Starting Email Pipeline Scheduler")
        logger.info("📧 AI-powered emails will be sent hourly from 6 AM to 12 AM IST")
        
        # Schedule hourly emails from 6 AM to 12 AM IST
        for hour in range(6, 24):  # 6 AM to 11 PM
            schedule_time = f"{hour:02d}:00"
            schedule.every().day.at(schedule_time).do(self._scheduled_email_task)
            
        # Also schedule for midnight (00:00 = 12 AM)
        schedule.every().day.at("00:00").do(self._scheduled_email_task)
        
        # Daily reset at 1 AM
        schedule.every().day.at("01:00").do(self._daily_reset)
        
        logger.info(f"📅 Scheduled {self.max_daily_emails} daily emails")
        
        # Send immediate test email
        logger.info("📧 Sending initial AI-powered email...")
        self.send_content_email()
        
        # Run scheduler loop
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Email pipeline stopped by user")
            self.stop()
    
    def stop(self):
        """Stop the email pipeline"""
        self.is_running = False
        logger.info("🛑 Email Pipeline stopped")
    
    def send_content_email(self) -> bool:
        """Send AI-powered content suggestion email"""
        
        try:
            current_time = datetime.now(self.ist)
            logger.info(f"🧠 Generating AI-powered content for {current_time.strftime('%I:%M %p IST')}")
            
            # Check daily limit
            if self.emails_sent_today >= self.max_daily_emails:
                logger.warning("Daily email limit reached")
                return False
            
            # Step 1: Analyze trending topics with AI
            trends = self.trend_analyzer.analyze_current_trends()
            top_trend = None
            if trends and 'ai_analysis' in trends:
                ai_analysis = trends['ai_analysis']
                if 'top_opportunities' in ai_analysis and ai_analysis['top_opportunities']:
                    top_trend = ai_analysis['top_opportunities'][0]
                    logger.info(f"📈 Top trending opportunity: {top_trend.get('trend_topic', 'AI-identified trend')}")
            
            # Step 2: Generate AI-powered post suggestions (3 options)
            trending_context = top_trend.get('trend_topic') if top_trend else None
            ai_posts = self.content_generator.generate_viral_posts(
                content_pillar=self._get_hourly_content_pillar(),
                trending_context=trending_context,
                count=3
            )
            
            # Use all 3 AI-generated posts, or fallback if none generated
            if not ai_posts:
                ai_posts = [self._get_fallback_post(), self._get_fallback_post(alternative=True), self._get_fallback_post(alternative=True)]
            
            # Format all posts for email template
            post_suggestions = []
            for i, post in enumerate(ai_posts[:3], 1):
                post_suggestion = {
                    'option_number': i,
                    'pillar': post.get('content_pillar', 'educational'),
                    'framework': post.get('viral_strategy', 'ai-generated'),
                    'content': post['content'],
                    'suggested_time': self._get_optimal_posting_time(),
                    'hashtags': post.get('hashtags', ['#AI', '#SaaS']),
                    'engagement_strategy': post.get('engagement_strategy', 'Engage with all replies within 1 hour'),
                    'viral_score': post.get('viral_score', 8.0),
                    'trending_inspiration': post.get('trending_inspiration', 'Current market trends'),
                    'viral_potential': post.get('viral_potential', 'High engagement potential'),
                    'viral_explanation': post.get('viral_explanation', 'Combines actionable insight with authentic personal experience that resonates with entrepreneurs and builders'),
                    'ai_model': self.config.ai.get_current_provider_config().model_name,
                    'character_count': post.get('character_count', len(post['content'])),
                    'is_thread': post.get('is_thread', False),
                    'thread_count': post.get('thread_count', 1)
                }
                post_suggestions.append(post_suggestion)
            
            # Step 3: Get profile-based engagement opportunities
            # Get engagement opportunities ONLY from RSS feeds + Twitter API (NO web scraping) 
            engagement_opportunities = []
            try:
                # RSS Feed opportunities (primary source for replies)
                rss_opportunities = self.rss_engagement.discover_engagement_opportunities(max_opportunities=2)
                for opp in rss_opportunities:
                    if not self.content_tracker.has_used_rss_post(opp.get('source_username', ''), opp.get('content', '')):
                        engagement_opportunities.append(opp)
                
                # Twitter API viral opportunities (only if we have reads left and from known profiles)
                if self.api_tracker.can_read() and len(engagement_opportunities) < 2:
                    try:
                        viral_opportunities = self.profile_analyzer.get_top_engagement_opportunities(limit=1)
                        for opp in viral_opportunities:
                            # Only include if from profiles in our RSS feeds
                            author_name = opp.get('author_name', '').replace('@', '')
                            if author_name in ['sama', 'naval', 'AndrewYNg', 'alliekmiller', 'mattshumer_', 'balajis', 'ylecun', 'paulg', 'levelsio']:
                                engagement_opportunities.append(opp)
                                self.api_tracker.record_read()
                    except Exception as e:
                        logger.warning(f"Twitter API opportunity discovery failed: {e}")
                
                logger.info(f"📊 Found {len(engagement_opportunities)} engagement opportunities (RSS + API only)")
                
            except Exception as e:
                logger.warning(f"Engagement opportunity discovery failed: {e}")
                engagement_opportunities = []
            
            # Step 4: Generate contextual AI replies for each unique engagement opportunity
            enhanced_opportunities = []
            used_reply_concepts = set()  # Track reply concepts to ensure uniqueness
            
            for opp in engagement_opportunities:
                try:
                    # Generate contextual replies specific to this tweet's content
                    tweet_content = opp.get('content', '')
                    author_name = opp.get('author', 'unknown')
                    
                    # Create contextual prompt for this specific tweet
                    contextual_prompt = f"""
                    Generate 2 unique, contextual replies to this specific tweet by {author_name}:
                    
                    Original Tweet: "{tweet_content}"
                    
                    Requirements:
                    - Reply must be SPECIFIC to the content above
                    - Include personal SaaS/startup experience relevant to their point
                    - Ask a follow-up question related to their specific message
                    - Avoid generic responses
                    - Keep under 280 characters
                    - Sound like Rakesh Roushan (SaaS expert with practical experience)
                    
                    Generate 2 different reply approaches:
                    1. Personal experience + specific question
                    2. Contrarian insight + follow-up
                    """
                    
                    # Generate contextual replies instead of generic ones
                    contextual_replies = self.content_generator.ai_client.generate_content(contextual_prompt)
                    
                    if contextual_replies and 'content' in contextual_replies:
                        # Parse the response to extract multiple replies
                        reply_text = contextual_replies['content']
                        
                        # Store contextual reply information
                        opp['contextual_reply_prompt'] = contextual_prompt
                        opp['ai_reply_suggestion'] = reply_text[:280]  # Limit to tweet length
                        opp['ai_reply_strategy'] = f"Contextual response to {author_name}'s specific content"
                        opp['reply_viral_score'] = 8.0  # Higher score for contextual content
                        opp['reply_options'] = [{'content': reply_text[:280], 'viral_score': 8.0}]
                    else:
                        # Skip opportunities that can't generate proper contextual replies
                        logger.warning(f"Skipping {author_name} - unable to generate contextual reply")
                        continue
                    
                    enhanced_opportunities.append(opp)
                    
                except Exception as e:
                    logger.warning(f"Failed to generate contextual reply for {author_name}: {e}")
                    # Skip opportunities with generation failures instead of using generic fallbacks
                    continue
            
            # Step 5: Check for duplicate content AND themes before sending
            email_content_hash = self._generate_email_content_hash(post_suggestions, enhanced_opportunities)
            main_theme = trending_context if trending_context else top_trend.get('trend_topic', 'general_content') if top_trend else 'general_content'
            
            # Check both exact content and thematic duplicates
            has_content_duplicate = self.content_tracker.has_generated_similar_email(
                content=str(post_suggestions),
                content_type=top_trend.get('trend_topic', 'general') if top_trend else 'general',
                context=trending_context or ''
            )
            has_theme_duplicate = self.content_tracker.has_used_theme_recently(main_theme, timeframe_hours=6)
            
            if has_content_duplicate or has_theme_duplicate:
                skip_reason = "content" if has_content_duplicate else "theme"
                logger.info(f"⏭️ Skipping email - similar {skip_reason} already used recently (theme: {main_theme})")
                
                # Try to generate completely different content with different theme
                logger.info("🔄 Attempting alternative content with different theme...")
                
                # Try completely different content approach with NO trending context
                alternative_topics = [
                    "General SaaS growth strategies without current trends",
                    "Product development best practices",
                    "Team building and leadership insights",
                    "Customer acquisition and retention",
                    "Business strategy and execution"
                ]
                
                import random
                alternative_topic = random.choice(alternative_topics)
                
                fresh_posts = self.content_generator.generate_viral_posts(
                    content_pillar=self._get_alternative_content_pillar(),
                    trending_context=alternative_topic,  # Use alternative topic instead
                    count=3,

                )
                
                if fresh_posts:
                    # Check if the new theme is also recently used
                    alternative_theme = fresh_posts[0].get('trending_inspiration', alternative_topic)
                    if self.content_tracker.has_used_theme_recently(alternative_theme, timeframe_hours=6):
                        logger.info("⏭️ Even alternative content theme already used - skipping this email cycle")
                        return True  # Skip entirely if we can't find unique content
                    
                    # Format fresh posts
                    post_suggestions = []
                    for i, post in enumerate(fresh_posts[:3], 1):
                        post_suggestion = {
                            'option_number': i,
                            'pillar': post.get('content_pillar', 'educational'),
                            'framework': post.get('viral_strategy', 'ai-generated'),
                            'content': post['content'],
                            'suggested_time': self._get_optimal_posting_time(),
                            'hashtags': post.get('hashtags', ['#AI', '#SaaS']),
                            'engagement_strategy': post.get('engagement_strategy', 'Engage with all replies within 1 hour'),
                            'viral_score': post.get('viral_score', 8.0),
                            'trending_inspiration': post.get('trending_inspiration', alternative_topic),
                            'viral_potential': post.get('viral_potential', 'High engagement potential'),
                            'viral_explanation': post.get('viral_explanation', 'Combines actionable insight with authentic personal experience that resonates with entrepreneurs and builders'),
                            'ai_model': self.config.ai.get_current_provider_config().model_name,
                            'character_count': post.get('character_count', len(post['content'])),
                            'is_thread': post.get('is_thread', False),
                            'thread_count': post.get('thread_count', 1)
                        }
                        post_suggestions.append(post_suggestion)
                    
                    # Update the main theme to the alternative
                    main_theme = alternative_theme
                else:
                    logger.info("⏭️ Failed to generate alternative content - skipping this email cycle")
                    return True
            
            # Step 6: Send enhanced email with AI content (multiple post options)
            success = self.smtp_client.send_content_email(
                post_suggestions, enhanced_opportunities, trends
            )
            
            if success:
                self.emails_sent_today += 1
                
                # Track both content and theme to prevent duplicates
                self.content_tracker.mark_email_content_generated(email_content_hash)
                self.content_tracker.mark_theme_used(main_theme)
                
                logger.info("✅ AI-powered content suggestion email sent successfully")
                
                # Log AI insights for analysis
                self._log_ai_insights(post_suggestions[0] if post_suggestions else {}, enhanced_opportunities, trends)
                return True
            else:
                logger.error("❌ Failed to send AI-powered content suggestion email")
                return False
                
        except Exception as e:
            logger.error(f"Error in AI content pipeline: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """Send a test email"""
        
        try:
            test_content = {
                'pillar': 'test',
                'content': 'This is a test email from the AI-powered content pipeline.',
                'viral_score': 8.0,
                'hashtags': ['#Test', '#AI']
            }
            
            test_opportunities = [
                {
                    'author': '@test_user',
                    'content': 'This is a test engagement opportunity',
                    'engagement_score': 85,
                    'timing': '1 hour ago',
                    'ai_reply_suggestion': 'This is a test AI-generated reply'
                }
            ]
            
            success = self.smtp_client.send_content_email(
                test_content, test_opportunities, {}
            )
            
            if success:
                logger.info("✅ Test email sent successfully")
                return True
            else:
                logger.error("❌ Test email failed")
                return False
                
        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get email pipeline analytics"""
        
        return {
            'daily_stats': {
                'emails_sent_today': self.emails_sent_today,
                'emails_remaining': self.max_daily_emails - self.emails_sent_today
            },
            'pipeline_status': {
                'is_running': self.is_running,
                'can_send_email': self.emails_sent_today < self.max_daily_emails
            },
            'configuration': {
                'max_daily_emails': self.max_daily_emails,
                'timezone': 'Asia/Kolkata',
                'schedule': '6 AM - 12 AM IST (hourly)'
            }
        }
    
    def _scheduled_email_task(self):
        """Scheduled email task"""
        logger.info("📅 Executing scheduled email task")
        
        result = self.send_content_email()
        
        if result:
            logger.info("✅ Scheduled email completed successfully")
        else:
            logger.error("❌ Scheduled email failed")
    
    def _daily_reset(self):
        """Reset daily counters"""
        self.emails_sent_today = 0
        logger.info("🔄 Daily email counter reset")
    
    def _get_hourly_content_pillar(self) -> str:
        """Get content pillar based on hour for strategic distribution"""
        current_hour = datetime.now(self.ist).hour
        
        # Strategic distribution throughout the day
        if 6 <= current_hour <= 9:
            return "educational"  # Morning: Educational content
        elif 10 <= current_hour <= 14:
            return "insight"  # Midday: Industry insights
        elif 15 <= current_hour <= 18:
            return "personal"  # Afternoon: Personal stories
        elif 19 <= current_hour <= 21:
            return "educational"  # Evening: More educational
        else:
            return "interactive"  # Late night: Interactive content
    
    def _get_optimal_posting_time(self) -> str:
        """Get next optimal posting time based on current hour"""
        current_hour = datetime.now(self.ist).hour
        
        # Peak times for tech/SaaS audience (IST)
        optimal_times = {
            6: "9:00 AM IST", 7: "10:00 AM IST", 8: "11:00 AM IST",
            9: "2:00 PM IST", 10: "2:00 PM IST", 11: "2:00 PM IST",
            12: "5:00 PM IST", 13: "5:00 PM IST", 14: "5:00 PM IST",
            15: "7:00 PM IST", 16: "7:00 PM IST", 17: "9:00 PM IST",
            18: "9:00 PM IST", 19: "Next day 9:00 AM IST",
            20: "Next day 9:00 AM IST", 21: "Next day 9:00 AM IST",
            22: "Next day 9:00 AM IST", 23: "Next day 9:00 AM IST"
        }
        
        return optimal_times.get(current_hour, "9:00 AM IST")
    
    def _get_fallback_post(self, alternative: bool = False) -> Dict[str, Any]:
        """Fallback post if AI generation fails"""
        
        if alternative:
            fallback_posts = [
                {
                    'content': f'Most {self.config.brand.expertise_areas[0]} leaders focus on features. Winners focus on outcomes. What outcome are you creating today? {self.config.brand.target_hashtags[0]}',
                    'content_pillar': 'insight',
                    'viral_score': 7.2,
                    'hashtags': self.config.brand.target_hashtags[:2],
                    'engagement_strategy': 'Ask followers to share their outcome-focused strategies',
                    'ai_model': 'fallback_alt'
                },
                {
                    'content': f'Unpopular opinion: The best {self.config.brand.expertise_areas[0]} decisions are made with 70% of the information. The other 30% comes from execution. {self.config.brand.target_hashtags[0]}',
                    'content_pillar': 'personal',
                    'viral_score': 7.0,
                    'hashtags': self.config.brand.target_hashtags[:2],
                    'engagement_strategy': 'Ask followers about their decision-making frameworks',
                    'ai_model': 'fallback_alt2'
                }
            ]
            import random
            return random.choice(fallback_posts)
        
        return {
            'content': f'The difference between good and great {self.config.brand.expertise_areas[0]}: great ones solve problems customers didn\'t know they had. {self.config.brand.target_hashtags[0]} #ProductStrategy',
            'content_pillar': 'insight',
            'viral_score': 7.5,
            'hashtags': self.config.brand.target_hashtags[:2],
            'engagement_strategy': 'Ask followers to share their product discovery stories',
            'ai_model': 'fallback'
        }
    
    def _get_alternative_content_pillar(self) -> str:
        """Get alternative content pillar for fresh content generation"""
        primary_pillar = self._get_hourly_content_pillar()
        
        # Map to alternative pillars for freshness
        alternatives = {
            'educational': 'insight',
            'insight': 'personal', 
            'personal': 'interactive',
            'interactive': 'educational'
        }
        
        return alternatives.get(primary_pillar, 'educational')
    
    def _generate_email_content_hash(self, post_suggestions: list, engagement_opportunities: list) -> str:
        """Generate hash for email content to detect duplicates"""
        # Combine key content elements for hashing
        content_elements = []
        
        # Add detailed post content for better deduplication
        for post in post_suggestions[:3]:  # Only first 3 posts
            content_elements.append(post.get('content', ''))
            content_elements.append(str(post.get('viral_score', '')))
            content_elements.append(post.get('pillar', ''))
        
        # Add engagement content with more detail
        for opp in engagement_opportunities[:3]:  # Only first 3 opportunities
            content_elements.append(f"{opp.get('author', '')}: {opp.get('content', '')[:100]}")
            content_elements.append(opp.get('handle', ''))
        
        # Add hour-level timestamp to ensure time-based variance
        content_elements.append(datetime.now().strftime('%Y-%m-%d-%H'))
        
        # Combine all elements
        combined_content = ' | '.join(content_elements)
        
        # Return the first part of the hash
        import hashlib
        return hashlib.md5(combined_content.lower().encode()).hexdigest()[:16]
    
    def _log_ai_insights(self, post_suggestion: Dict[str, Any], 
                        engagement_opportunities: List[Dict[str, Any]], 
                        trends: Dict[str, Any]):
        """Log AI insights for performance analysis"""
        try:
            insights = {
                'timestamp': datetime.now(self.ist).isoformat(),
                'ai_post_viral_score': post_suggestion.get('viral_score'),
                'trending_topic': trends.get('ai_analysis', {}).get('top_opportunities', [{}])[0].get('trend_topic') if trends else None,
                'engagement_count': len(engagement_opportunities),
                'ai_replies_generated': sum(1 for opp in engagement_opportunities if 'ai_reply_suggestion' in opp),
                'content_pillar': post_suggestion.get('pillar'),
                'character_count': post_suggestion.get('character_count')
            }
            
            # Would log to database or file
            logger.info(f"📊 AI Insights: {insights}")
            
        except Exception as e:
            logger.warning(f"Failed to log AI insights: {e}")
