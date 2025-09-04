#!/usr/bin/env python3
"""
Trend Analyzer
Analyzes trending topics and identifies viral opportunities
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from .unified_client import UnifiedAIClient
from .web_scraper import WebScraper

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """Analyzes trends and identifies content opportunities"""
    
    def __init__(self, config):
        """Initialize trend analyzer"""
        self.config = config
        self.ai_client = UnifiedAIClient(config)
        
        # Initialize web scraper for comprehensive content research
        try:
            self.web_scraper = WebScraper(config)
            self.searxng_enabled = True
            logger.info("📈 Trend Analyzer initialized with web scraping capabilities")
        except Exception as e:
            self.web_scraper = None
            self.searxng_enabled = False
            logger.info(f"📈 Web scraper not available: {e} - using fallback data")
        
        logger.info("📈 Trend Analyzer initialized")
    
    def analyze_current_trends(self, 
                             categories: Optional[List[str]] = None,
                             focus_areas: Optional[List[str]] = None,
                             time_range: str = 'day') -> Dict[str, Any]:
        """Analyze current trending topics with enhanced real-time focus"""
        
        if not categories:
            # Optimized categories for faster performance
            categories = ['ai', 'technology', 'startup', 'venture capital', 'fintech', 'developer tools']
        
        if not focus_areas:
            # Dynamic focus areas based on current tech landscape
            focus_areas = [
                'generative ai', 'llm applications', 'agi development',
                'startup funding', 'creator economy', 'web3',
                'climate solutions', 'space tech', 'quantum computing', 'biotech',
                'developer productivity', 'no-code tools', 'api economy'
            ]
        
        trends_data = {}
        current_time = datetime.utcnow()
        
        # Gather trend data concurrently for better performance
        trends_data = self._get_trends_concurrently(categories, time_range)
        
        # Enhanced focus area analysis (concurrent)
        focus_trends = self._get_focus_trends_concurrently(focus_areas[:5], time_range)
        
        # Analyze with AI using enhanced context
        ai_analysis = self._analyze_trends_with_ai(trends_data, focus_trends, current_time)
        
        # Get real-time viral opportunities
        viral_opportunities = self._identify_viral_opportunities(trends_data, focus_trends)
        
        return {
            'timestamp': current_time.isoformat(),
            'time_range': time_range,
            'raw_trends': trends_data,
            'focus_area_trends': focus_trends,
            'ai_analysis': ai_analysis,
            'viral_opportunities': viral_opportunities,
            'recommendations': self._generate_recommendations(ai_analysis),
            'trending_hashtags': self.get_trending_hashtags(limit=15),
            'market_context': self._get_market_context(current_time)
        }
    
    def _get_category_trends(self, category: str, time_range: str = 'day') -> List[Dict[str, Any]]:
        """Get trending topics for a specific category using web scraping"""
        
        if not self.searxng_enabled or not self.web_scraper:
            logger.info(f"Using curated trends for {category}")
            return self._get_mock_trends(category)
        
        try:
            # Enhanced search queries with time sensitivity
            current_year = datetime.now().strftime('%Y')
            current_month = datetime.now().strftime('%B %Y')
            
            # Get current date info for more specific queries
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_day = datetime.now().strftime('%A')
            
            time_queries = {
                'hour': f"{category} breaking news {current_date} today",
                'day': f"{category} latest news {current_date} {current_day}",
                'week': f"{category} this week {current_month} recent",
                'month': f"{category} {current_month} latest developments"
            }
            
            search_query = time_queries.get(time_range, f"{category} trends {current_year}")
            
            logger.info(f"🕷️ Scraping {time_range} trends for {category}: {search_query}")
            
            trends = self.web_scraper.search_and_scrape(
                query=search_query,
                categories=['news', 'tech', 'business'],
                max_results=10,
                scrape_content=True
            )
            
            if trends:
                # Enhance trends with time-based scoring
                enhanced_trends = self._enhance_with_time_scoring(trends, time_range)
                logger.info(f"✅ Found {len(enhanced_trends)} enriched {time_range} trends for {category}")
                return enhanced_trends
            else:
                logger.info(f"No web trends found for {category}, using fallback")
                return self._get_mock_trends(category)
                
        except Exception as e:
            logger.warning(f"Web scraping failed for {category}: {e}")
            return self._get_mock_trends(category)
    
    def _get_trends_concurrently(self, categories: List[str], time_range: str) -> Dict[str, List]:
        """Get trends for multiple categories concurrently"""
        
        trends_data = {}
        
        # Use ThreadPoolExecutor for concurrent trend fetching
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all category trend fetching tasks
            future_to_category = {
                executor.submit(self._get_category_trends, category, time_range): category 
                for category in categories
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    category_trends = future.result(timeout=120)  # 2 minute timeout per category
                    trends_data[category] = category_trends
                    logger.info(f"✅ Completed trends for {category}: {len(category_trends)} results")
                except Exception as e:
                    logger.warning(f"❌ Failed to get trends for {category}: {e}")
                    trends_data[category] = []
        
        return trends_data
    
    def _get_focus_trends_concurrently(self, focus_areas: List[str], time_range: str) -> Dict[str, List]:
        """Get focus area trends concurrently"""
        
        focus_trends = {}
        
        # Use ThreadPoolExecutor for concurrent focus area trend fetching
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all focus area trend fetching tasks
            future_to_focus = {
                executor.submit(self._get_focus_area_trends, focus, time_range): focus 
                for focus in focus_areas
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_focus):
                focus = future_to_focus[future]
                try:
                    focus_trends_result = future.result(timeout=90)  # 90 second timeout per focus
                    focus_trends[focus] = focus_trends_result
                    logger.info(f"✅ Completed focus trends for {focus}: {len(focus_trends_result)} results")
                except Exception as e:
                    logger.warning(f"❌ Failed to get focus trends for {focus}: {e}")
                    focus_trends[focus] = []
        
        return focus_trends
    
    def _get_focus_area_trends(self, focus_area: str, time_range: str = 'day') -> List[Dict[str, Any]]:
        """Get trends for specific focus areas with enhanced targeting"""
        
        if not self.searxng_enabled or not self.web_scraper:
            return self._get_mock_focus_trends(focus_area)
        
        try:
            # Enhanced focus area queries with current date specificity
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_month = datetime.now().strftime('%B %Y')
            
            focus_queries = {
                'generative ai': f"generative AI breakthroughs {current_date}",
                'llm applications': f"LLM use cases applications {current_month}",
                'ai safety': f"AI safety alignment research {current_date}",
                'startup funding': f"startup funding rounds {current_month}",
                'remote work': f"remote work trends productivity {current_date}",
                'creator economy': f"creator economy monetization {current_date}",
                'web3': f"web3 adoption enterprise {current_date}",
                'climate tech': f"climate technology solutions {current_date}",
                'space tech': f"space technology commercial {current_date}",
                'developer tools': f"developer productivity tools {current_date}"
            }
            
            search_query = focus_queries.get(focus_area, f"{focus_area} trends {datetime.now().strftime('%Y')}")
            
            trends = self.web_scraper.search_and_scrape(
                query=search_query,
                categories=['tech', 'business', 'news'],
                max_results=5,
                scrape_content=True
            )
            
            return self._enhance_with_focus_scoring(trends, focus_area) if trends else []
            
        except Exception as e:
            logger.warning(f"Focus area scraping failed for {focus_area}: {e}")
            return self._get_mock_focus_trends(focus_area)
    
    def _enhance_with_time_scoring(self, trends: List[Dict[str, Any]], time_range: str) -> List[Dict[str, Any]]:
        """Enhance trends with time-based relevance scoring"""
        
        time_multipliers = {
            'hour': 2.0,    # Recent news gets highest boost
            'day': 1.5,     # Daily trends get good boost
            'week': 1.2,    # Weekly trends get moderate boost
            'month': 1.0    # Monthly trends baseline
        }
        
        multiplier = time_multipliers.get(time_range, 1.0)
        
        for trend in trends:
            original_score = trend.get('score', 5.0)
            trend['score'] = min(original_score * multiplier, 10.0)
            trend['time_relevance'] = time_range
            trend['enhanced'] = True
            
        return sorted(trends, key=lambda x: x.get('score', 0), reverse=True)
    
    def _enhance_with_focus_scoring(self, trends: List[Dict[str, Any]], focus_area: str) -> List[Dict[str, Any]]:
        """Enhance trends with focus area relevance scoring"""
        
        focus_keywords = {
            'generative ai': ['gpt', 'claude', 'llm', 'generative', 'ai model'],
            'startup funding': ['funding', 'series', 'venture', 'investment', 'valuation'],
            'remote work': ['remote', 'hybrid', 'distributed', 'wfh', 'productivity'],
            'creator economy': ['creator', 'monetization', 'platform', 'content', 'influencer'],
            'climate tech': ['climate', 'carbon', 'renewable', 'sustainability', 'green tech']
        }
        
        keywords = focus_keywords.get(focus_area, [focus_area.split()[0]])
        
        for trend in trends:
            content = f"{trend.get('title', '')} {trend.get('content', '')}".lower()
            keyword_matches = sum(1 for keyword in keywords if keyword in content)
            
            # Boost score based on keyword relevance
            trend['score'] = trend.get('score', 5.0) + (keyword_matches * 0.5)
            trend['focus_relevance'] = keyword_matches
            trend['focus_area'] = focus_area
            
        return sorted(trends, key=lambda x: x.get('score', 0), reverse=True)
    
    def _identify_viral_opportunities(self, trends_data: Dict[str, List], 
                                   focus_trends: Dict[str, List]) -> List[Dict[str, Any]]:
        """Identify real-time viral opportunities from trends"""
        
        viral_opportunities = []
        
        # Collect all trends with high viral potential
        all_trends = []
        for category, trends in trends_data.items():
            for trend in trends:
                if trend.get('score', 0) > 7.0:  # High-scoring trends only
                    trend['source_category'] = category
                    all_trends.append(trend)
        
        for focus, trends in focus_trends.items():
            for trend in trends:
                if trend.get('score', 0) > 7.0:
                    trend['source_focus'] = focus
                    all_trends.append(trend)
        
        # Sort by viral potential and return top opportunities
        viral_trends = sorted(all_trends, key=lambda x: x.get('score', 0), reverse=True)[:10]
        
        for trend in viral_trends:
            viral_opportunities.append({
                'title': trend.get('title', ''),
                'content': trend.get('content', '')[:200],
                'viral_score': trend.get('score', 0),
                'source': trend.get('source_category', trend.get('source_focus', 'unknown')),
                'url': trend.get('url', ''),
                'published': trend.get('published', 'recent'),
                'viral_potential': 'Very High' if trend.get('score', 0) > 8.5 else 'High'
            })
        
        return viral_opportunities
    
    def _get_market_context(self, current_time: datetime) -> Dict[str, Any]:
        """Get current market context for trend analysis"""
        
        current_hour = current_time.hour
        current_day = current_time.strftime('%A')
        current_month = current_time.strftime('%B')
        
        return {
            'optimal_posting_time': self._get_optimal_posting_context(current_hour),
            'day_context': self._get_day_context(current_day),
            'seasonal_context': self._get_seasonal_context(current_month),
            'market_hours': 'business' if 9 <= current_hour <= 17 else 'after_hours',
            'engagement_prediction': self._predict_engagement_window(current_hour, current_day)
        }
    
    def _get_optimal_posting_context(self, hour: int) -> str:
        """Get optimal posting context based on time"""
        if 9 <= hour <= 11:
            return 'morning_peak'  # High engagement
        elif 14 <= hour <= 16:
            return 'afternoon_peak'  # High engagement
        elif 19 <= hour <= 21:
            return 'evening_peak'  # High engagement
        else:
            return 'off_peak'
    
    def _get_day_context(self, day: str) -> str:
        """Get day-based context"""
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        if day in weekdays:
            return 'business_day'
        else:
            return 'weekend'
    
    def _get_seasonal_context(self, month: str) -> str:
        """Get seasonal context"""
        contexts = {
            'January': 'new_year_planning', 'February': 'early_year_execution',
            'March': 'q1_wrap', 'April': 'spring_initiatives', 'May': 'mid_year_prep',
            'June': 'q2_wrap', 'July': 'summer_planning', 'August': 'late_summer',
            'September': 'back_to_business', 'October': 'q4_planning',
            'November': 'year_end_push', 'December': 'year_end_reflection'
        }
        return contexts.get(month, 'general')
    
    def _predict_engagement_window(self, hour: int, day: str) -> str:
        """Predict engagement level based on time and day"""
        if day in ['Saturday', 'Sunday']:
            return 'low' if hour < 10 or hour > 22 else 'medium'
        else:
            if 9 <= hour <= 11 or 14 <= hour <= 16 or 19 <= hour <= 21:
                return 'high'
            elif 12 <= hour <= 13 or 17 <= hour <= 18:
                return 'medium'
            else:
                return 'low'
    
    def _get_mock_focus_trends(self, focus_area: str) -> List[Dict[str, Any]]:
        """Generate mock trends for focus areas"""
        
        mock_focus_trends = {
            'generative ai': [
                {
                    'title': 'New Multimodal AI Model Breakthrough',
                    'content': 'Latest AI model combines text, image, and video understanding',
                    'score': 8.5, 'focus_area': focus_area
                }
            ],
            'startup funding': [
                {
                    'title': 'AI Startups Dominate Q4 Funding Rounds',
                    'content': 'Venture capital heavily investing in AI infrastructure',
                    'score': 8.2, 'focus_area': focus_area
                }
            ],
            'remote work': [
                {
                    'title': 'Hybrid Work Models Show 25% Productivity Increase',
                    'content': 'New research on optimal remote work configurations',
                    'score': 7.8, 'focus_area': focus_area
                }
            ]
        }
        
        return mock_focus_trends.get(focus_area, [])
    
    def _calculate_trend_score(self, result: Dict[str, Any]) -> float:
        """Calculate trend relevance score"""
        score = 0.0
        
        # Title relevance
        title = result.get('title', '').lower()
        trending_keywords = [
            'trend', 'viral', 'popular', 'breakthrough', 'innovation',
            'new', 'latest', 'emerging', 'disrupting', 'revolutionary'
        ]
        
        for keyword in trending_keywords:
            if keyword in title:
                score += 1.0
        
        # Content relevance
        content = result.get('content', '').lower()
        business_keywords = [
            'startup', 'business', 'tech', 'ai', 'ml', 'saas',
            'product', 'strategy', 'growth', 'scaling'
        ]
        
        for keyword in business_keywords:
            if keyword in content:
                score += 0.5
        
        # Recency boost
        published = result.get('publishedDate', '')
        if published:
            try:
                # Simple recency check
                if 'hour' in published or 'minute' in published:
                    score += 2.0
                elif 'day' in published:
                    score += 1.0
            except:
                pass
        
        return score
    
    def _analyze_trends_with_ai(self, trends_data: Dict[str, List], 
                              focus_trends: Dict[str, List], 
                              current_time: datetime) -> Dict[str, Any]:
        """Analyze trends using AI with enhanced context"""
        
        # Prepare data for AI analysis
        trend_summary = {}
        for category, trends in trends_data.items():
            if trends:
                trend_summary[category] = [
                    {
                        'title': trend['title'],
                        'score': trend['score'],
                        'category': trend.get('category', category),
                        'time_relevance': trend.get('time_relevance', 'unknown'),
                        'published': trend.get('published', 'recent')
                    }
                    for trend in trends[:5]  # Top 5 per category
                ]
        
        # Add focus area trends
        focus_summary = {}
        for focus, trends in focus_trends.items():
            if trends:
                focus_summary[focus] = [
                    {
                        'title': trend['title'],
                        'score': trend['score'],
                        'focus_area': trend.get('focus_area', focus),
                        'focus_relevance': trend.get('focus_relevance', 0)
                    }
                    for trend in trends[:3]  # Top 3 per focus
                ]
        
        # Get current context
        time_context = self._get_market_context(current_time)
        current_time_str = current_time.strftime('%A, %B %d, %Y at %I:%M %p UTC')
        
        prompt = f"""
