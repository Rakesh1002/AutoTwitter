#!/usr/bin/env python3
"""
Profile Analyzer
Analyzes target Twitter profiles for engagement opportunities
"""

import logging
from typing import Dict, Any, List, Optional
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ProfileAnalyzer:
    """Analyzes target profiles for engagement opportunities"""
    
    def __init__(self, web_scraper):
        """Initialize profile analyzer with web scraper"""
        self.web_scraper = web_scraper
        self.config = web_scraper.config if hasattr(web_scraper, 'config') else None
        
        # Enhanced target profiles with diverse influential categories
        self.target_profiles = {
            # Original tech leaders
            'tech_leaders': [
                {
                    'username': '@alliekmiller', 'name': 'Allie K. Miller',
                'expertise': 'AI, Machine Learning, Product Strategy',
                'engagement_style': 'Thought leadership, technical insights, industry predictions',
                'posting_frequency': 'High - multiple times daily',
                    'content_themes': ['AI trends', 'ML applications', 'Tech leadership', 'Future predictions'],
                    'follower_range': '500K-1M', 'influence_score': 9.5
            },
            {
                    'username': '@mattshumer_', 'name': 'Matt Shumer',
                'expertise': 'AI, Automation, Product Development',
                'engagement_style': 'Technical depth, practical applications, metrics-driven',
                'posting_frequency': 'Moderate - daily posts with high engagement',
                    'content_themes': ['AI automation', 'Product metrics', 'Technical tutorials', 'Performance optimization'],
                    'follower_range': '100K-500K', 'influence_score': 8.8
            },
            {
                    'username': '@officiallogank', 'name': 'Logan Kilpatrick',
                'expertise': 'Developer Relations, AI, OpenAI',
                'engagement_style': 'Community building, developer education, accessible explanations',
                'posting_frequency': 'High - consistent daily posting',
                    'content_themes': ['Developer education', 'AI accessibility', 'Community insights', 'Technical tutorials'],
                    'follower_range': '100K-500K', 'influence_score': 8.5
                }
            ],
            
            # VCs and Angel Investors
            'investors': [
                {
                    'username': '@sama', 'name': 'Sam Altman',
                    'expertise': 'AI, Startups, VC, OpenAI Leadership',
                    'engagement_style': 'Bold predictions, strategic insights, industry shaping',
                    'posting_frequency': 'High - thought leadership',
                    'content_themes': ['AI future', 'Startup advice', 'Technology trends', 'Society impact'],
                    'follower_range': '1M+', 'influence_score': 10.0
                },
                {
                    'username': '@naval', 'name': 'Naval Ravikant',
                    'expertise': 'Angel Investing, Philosophy, Wealth Creation',
                    'engagement_style': 'Philosophical insights, wealth wisdom, contrarian thinking',
                    'posting_frequency': 'Moderate - high impact posts',
                    'content_themes': ['Wealth creation', 'Philosophy', 'Startups', 'Life wisdom'],
                    'follower_range': '2M+', 'influence_score': 9.8
                },
                {
                    'username': '@balajis', 'name': 'Balaji Srinivasan',
                    'expertise': 'Crypto, Tech, Geopolitics, Former a16z',
                    'engagement_style': 'Data-driven predictions, geopolitical analysis, tech trends',
                    'posting_frequency': 'High - analytical threads',
                    'content_themes': ['Crypto', 'Geopolitics', 'Tech trends', 'Future predictions'],
                    'follower_range': '900K+', 'influence_score': 9.2
                },
                {
                    'username': '@chrissacca', 'name': 'Chris Sacca',
                    'expertise': 'VC, Early Stage Investing, Climate Tech',
                    'engagement_style': 'Direct insights, portfolio wisdom, climate focus',
                    'posting_frequency': 'Moderate - strategic posts',
                    'content_themes': ['Venture capital', 'Climate tech', 'Startup advice', 'Portfolio insights'],
                    'follower_range': '1.5M+', 'influence_score': 9.0
                }
            ],
            
            # Micro VCs and Emerging Investors
            'micro_vcs': [
                {
                    'username': '@harryhurst', 'name': 'Harry Hurst',
                    'expertise': 'Micro VC, Early Stage, SaaS',
                    'engagement_style': 'Practical investing advice, startup metrics',
                    'posting_frequency': 'Daily - startup insights',
                    'content_themes': ['Micro VC', 'SaaS metrics', 'Early stage', 'Founder advice'],
                    'follower_range': '50K-100K', 'influence_score': 8.0
                },
                {
                    'username': '@justinkan', 'name': 'Justin Kan',
                    'expertise': 'Founder, Investor, Community Building',
                    'engagement_style': 'Founder journey, transparent building',
                    'posting_frequency': 'High - authentic sharing',
                    'content_themes': ['Founder journey', 'Community', 'Building in public', 'Investing'],
                    'follower_range': '200K+', 'influence_score': 8.5
                }
            ],
            
            # AI Thought Leaders and Researchers
            'ai_leaders': [
                {
                    'username': '@ylecun', 'name': 'Yann LeCun',
                    'expertise': 'AI Research, Deep Learning, Meta AI',
                    'engagement_style': 'Technical depth, research insights, AI education',
                    'posting_frequency': 'Regular - research focused',
                    'content_themes': ['AI research', 'Deep learning', 'AGI debates', 'Technical education'],
                    'follower_range': '800K+', 'influence_score': 9.7
                },
                {
                    'username': '@AndrewYNg', 'name': 'Andrew Ng',
                    'expertise': 'AI Education, Machine Learning, Coursera',
                    'engagement_style': 'Educational, accessible AI concepts',
                    'posting_frequency': 'Regular - educational focus',
                    'content_themes': ['AI education', 'ML democratization', 'Career advice', 'Industry trends'],
                    'follower_range': '1M+', 'influence_score': 9.5
                },
                {
                    'username': '@karpathy', 'name': 'Andrej Karpathy',
                    'expertise': 'AI Research, Neural Networks, Tesla AI',
                    'engagement_style': 'Technical insights, educational threads',
                    'posting_frequency': 'Moderate - high quality',
                    'content_themes': ['Neural networks', 'AI research', 'Technical tutorials', 'Industry insights'],
                    'follower_range': '700K+', 'influence_score': 9.3
                }
            ],
            
            # Startup Ecosystem and Accelerators
            'startup_ecosystem': [
                {
                    'username': '@paulg', 'name': 'Paul Graham',
                    'expertise': 'Y Combinator, Startup Advice, Essays',
                    'engagement_style': 'Philosophical startup wisdom, contrarian insights',
                    'posting_frequency': 'Moderate - thoughtful posts',
                    'content_themes': ['Startup advice', 'Essays', 'Entrepreneurship', 'YC insights'],
                    'follower_range': '1.8M+', 'influence_score': 9.8
                },
                {
                    'username': '@jessicamliving', 'name': 'Jessica Livingston',
                    'expertise': 'Y Combinator, Startup Stories, Founder Support',
                    'engagement_style': 'Founder stories, startup ecosystem insights',
                    'posting_frequency': 'Regular - ecosystem focus',
                    'content_themes': ['Founder stories', 'Startup ecosystem', 'YC insights', 'Entrepreneur support'],
                    'follower_range': '100K+', 'influence_score': 8.7
                },
                {
                    'username': '@agazdecki', 'name': 'Andrew Gazdecki',
                    'expertise': 'SaaS, Acquisitions, MicroAcquire',
                    'engagement_style': 'SaaS metrics, acquisition insights',
                    'posting_frequency': 'High - SaaS focused',
                    'content_themes': ['SaaS business', 'Acquisitions', 'Bootstrap insights', 'Exit strategies'],
                    'follower_range': '400K+', 'influence_score': 8.5
                }
            ],
            
            # Twitter/X Platform Masters
            'twitter_masters': [
                {
                    'username': '@elonmusk', 'name': 'Elon Musk',
                    'expertise': 'Tech, Space, AI, Business',
                    'engagement_style': 'Controversial, direct, trend-setting',
                    'posting_frequency': 'Very High - multiple daily',
                    'content_themes': ['Tech innovation', 'Space', 'AI', 'Business updates', 'Memes'],
                    'follower_range': '150M+', 'influence_score': 10.0
                },
                {
                    'username': '@levelsio', 'name': 'Pieter Levels',
                    'expertise': 'Indie Hacking, Remote Work, Building in Public',
                    'engagement_style': 'Transparent building, data sharing, nomad lifestyle',
                    'posting_frequency': 'High - authentic updates',
                    'content_themes': ['Indie hacking', 'Revenue transparency', 'Remote work', 'Building in public'],
                    'follower_range': '600K+', 'influence_score': 8.8
                },
                {
                    'username': '@dharmesh', 'name': 'Dharmesh Shah',
                    'expertise': 'HubSpot, Marketing, SaaS Growth',
                    'engagement_style': 'Marketing insights, growth tactics, SaaS wisdom',
                    'posting_frequency': 'Regular - growth focused',
                    'content_themes': ['Marketing', 'SaaS growth', 'HubSpot insights', 'Growth strategies'],
                    'follower_range': '500K+', 'influence_score': 8.6
                }
            ],
            
            # Tech Bloggers and Content Creators
            'content_creators': [
                {
                    'username': '@benthompson', 'name': 'Ben Thompson',
                    'expertise': 'Tech Strategy, Stratechery, Business Analysis',
                    'engagement_style': 'Deep strategic analysis, business model insights',
                    'posting_frequency': 'Regular - analytical posts',
                    'content_themes': ['Tech strategy', 'Business models', 'Platform dynamics', 'Industry analysis'],
                    'follower_range': '300K+', 'influence_score': 9.0
                },
                {
                    'username': '@caseynewton', 'name': 'Casey Newton',
                    'expertise': 'Tech Journalism, Platformer, Content Creator',
                    'engagement_style': 'Investigative insights, platform analysis',
                    'posting_frequency': 'Daily - journalism focus',
                    'content_themes': ['Tech journalism', 'Platform news', 'Industry investigation', 'Creator economy'],
                    'follower_range': '200K+', 'influence_score': 8.5
                }
            ]
        }
        
        # Flatten all profiles for easy access
        self.all_profiles = []
        for category, profiles in self.target_profiles.items():
            for profile in profiles:
                profile['category'] = category
                self.all_profiles.append(profile)
        
        logger.info(f"👥 Profile Analyzer initialized with {len(self.all_profiles)} diverse influential profiles across {len(self.target_profiles)} categories")
    
    def get_top_engagement_opportunities(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get top engagement opportunities from target profiles"""
        
        try:
            opportunities = []
            
            # Intelligently select profiles based on influence and variety
            import random
            
            # Weight selection by influence score and category diversity
            weighted_profiles = []
            for profile in self.all_profiles:
                # Weight by influence score (higher scores get more chances)
                weight = int(profile.get('influence_score', 8.0))
                weighted_profiles.extend([profile] * weight)
            
            # Select diverse profiles ensuring category variety
            selected_profiles = []
            categories_used = set()
            
            # First, ensure at least one from each high-impact category
            priority_categories = ['investors', 'ai_leaders', 'twitter_masters', 'startup_ecosystem']
            for category in priority_categories:
                category_profiles = [p for p in self.all_profiles if p['category'] == category]
                if category_profiles and len(selected_profiles) < count + 2:
                    profile = random.choice(category_profiles)
                    selected_profiles.append(profile)
                    categories_used.add(category)
            
            # Fill remaining slots with weighted random selection
            remaining_slots = max(0, count + 2 - len(selected_profiles))
            available_profiles = [p for p in weighted_profiles if p not in selected_profiles]
            
            if available_profiles and remaining_slots > 0:
                additional_profiles = random.sample(available_profiles, min(remaining_slots, len(available_profiles)))
                selected_profiles.extend(additional_profiles)
            
            # Fetch REAL engagement opportunities from actual Twitter posts
            for profile in selected_profiles:
                real_opportunities = self._fetch_real_twitter_posts(profile)
                if real_opportunities:
                    opportunities.extend(real_opportunities)
                else:
                    # Fallback to mock only if real scraping fails
                    logger.warning(f"Failed to fetch real posts for {profile['username']}, using fallback")
                    fallback_opportunities = self._generate_profile_opportunities(profile)
                    opportunities.extend(fallback_opportunities[:1])  # Limit fallback
            
            # Remove duplicate opportunities (same author + similar content)
            unique_opportunities = []
            seen_authors = set()
            seen_content_hashes = set()
            
            for opp in opportunities:
                author = opp.get('handle', opp.get('author', 'unknown'))
                content = opp.get('content', '')
                
                # Simple content hash for deduplication
                import hashlib
                content_hash = hashlib.md5(content[:100].lower().encode()).hexdigest()[:8]
                
                # Skip if we've seen this author or very similar content
                if author not in seen_authors and content_hash not in seen_content_hashes:
                    unique_opportunities.append(opp)
                    seen_authors.add(author)
                    seen_content_hashes.add(content_hash)
                    
                    # Limit to prevent too many from same category
                    if len(unique_opportunities) >= count:
                        break
            
            # Sort by engagement score and return top unique opportunities
            unique_opportunities.sort(key=lambda x: x['engagement_score'], reverse=True)
            
            return unique_opportunities[:count]
            
        except Exception as e:
            logger.error(f"Error getting engagement opportunities: {e}")
            return self._get_fallback_opportunities(count)
    
    def _fetch_real_twitter_posts(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch real Twitter posts from a profile using RSS feeds"""
        try:
            from datetime import datetime, timedelta
            import pytz
            
            username = profile['username'].replace('@', '')
            profile_name = profile['name']
            
            # Get today's date for filtering recent posts
            ist = pytz.timezone('Asia/Kolkata')
            today = datetime.now(ist)
            
            opportunities = []
            
            # Try RSS feed approach first (most reliable)
            rss_opportunities = self._fetch_from_rss_feed(username, profile)
            if rss_opportunities:
                opportunities.extend(rss_opportunities)
                logger.info(f"✅ Found {len(rss_opportunities)} posts from RSS feed for {username}")
            
            # If RSS fails, fallback to web scraping
            if not opportunities:
                logger.info(f"🔍 RSS failed for {username}, trying web scraping...")
                opportunities = self._fetch_from_web_scraping(username, profile)
            
            return opportunities[:2]  # Limit to 2 per profile
            
        except Exception as e:
            logger.error(f"Error fetching real posts for {profile['username']}: {e}")
            return []
    
    def _is_valid_twitter_post(self, content: str, url: str, username: str) -> bool:
        """Check if content is a valid Twitter post"""
        if not content or len(content.strip()) < 10:
            return False
        
        # Check if URL is from Twitter/X
        if not any(domain in url.lower() for domain in ['twitter.com', 'x.com']):
            return False
        
        # Check if content contains tweet-like patterns
        tweet_indicators = ['retweet', 'reply', 'quote tweet', '@', '#']
        content_lower = content.lower()
        
        # Avoid retweets and replies if possible
        avoid_patterns = ['retweeted', 'replying to', 'quote tweet']
        if any(pattern in content_lower for pattern in avoid_patterns):
            return False
        
        # Must be substantial content
        if len(content.strip()) < 20:
            return False
        
        return True
    
    def _extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from Twitter URL"""
        import re
        
        # Match patterns like /status/1234567890
        pattern = r'/status/(\d+)'
        match = re.search(pattern, url)
        
        if match:
            return match.group(1)
        
        # Alternative patterns
        pattern = r'twitter\.com/\w+/status/(\d+)'
        match = re.search(pattern, url)
        
        if match:
            return match.group(1)
        
        return None
    
    def _clean_tweet_content(self, content: str) -> str:
        """Clean and format tweet content"""
        import re
        
        # Remove extra whitespace and line breaks
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Remove common web scraping artifacts
        artifacts = [
            'Show this thread',
            'Show more',
            'Translate Tweet',
            'View Tweet activity',
            'Embed Tweet',
            'Copy link to Tweet'
        ]
        
        for artifact in artifacts:
            content = content.replace(artifact, '').strip()
        
        # Limit length but preserve readability
        if len(content) > 250:
            content = content[:247] + '...'
        
        return content
    
    def _extract_timestamp(self, result: Dict[str, Any]) -> str:
        """Extract readable timestamp from result"""
        timestamp = result.get('timestamp', '')
        
        if timestamp:
            return timestamp
        
        # Try to extract from content or URL
        content = result.get('content', '')
        if 'ago' in content.lower():
            import re
            time_pattern = r'(\d+[hm]?\s*ago)'
            match = re.search(time_pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'Recent'
    
    def _calculate_real_engagement_score(self, result: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """Calculate engagement score for real posts"""
        base_score = profile.get('influence_score', 8.0)
        
        # Boost score based on content indicators
        content = result.get('content', '').lower()
        
        # High engagement indicators
        if any(word in content for word in ['breaking', 'just', 'new', 'update']):
            base_score += 0.5
        
        # Question posts tend to get more engagement
        if '?' in content:
            base_score += 0.3
        
        # Controversial or strong opinions
        if any(word in content for word in ['wrong', 'mistake', 'disagree', 'unpopular']):
            base_score += 0.4
        
        return min(base_score, 9.9)  # Cap at 9.9
    
    def _fetch_from_rss_feed(self, username: str, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch posts using RSS.app feed"""
        try:
            import requests
            import xml.etree.ElementTree as ET
            from datetime import datetime
            import re
            
            # Load RSS feeds from config file
            known_feeds = self._load_rss_feeds()
            
            # Try multiple RSS feed approaches
            rss_urls = []
            if username in known_feeds:
                rss_urls.append(known_feeds[username])
            
            # Alternative RSS services
            rss_urls.extend([
                f"https://nitter.net/{username}/rss",  # Nitter RSS (if available)
                f"https://twitrss.me/twitter_user_to_rss/?user={username}",  # TwitRSS
            ])
            
            opportunities = []
            
            for rss_url in rss_urls:
                try:
                    logger.info(f"🔍 Trying RSS feed: {rss_url}")
                    
                    response = requests.get(rss_url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; TwitterBot/1.0)'
                    })
                    
                    if response.status_code == 200:
                        # Parse RSS/XML
                        root = ET.fromstring(response.content)
                        
                        # Handle different RSS formats
                        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
                        
                        for item in items[:3]:  # Limit to 3 most recent
                            # Use helper method for safe XML text extraction
                            title = self._get_xml_text(item, 'title') or self._get_xml_text(item, '{http://www.w3.org/2005/Atom}title')
                            description = self._get_xml_text(item, 'description') or self._get_xml_text(item, '{http://www.w3.org/2005/Atom}content')
                            link = self._get_xml_text(item, 'link') or self._get_xml_text(item, '{http://www.w3.org/2005/Atom}link')
                            pub_date = self._get_xml_text(item, 'pubDate') or self._get_xml_text(item, '{http://www.w3.org/2005/Atom}published')
                            
                            # Clean and extract tweet content
                            tweet_content = self._extract_tweet_from_rss(title, description)
                            
                            if tweet_content and len(tweet_content.strip()) > 10:
                                # Extract tweet ID from link
                                tweet_id = self._extract_tweet_id_from_link(link)
                                proper_tweet_url = f"https://x.com/{username}/status/{tweet_id}" if tweet_id else link
                                
                                # Parse timestamp
                                timestamp = self._parse_rss_timestamp(pub_date)
                                
                                opportunity = {
                                    'author': profile['name'],
                                    'handle': profile['username'],
                                    'category': profile['category'],
                                    'content': tweet_content[:300],
                                    'url': link,
                                    'tweet_link': proper_tweet_url,
                                    'timestamp': timestamp,
                                    'engagement_strategy': profile.get('engagement_style', 'Professional commentary'),
                                    'engagement_score': self._calculate_real_engagement_score({'content': tweet_content}, profile),
                                    'posting_time': datetime.now().strftime('%Y-%m-%d'),
                                    'is_real_post': True,
                                    'source': 'RSS'
                                }
                                
                                opportunities.append(opportunity)
                                logger.info(f"✅ Found RSS post from {username}: {tweet_content[:50]}...")
                        
                        if opportunities:
                            break  # Found good RSS feed, stop trying others
                            
                except Exception as e:
                    logger.debug(f"RSS feed failed {rss_url}: {e}")
                    continue
            
            return opportunities
            
        except Exception as e:
            logger.warning(f"RSS fetch failed for {username}: {e}")
            return []
    
    def _get_xml_text(self, element, tag):
        """Safely get text from XML element"""
        try:
            child = element.find(tag)
            return child.text if child is not None else None
        except:
            return None
    
    def _extract_tweet_from_rss(self, title, description):
        """Extract clean tweet content from RSS title/description"""
        try:
            import re  # Import at the top
            
            # Try title first (usually cleaner)
            if title and not title.startswith('RT by'):
                # Remove common RSS artifacts
                content = title.replace('— Naval (@naval)', '').strip()
                content = re.sub(r'— \w+ \(@\w+\)', '', content).strip()  # Remove signature
                content = re.sub(r'@\w+:?', '', content).strip()  # Remove mentions at start
                if len(content) > 10:
                    return content
            
            # Fallback to description
            if description:
                # Remove HTML tags and CDATA
                content = re.sub(r'<.*?>', '', description)
                content = re.sub(r'<!\[CDATA\[|\]\]>', '', content)
                content = re.sub(r'— \w+ \(@\w+\)', '', content).strip()  # Remove signature
                
                # Remove common artifacts
                artifacts = ['pic.twitter.com/', 'https://t.co/', 'Show this thread', 'Translate Tweet']
                for artifact in artifacts:
                    if artifact in content:
                        content = content.split(artifact)[0].strip()
                
                if len(content) > 10:
                    return content
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting tweet content: {e}")
            return None
    
    def _extract_tweet_id_from_link(self, link):
        """Extract tweet ID from RSS link"""
        try:
            if not link:
                return None
            
            import re
            # Match patterns like /status/1234567890
            pattern = r'/status/(\d+)'
            match = re.search(pattern, link)
            
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting tweet ID from link: {e}")
            return None
    
    def _parse_rss_timestamp(self, pub_date):
        """Parse RSS timestamp to readable format"""
        try:
            if not pub_date:
                return 'Recent'
            
            from datetime import datetime
            import re
            
            # Try to parse common RSS timestamp formats
            try:
                # RFC 2822 format: Wed, 02 Sep 2025 07:27:00 GMT
                dt = datetime.strptime(pub_date.split(' GMT')[0].split(' +')[0], '%a, %d %b %Y %H:%M:%S')
                return dt.strftime('%b %d, %I:%M %p')
            except:
                pass
            
            # Extract relative time if available
            if 'ago' in pub_date.lower():
                return pub_date
            
            # Extract date part
            date_match = re.search(r'(\d{1,2} \w+ \d{4})', pub_date)
            if date_match:
                return date_match.group(1)
            
            return 'Recent'
            
        except Exception as e:
            logger.debug(f"Error parsing timestamp: {e}")
            return 'Recent'
    
    def _fetch_from_web_scraping(self, username: str, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to web scraping when RSS fails"""
        try:
            from datetime import datetime
            
            # Simplified web scraping approach
            search_queries = [
                f"\"{profile['name']}\" twitter quote recent",
                f"{username} latest tweet news",
                f"\"{profile['name']}\" statement September 2025"
            ]
            
            opportunities = []
            
            for query in search_queries[:2]:  # Limit attempts
                try:
                    results = self.web_scraper.search_and_scrape(
                        query=query,
                        max_results=2,
                        scrape_content=True
                    )
                    
                    for result in results:
                        content = result.get('content', '')
                        if len(content.strip()) > 20:
                            opportunity = {
                                'author': profile['name'],
                                'handle': profile['username'],
                                'category': profile['category'],
                                'content': self._clean_tweet_content(content)[:300],
                                'url': result.get('url', ''),
                                'tweet_link': result.get('url', ''),
                                'timestamp': self._extract_timestamp(result),
                                'engagement_strategy': profile.get('engagement_style', 'Professional commentary'),
                                'engagement_score': self._calculate_real_engagement_score(result, profile),
                                'posting_time': datetime.now().strftime('%Y-%m-%d'),
                                'is_real_post': True,
                                'source': 'Web Scraping'
                            }
                            opportunities.append(opportunity)
                            break
                    
                    if opportunities:
                        break
                        
                except Exception as e:
                    logger.debug(f"Web scraping failed for query '{query}': {e}")
                    continue
            
            return opportunities
            
        except Exception as e:
            logger.warning(f"Web scraping fallback failed for {username}: {e}")
            return []
    
    def _load_rss_feeds(self) -> Dict[str, str]:
        """Load RSS feed URLs from config file"""
        try:
            import yaml
            from pathlib import Path
            
            config_file = Path(__file__).parent.parent / "config" / "rss_feeds.yml"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('rss_feeds', {})
            else:
                logger.warning(f"RSS feeds config not found: {config_file}")
                return {}
                
        except Exception as e:
            logger.warning(f"Error loading RSS feeds config: {e}")
            return {}
    
    def analyze_profile_strategy(self, username: str) -> Dict[str, Any]:
        """Analyze a specific profile's posting and engagement strategy"""
        
        try:
            # Find target profile
            profile = next((p for p in self.target_profiles if p['username'] == username), None)
            
            if not profile:
                logger.warning(f"Profile not found: {username}")
                return self._get_generic_profile_analysis(username)
            
            # Generate comprehensive analysis
            analysis = {
                'profile': profile,
                'posting_strategy': self._analyze_posting_strategy(profile),
                'engagement_strategy': self._analyze_engagement_strategy(profile),
                'content_frameworks': self._extract_content_frameworks(profile),
                'key_insights': self._generate_key_insights(profile),
                'recommendations': self._generate_recommendations(profile)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing profile {username}: {e}")
            return self._get_generic_profile_analysis(username)
    
    def get_posting_schedule_insights(self) -> Dict[str, Any]:
        """Get insights about optimal posting schedules based on target profiles"""
        
        return {
            'optimal_times': {
                'morning': '9:00-11:00 AM IST',
                'afternoon': '2:00-4:00 PM IST', 
                'evening': '7:00-9:00 PM IST'
            },
            'posting_frequency': {
                'recommended': '2-3 posts per day',
                'max_daily': '5 posts per day',
                'engagement_posts': '10-15 replies per day'
            },
            'content_distribution': {
                'educational': '40%',
                'personal_insights': '30%',
                'industry_commentary': '20%',
                'interactive': '10%'
            },
            'engagement_best_practices': [
                'Respond within 30 minutes for maximum visibility',
                'Add unique technical perspective to trending topics',
                'Use specific metrics and data points when available',
                'Ask thought-provoking questions to encourage discussion',
                'Share behind-the-scenes insights from professional experience'
            ]
        }
    
    def _generate_profile_opportunities(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock engagement opportunities for a profile"""
        
        opportunities = []
        
        # Generate 2-3 opportunities per profile
        for i in range(random.randint(2, 3)):
            opportunity = self._create_mock_opportunity(profile, i)
            opportunities.append(opportunity)
        
        return opportunities
    
    def _create_mock_opportunity(self, profile: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a mock engagement opportunity"""
        
        # Diverse content samples based on profile categories and influence styles
        content_samples = {
            # Tech Leaders
            '@alliekmiller': [
                "AI is reshaping how we think about product strategy. The companies that adapt fastest will lead the next decade.",
                "Just saw another 'AI will replace developers' post. Here's why that's missing the bigger picture...",
                "The gap between AI hype and AI reality is shrinking fast. What are you seeing in your industry?"
            ],
            '@mattshumer_': [
                "Optimized our AI pipeline: 10x throughput improvement, 60% cost reduction. The key was changing how we think about batching.",
                "Most teams are implementing AI backwards. Start with the business problem, not the technology.",
                "Spent 6 months building an AI feature users didn't want. Here's what I learned about product-market fit..."
            ],
            
            # VCs and Angel Investors
            '@sama': [
                "AGI timeline predictions are mostly noise. What matters is building infrastructure for when it arrives.",
                "The most important startups of the next decade will be ones that seem impossible today.",
                "OpenAI's success isn't just about better models—it's about making AI accessible to everyone."
            ],
            '@naval': [
                "Wealth creation has nothing to do with luck. It's about understanding leverage, judgment, and specific knowledge.",
                "The internet destroyed gatekeepers. AI will destroy the gatekeepers of knowledge work.",
                "Most people optimize for looking smart. Winners optimize for being effective."
            ],
            '@balajis': [
                "The network state isn't just a concept—it's happening in real time through crypto, remote work, and digital communities.",
                "Traditional metrics miss the story. Look at on-chain data, GitHub commits, and real-time sentiment.",
                "Geographic arbitrage + technological leverage = the new wealth creation formula."
            ],
            '@chrissacca': [
                "Climate tech is where internet was in 1995. Massive opportunity, but timing and execution are everything.",
                "The best investments feel obvious in retrospect and crazy at the time of investment.",
                "Portfolio construction is risk management. Concentration is wealth creation. Know which game you're playing."
            ],
            
            # Micro VCs and Emerging Investors
            '@harryhurst': [
                "SaaS metrics everyone tracks: MRR, churn, CAC. Metrics that actually matter: time to value, expansion rate, founder conviction.",
                "Micro VC isn't just smaller checks. It's faster decisions, operator experience, and hands-on value creation.",
                "Best founders don't need convincing on market size. They need help with go-to-market and scaling operations."
            ],
            '@justinkan': [
                "Building in public forced me to be honest about what wasn't working. Best accountability system ever created.",
                "Community isn't just marketing—it's product development, customer success, and competitive moat rolled into one.",
                "The hardest part of entrepreneurship isn't the failures. It's staying motivated through the long middle."
            ],
            
            # AI Thought Leaders
            '@ylecun': [
                "LLMs are just one piece of intelligence. True AI needs reasoning, planning, and world models.",
                "The hype around current AI capabilities is both excessive and insufficient. We're overestimating short-term, underestimating long-term.",
                "Self-supervised learning from video will unlock the next breakthrough in AI understanding."
            ],
            '@AndrewYNg': [
                "AI transformation isn't about technology—it's about workflow redesign and organizational change.",
                "Every company will need an AI strategy. Start with small pilots, measure impact, then scale systematically.",
                "The future belongs to teams that combine domain expertise with AI capabilities, not AI experts alone."
            ],
            '@karpathy': [
                "The most underrated skill in AI: debugging neural networks. It's part art, part science, all patience.",
                "Foundation models are incredible, but the real value is in the application layer and fine-tuning for specific domains.",
                "AI safety isn't just about alignment—it's about building robust, interpretable, and controllable systems."
            ],
            
            # Startup Ecosystem
            '@paulg': [
                "The best startup ideas seem obvious in retrospect. They're hiding in plain sight because everyone thinks someone must have tried it.",
                "Fundraising is a tax on startups. Minimize time spent on it and get back to building and talking to users.",
                "Default alive vs default dead. Every startup decision should be evaluated through this lens."
            ],
            '@jessicamliving': [
                "Founder mental health is the most underinvested area in startup success. Resilience compounds everything else.",
                "The best startup stories aren't about overnight success—they're about persistence through seemingly impossible odds.",
                "Y Combinator's secret isn't the money or network. It's giving founders permission to think bigger."
            ],
            '@agazdecki': [
                "SaaS acquisition multiples are compressing, but quality businesses are still getting premium valuations.",
                "Bootstrap to $1M ARR, then decide if you want to stay independent or scale with capital. Both paths are valid.",
                "The best time to think about exit strategy is before you need one. Optionality is leverage."
            ],
            
            # Twitter/X Platform Masters  
            '@elonmusk': [
                "First principles thinking: ignore conventional wisdom and build from basic truths.",
                "X will become the everything app. Banking, social, commerce, news—all in one platform.",
                "Mars colonization isn't optional. It's an insurance policy for consciousness itself."
            ],
            '@levelsio': [
                "Revenue transparency builds trust and accountability. Here's exactly how much NomadList made last month...",
                "Remote work killed geography as competitive advantage. Skills and execution are the only moats left.",
                "Indie hacking is just entrepreneurship without the VC theater. Build, launch, iterate, repeat."
            ],
            '@dharmesh': [
                "Growth tactics change. Growth principles are eternal: solve real problems for real people.",
                "HubSpot's biggest insight: marketing and sales alignment isn't nice-to-have—it's survival.",
                "The best SaaS companies don't just track metrics. They understand the stories metrics tell."
            ],
            
            # Content Creators and Analysts
            '@benthompson': [
                "Platform business models create winner-take-all dynamics. Understand the flywheel or get disrupted by it.",
                "Strategy isn't about what you choose to do. It's about what you choose not to do.",
                "The internet rewards scale and quality. Everything else is temporary competitive advantage."
            ],
            '@caseynewton': [
                "Platform governance isn't just policy—it's the architecture of digital democracy.",
                "Creator economy success stories hide the vast majority who can't make sustainable income.",
                "Tech journalism's job isn't just reporting what happened. It's explaining why it matters."
            ]
        }
        
        username = profile['username']
        contents = content_samples.get(username, [
            f"Interesting insights about the future of {profile.get('expertise', 'technology')} and its impact on business.",
            f"Sharing lessons learned from {profile.get('engagement_style', 'building products at scale')}.",
            f"The intersection of {random.choice(profile.get('content_themes', ['AI', 'technology']))} and practical business applications continues to evolve."
        ])
        
        content = random.choice(contents)
        
        # Calculate engagement score based on profile influence and category
        influence_score = profile.get('influence_score', 8.0)
        category = profile.get('category', 'tech_leaders')
        
        # Base score influenced by profile influence
        base_score = int(influence_score * 10) + random.randint(-10, 15)
        base_score = min(max(base_score, 70), 98)  # Clamp between 70-98
        
        # Category-based adjustments
        category_multipliers = {
            'investors': 1.1,        # VCs get higher engagement
            'twitter_masters': 1.15, # Platform masters get highest
            'ai_leaders': 1.05,      # AI leaders get slight boost
            'startup_ecosystem': 1.08, # Startup ecosystem gets boost
            'content_creators': 1.02,  # Content creators slight boost
            'micro_vcs': 1.0,        # Baseline
            'tech_leaders': 1.0      # Baseline
        }
        
        multiplier = category_multipliers.get(category, 1.0)
        base_score = int(base_score * multiplier)
        base_score = min(base_score, 99)  # Final cap
        
        # Dynamic time-based scoring (higher influence = more recent)
        if influence_score >= 9.5:
            hours_ago = random.randint(1, 3)  # High influence = very recent
        elif influence_score >= 9.0:
            hours_ago = random.randint(1, 4)  # Good influence = recent
        else:
            hours_ago = random.randint(2, 6)  # Lower influence = less recent
            
        timing_desc = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"
        
        # Dynamic reach estimation based on follower range and influence
        follower_range = profile.get('follower_range', '100K-500K')
        if '150M+' in follower_range or '2M+' in follower_range:
            estimated_reach = random.randint(50000, 150000)
        elif '1M+' in follower_range or '1.8M+' in follower_range:
            estimated_reach = random.randint(25000, 75000)
        elif '500K+' in follower_range or '900K+' in follower_range:
            estimated_reach = random.randint(15000, 45000)
        elif '100K-500K' in follower_range or '200K+' in follower_range:
            estimated_reach = random.randint(8000, 25000)
        else:
            estimated_reach = random.randint(3000, 15000)
        
        # Clean username for URL generation
        username_clean = username.replace('@', '')
        
        return {
            'author': profile.get('name', profile.get('focus', 'Tech Expert')),
            'handle': username,  # Keep the @username format
            'category': category,
            'content': content,
            'engagement_score': base_score,
            'timing': timing_desc,
            'profile_expertise': profile.get('expertise', profile.get('focus', 'Technology')),
            'profile_category': category,
            'influence_score': influence_score,
            'follower_range': follower_range,
            'estimated_reach': estimated_reach,
            'reply_potential': 'Very High' if base_score > 90 else 'High' if base_score > 80 else 'Medium',
            'content_theme': random.choice(profile.get('content_themes', ['Technology', 'Business', 'Innovation'])),
            'engagement_style': profile.get('engagement_style', 'Professional insights'),
            'posting_frequency': profile.get('posting_frequency', 'Regular posting'),
            'posting_time': datetime.now().strftime('%b %d, %I:%M %p'),
            'tweet_link': f"https://twitter.com/{username_clean}",  # Profile link as fallback
            'url': f"https://twitter.com/{username_clean}",
            'timestamp': datetime.now().isoformat(),
            'is_mock': True,
            'source': 'ProfileFallback'
        }
    
    def _analyze_posting_strategy(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze posting strategy for a profile"""
        
        strategies = {
            '@alliekmiller': {
                'frequency': 'High-frequency thought leadership',
                'timing': 'Multiple posts throughout business hours',
                'content_mix': '60% insights, 25% predictions, 15% personal',
                'engagement_approach': 'Authoritative voice with data backing',
                'hashtag_strategy': 'Strategic use of AI/ML hashtags',
                'thread_usage': 'Frequent detailed threads on complex topics'
            },
            '@mattshumer_': {
                'frequency': 'Consistent daily posting with quality focus',
                'timing': 'Strategic timing for maximum developer reach',
                'content_mix': '50% technical content, 30% metrics, 20% lessons learned',
                'engagement_approach': 'Data-driven insights with specific examples',
                'hashtag_strategy': 'Minimal hashtags, strong organic reach',
                'thread_usage': 'Detailed technical explanations and tutorials'
            },
            '@officiallogank': {
                'frequency': 'High engagement with community focus',
                'timing': 'Consistent posting during peak developer hours',
                'content_mix': '40% education, 30% community, 20% product, 10% personal',
                'engagement_approach': 'Accessible explanations with community building',
                'hashtag_strategy': 'Community-focused hashtags',
                'thread_usage': 'Educational threads and transparent sharing'
            }
        }
        
        return strategies.get(profile['username'], {
            'frequency': 'Regular posting schedule',
            'timing': 'Business hours focus',
            'content_mix': 'Mix of professional and educational content',
            'engagement_approach': 'Professional thought leadership',
            'hashtag_strategy': 'Strategic hashtag usage',
            'thread_usage': 'Occasional detailed threads'
        })
    
    def _analyze_engagement_strategy(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement strategy for a profile"""
        
        strategies = {
            '@alliekmiller': {
                'reply_frequency': 'Selective but high-value responses',
                'community_building': 'Thought leadership through authoritative responses',
                'collaboration_style': 'Engages with other industry leaders',
                'question_asking': 'Poses strategic questions to provoke discussion',
                'value_addition': 'Adds unique AI/ML perspective to conversations'
            },
            '@mattshumer_': {
                'reply_frequency': 'Active engagement with technical discussions',
                'community_building': 'Shares concrete examples and metrics',
                'collaboration_style': 'Collaborative problem-solving approach',
                'question_asking': 'Asks specific technical questions',
                'value_addition': 'Provides data-backed insights and solutions'
            },
            '@officiallogank': {
                'reply_frequency': 'High engagement with educational focus',
                'community_building': 'Active community participation and support',
                'collaboration_style': 'Inclusive and educational responses',
                'question_asking': 'Asks questions to understand community needs',
                'value_addition': 'Makes complex topics accessible'
            }
        }
        
        return strategies.get(profile['username'], {
            'reply_frequency': 'Regular engagement',
            'community_building': 'Professional networking',
            'collaboration_style': 'Thoughtful responses',
            'question_asking': 'Strategic questioning',
            'value_addition': 'Adds professional perspective'
        })
    
    def _extract_content_frameworks(self, profile: Dict[str, Any]) -> List[str]:
        """Extract content frameworks used by the profile"""
        
        frameworks = {
            '@alliekmiller': [
                'Prediction + Data + Implication framework',
                'Problem + AI Solution + Business Impact',
                'Current State + Future Vision + Action Steps',
                'Industry Trend + Personal Analysis + Recommendation'
            ],
            '@mattshumer_': [
                'Problem + Technical Solution + Metrics',
                'Before + After + Methodology',
                'Challenge + Approach + Results + Lessons',
                'Technical Concept + Practical Application + Performance Data'
            ],
            '@officiallogank': [
                'Complex Topic + Simple Explanation + Practical Example',
                'Community Question + Educational Response + Resource Sharing',
                'Product Update + Developer Impact + Implementation Guide',
                'Industry Change + Community Implication + Support Resources'
            ]
        }
        
        return frameworks.get(profile['username'], [
            'Professional Insight + Supporting Evidence + Call to Action',
            'Industry Observation + Personal Experience + Recommendation',
            'Problem Statement + Solution Approach + Key Takeaways'
        ])
    
    def _generate_key_insights(self, profile: Dict[str, Any]) -> List[str]:
        """Generate key insights about the profile's strategy"""
        
        insights = {
            '@alliekmiller': [
                'Establishes thought leadership through bold predictions backed by data',
                'Uses authoritative voice to drive industry conversations',
                'Balances technical depth with business accessibility',
                'Leverages AI expertise to provide unique perspectives on trends'
            ],
            '@mattshumer_': [
                'Focuses on concrete metrics and measurable outcomes',
                'Shares real implementation details and performance data',
                'Builds credibility through transparent problem-solving',
                'Emphasizes practical applications over theoretical concepts'
            ],
            '@officiallogank': [
                'Prioritizes community education and accessibility',
                'Makes complex technical concepts understandable',
                'Builds trust through transparent communication',
                'Focuses on developer success and community building'
            ]
        }
        
        return insights.get(profile['username'], [
            'Maintains consistent professional voice across all content',
            'Balances expertise with approachable communication style',
            'Engages authentically with community and industry topics',
            'Provides valuable insights based on professional experience'
        ])
    
    def _generate_recommendations(self, profile: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on profile analysis"""
        
        recommendations = {
            '@alliekmiller': [
                'Adopt authoritative tone when discussing AI/ML trends',
                'Back opinions with specific data points and metrics',
                'Make bold but educated predictions about industry direction',
                'Engage with other thought leaders to amplify reach'
            ],
            '@mattshumer_': [
                'Share specific metrics and performance improvements',
                'Provide concrete implementation details and methodologies',
                'Use before/after comparisons to demonstrate value',
                'Focus on practical applications over theoretical concepts'
            ],
            '@officiallogank': [
                'Simplify complex technical concepts for broader audience',
                'Prioritize educational value in all content',
                'Engage actively with community questions and feedback',
                'Share resources and tools that benefit the community'
            ]
        }
        
        return recommendations.get(profile['username'], [
            'Maintain consistent professional voice and expertise',
            'Share authentic insights from professional experience',
            'Engage thoughtfully with industry conversations',
            'Provide value through unique perspective and knowledge'
        ])
    
    def _get_fallback_opportunities(self, count: int) -> List[Dict[str, Any]]:
        """Get fallback opportunities if analysis fails"""
        
        fallback_opportunities = [
            {
                'author': '@tech_leader',
                'content': 'The future of AI in business is not about replacing humans, but augmenting human capability.',
                'engagement_score': 85,
                'timing': '2 hours ago',
                'reply_potential': 'High'
            },
            {
                'author': '@startup_founder',
                'content': 'Building a SaaS product taught me that customer feedback is worth more than any feature request.',
                'engagement_score': 78,
                'timing': '4 hours ago',
                'reply_potential': 'Medium'
            },
            {
                'author': '@product_expert',
                'content': 'Most product teams optimize for the wrong metrics. Start with user value, not engagement.',
                'engagement_score': 82,
                'timing': '1 hour ago',
                'reply_potential': 'High'
            }
        ]
        
        return fallback_opportunities[:count]
    
    def _get_generic_profile_analysis(self, username: str) -> Dict[str, Any]:
        """Get generic profile analysis"""
        
        return {
            'profile': {
                'username': username,
                'name': 'Professional User',
                'expertise': 'Industry Professional',
                'engagement_style': 'Professional thought leadership'
            },
            'posting_strategy': {
                'frequency': 'Regular posting schedule',
                'timing': 'Business hours focus',
                'content_mix': 'Professional insights and industry commentary'
            },
            'engagement_strategy': {
                'reply_frequency': 'Active professional engagement',
                'value_addition': 'Adds professional perspective to discussions'
            },
            'key_insights': [
                'Maintains professional voice across content',
                'Engages authentically with industry topics',
                'Provides valuable insights from experience'
            ],
            'recommendations': [
                'Share unique professional perspective',
                'Engage thoughtfully with industry conversations',
                'Provide value through expertise and experience'
            ]
        }