Analyze the following trending topics and identify viral content opportunities for {self.config.brand.persona}:

CURRENT CONTEXT:
- Time: {current_time_str}
- Market Hours: {time_context['market_hours']}
- Engagement Window: {time_context['engagement_prediction']}
- Optimal Posting: {time_context['optimal_posting_time']}
- Seasonal Context: {time_context['seasonal_context']}

TRENDING DATA BY CATEGORY:
{trend_summary}

FOCUS AREA TRENDS:
{focus_summary}

EXPERTISE AREAS:
{', '.join(self.config.brand.expertise_areas)}

TARGET HASHTAGS:
{', '.join(self.config.brand.target_hashtags)}

TASK: Identify the top 5 trending opportunities that align with expertise areas and have high viral potential, considering current timing and market context.

OUTPUT FORMAT (JSON):
{{
  "top_opportunities": [
    {{
      "trend_topic": "Specific trending topic with real-time relevance",
      "viral_potential": 9.2,
      "alignment_score": 8.5,
      "content_angle": "Unique professional perspective that leverages current timing",
      "timing_urgency": "immediate/within_6_hours/today/this_week",
      "hashtags": ["#relevant", "#hashtags"],
      "content_ideas": ["Specific post idea 1", "Specific post idea 2", "Specific post idea 3"],
      "engagement_strategy": "How to maximize engagement with this trend",
      "why_now": "Why this trend is viral-ready right now"
    }}
  ],
  "trend_themes": [
    "Current dominant theme in tech/business",
    "Emerging theme with growth potential", 
    "Seasonal/timing-based theme"
  ],
  "real_time_insights": [
    "Market timing insight",
    "Audience behavior pattern",
    "Competitive landscape observation"
  ],
  "recommendations": [
    "Immediate action (next 2 hours)",
    "Short-term strategy (today/tomorrow)",
    "Medium-term positioning (this week)"
  ]
}}

Focus on trends with immediate viral potential, strong professional alignment, and optimal timing for current market conditions.
"""

        try:
            response = self.ai_client.generate_content(prompt)
            
            if "error" in response:
                logger.error(f"AI trend analysis failed: {response['error']}")
                return self._fallback_analysis()
            
            return response
            
        except Exception as e:
            logger.error(f"Error in AI trend analysis: {e}")
            return self._fallback_analysis()
    
    def _generate_recommendations(self, ai_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Extract recommendations from AI analysis
        if 'recommendations' in ai_analysis:
            recommendations.extend(ai_analysis['recommendations'])
        
        # Add general recommendations
        recommendations.extend([
            "Monitor trending hashtags daily for emerging opportunities",
            "Engage with high-viral-potential posts within 2 hours of posting",
            "Create content that adds unique professional perspective to trends",
            "Use data and specific examples to stand out from generic content"
        ])
        
        return recommendations
    
    def _get_mock_trends(self, category: str) -> List[Dict[str, Any]]:
        """Generate mock trends for testing"""
        
        mock_trends = {
            'technology': [
                {
                    'title': 'AI Breakthrough in Natural Language Processing',
                    'url': 'https://example.com/ai-breakthrough',
                    'content': 'New AI model shows significant improvements in understanding context',
                    'published': '2 hours ago',
                    'score': 8.5,
                    'category': category
                },
                {
                    'title': 'Quantum Computing Milestone Achieved',
                    'url': 'https://example.com/quantum-computing',
                    'content': 'Research team demonstrates quantum advantage in practical applications',
                    'published': '4 hours ago',
                    'score': 7.8,
                    'category': category
                }
            ],
            'business': [
                {
                    'title': 'Remote Work Productivity Study Results',
                    'url': 'https://example.com/remote-work',
                    'content': 'Study shows 23% productivity increase with hybrid work models',
                    'published': '1 hour ago',
                    'score': 8.2,
                    'category': category
                },
                {
                    'title': 'SaaS Market Growth Predictions',
                    'url': 'https://example.com/saas-growth',
                    'content': 'Industry analysis predicts continued growth in SaaS sector',
                    'published': '3 hours ago',
                    'score': 7.5,
                    'category': category
                }
            ],
            'ai': [
                {
                    'title': 'ChatGPT Usage Reaches New Milestone',
                    'url': 'https://example.com/chatgpt-milestone',
                    'content': 'OpenAI reports significant increase in enterprise adoption',
                    'published': '30 minutes ago',
                    'score': 9.1,
                    'category': category
                }
            ],
            'startup': [
                {
                    'title': 'Startup Funding Trends 2024',
                    'url': 'https://example.com/startup-funding',
                    'content': 'Venture capital shifts focus to AI and sustainability startups',
                    'published': '2 hours ago',
                    'score': 8.0,
                    'category': category
                }
            ]
        }
        
        return mock_trends.get(category, [])
    
    def _fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis if AI fails"""
        return {
            "top_opportunities": [
                {
                    "trend_topic": f"AI implementation in {self.config.brand.expertise_areas[0]}",
                    "viral_potential": 8.5,
                    "alignment_score": 9.0,
                    "content_angle": "Practical implementation lessons from real-world experience",
                    "timing": "immediate",
                    "hashtags": ["#AI"] + self.config.brand.target_hashtags[:2],
                    "content_ideas": [
                        "Share specific AI implementation metrics",
                        "Common AI adoption mistakes to avoid"
                    ]
                }
            ],
            "trend_themes": [
                "AI adoption in enterprise",
                "Remote work optimization"
            ],
            "recommendations": [
                "Focus on practical AI implementation content",
                "Share specific metrics and case studies"
            ]
        }
    
    def get_trending_hashtags(self, limit: int = 20) -> List[str]:
        """Get currently trending hashtags"""
        
        # This would integrate with Twitter API or other hashtag tracking services
        # For now, return relevant professional hashtags
        
        trending_hashtags = [
            "#AI", "#MachineLearning", "#SaaS", "#Startup", "#TechTrends",
            "#Innovation", "#DigitalTransformation", "#ProductStrategy",
            "#Leadership", "#GrowthHacking", "#DataScience", "#CloudComputing",
            "#Cybersecurity", "#Blockchain", "#IoT", "#DevOps", "#Agile",
            "#RemoteWork", "#FutureOfWork", "#Entrepreneurship"
        ]
        
        # Filter by relevance to brand
        relevant_hashtags = []
        for hashtag in trending_hashtags:
            if any(expertise.lower() in hashtag.lower() for expertise in self.config.brand.expertise_areas):
                relevant_hashtags.append(hashtag)
        
        # Add brand's target hashtags
        relevant_hashtags.extend(self.config.brand.target_hashtags)
        
        # Remove duplicates and limit
        unique_hashtags = list(dict.fromkeys(relevant_hashtags))
        
        return unique_hashtags[:limit]
    
    def _parse_html_results(self, search_query: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse SearXNG HTML results using Beautiful Soup for comprehensive web scraping"""
        try:
            from bs4 import BeautifulSoup
            
            # Get HTML results from SearXNG
            response = requests.get(
                f"{self.searxng_url}/search",
                params={'q': search_query, 'categories': 'news'},
                headers=headers,
                timeout=self.config.searxng.timeout
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                trends = []
                
                # Extract search results using Beautiful Soup
                results = soup.find_all('article', class_='result')
                
                if not results:
                    # Fallback to different selectors if the main one doesn't work
                    results = soup.find_all('div', class_='result')
                    
                if not results:
                    # Try another common structure
                    results = soup.select('.result, .search-result, [class*="result"]')
                
                logger.info(f"Found {len(results)} search results to parse")
                
                for i, result in enumerate(results[:10]):  # Top 10 results
                    try:
                        # Extract title and URL
                        title_elem = result.find('h3') or result.find('a') or result.find('[class*="title"]')
                        if title_elem:
                            link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                            title = title_elem.get_text(strip=True)
                            url = link.get('href', '') if link else ''
                        else:
                            continue
                        
                        # Extract content/description
                        content_elem = (result.find('p', class_='content') or 
                                      result.find('div', class_='content') or
                                      result.find('p') or
                                      result.find('div', string=True))
                        content = content_elem.get_text(strip=True) if content_elem else title
                        
                        # Extract published date if available
                        date_elem = (result.find('time') or 
                                   result.find('[class*="date"]') or
                                   result.find('[class*="time"]'))
                        published = date_elem.get_text(strip=True) if date_elem else 'recent'
                        
                        # Create trend object
                        trend = {
                            'title': title,
                            'url': url,
                            'content': content[:500],  # Limit content length
                            'published': published,
                            'score': 8.0 - (i * 0.3),  # Decreasing score based on position
                            'category': 'news',
                            'source': 'searxng_html'
                        }
                        trends.append(trend)
                        
                        # Enhanced content research: scrape actual page content
                        if url and not url.startswith('javascript:'):
                            enhanced_trend = self._scrape_page_content(trend, headers)
                            if enhanced_trend:
                                trends[-1] = enhanced_trend
                        
                    except Exception as e:
                        logger.warning(f"Error parsing search result {i}: {e}")
                        continue
                
                logger.info(f"Successfully parsed {len(trends)} trends from SearXNG HTML")
                return trends
            else:
                logger.warning(f"SearXNG HTML request failed: {response.status_code}")
            
        except ImportError:
            logger.error("Beautiful Soup not installed. Install with: pip install beautifulsoup4")
        except Exception as e:
            logger.warning(f"Beautiful Soup HTML parsing failed: {e}")
        
        # Fallback to mock data if HTML parsing fails
        logger.info("Using fallback trends data")
        return self._get_mock_trends("general")
    
    def _scrape_page_content(self, trend: Dict[str, Any], headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Scrape actual page content for enhanced content research"""
        try:
            from bs4 import BeautifulSoup
            
            url = trend['url']
            if not url or url.startswith(('javascript:', 'mailto:', '#')):
                return None
            
            # Skip certain domains that are typically not useful
            skip_domains = ['youtube.com', 'youtu.be', 'twitter.com', 'facebook.com', 'instagram.com']
            if any(domain in url.lower() for domain in skip_domains):
                return trend
            
            logger.debug(f"Scraping content from: {url}")
            
            # Visit the actual page
            page_response = requests.get(
                url, 
                headers=headers,
                timeout=10,  # Shorter timeout for page visits
                allow_redirects=True
            )
            
            if page_response.status_code == 200:
                soup = BeautifulSoup(page_response.text, 'lxml')
                
                # Extract enhanced content
                enhanced_content = self._extract_article_content(soup)
                
                # Extract metadata
                meta_description = soup.find('meta', attrs={'name': 'description'})
                meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                
                # Update trend with enhanced data
                enhanced_trend = trend.copy()
                enhanced_trend.update({
                    'enhanced_content': enhanced_content[:1000] if enhanced_content else trend['content'],
                    'meta_description': meta_description.get('content', '') if meta_description else '',
                    'meta_keywords': meta_keywords.get('content', '') if meta_keywords else '',
                    'scraped': True,
                    'word_count': len(enhanced_content.split()) if enhanced_content else 0
                })
                
                # Boost score for successfully scraped content
                enhanced_trend['score'] += 1.0
                
                logger.debug(f"Enhanced content for: {trend['title']}")
                return enhanced_trend
            
        except Exception as e:
            logger.debug(f"Failed to scrape page content from {trend['url']}: {e}")
        
        return trend
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content from a webpage using Beautiful Soup"""
        try:
            # Try common article selectors
            content_selectors = [
                'article',
                '.article-content',
                '.post-content', 
                '.entry-content',
                '.content',
                'main',
                '.main-content',
                '[role="main"]'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove script and style elements
                    for script in content_elem(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    # Get text content
                    text = content_elem.get_text(separator=' ', strip=True)
                    if len(text) > 100:  # Only return if substantial content
                        return text
            
            # Fallback: extract all paragraphs
            paragraphs = soup.find_all('p')
            if paragraphs:
                content = ' '.join([p.get_text(strip=True) for p in paragraphs[:5]])
                return content
            
            # Last resort: get body text
            body = soup.find('body')
            if body:
                return body.get_text(separator=' ', strip=True)[:500]
        
        except Exception as e:
            logger.debug(f"Error extracting article content: {e}")
        
        return ""
