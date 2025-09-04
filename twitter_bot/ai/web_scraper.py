#!/usr/bin/env python3
"""
Web Scraper Service
Advanced web scraping and content research using SearXNG and Beautiful Soup
"""

import logging
import requests
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

try:
    from bs4 import BeautifulSoup
    from bs4.element import Comment
except ImportError:
    BeautifulSoup = None
    Comment = None

logger = logging.getLogger(__name__)

class WebScraper:
    """Advanced web scraper for content research and trend analysis"""
    
    def __init__(self, config):
        """Initialize web scraper"""
        self.config = config
        # Handle SearXNG configuration
        try:
            self.searxng_url = config.searxng.base_url
            self.timeout = config.searxng.timeout
        except AttributeError:
            self.searxng_url = 'http://localhost:8080'
            self.timeout = 30
            logger.info("Using default SearXNG configuration")
        
        # Enhanced concurrent processing settings
        self.max_workers = 12  # Increased concurrent scraping workers
        self.max_concurrent_searches = 8  # Increased concurrent search operations
        self.max_content_processors = 6  # Dedicated content processing workers
        
        # Rate limiting (per worker)
        self.last_request_times = {}  # Track per-worker timing
        self.min_delay = 0.5  # Reduced delay for concurrent processing
        self.request_lock = threading.Lock()
        
        # Enhanced user agent rotation for better access
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
            'TwitterContentBot/2.0 (Content Research; Real-time Trends)',
            'ContentAnalyzer/1.0 (Business Intelligence; +http://localhost:8080)'
        ]
        
        # Enhanced search targets for comprehensive content coverage
        self.priority_domains = {
            # Tech & AI News
            'ai_tech': [
                'techcrunch.com', 'theverge.com', 'arstechnica.com', 'wired.com',
                'venturebeat.com', 'techradar.com', 'engadget.com', 'aibreakfast.com',
                'artificialintelligence-news.com', 'syncedreview.com', 'lexfridman.com'
            ],
            # Business & Startup
            'business': [
                'reuters.com', 'bloomberg.com', 'cnbc.com', 'wsj.com',
                'businessinsider.com', 'fastcompany.com', 'inc.com', 'entrepreneur.com',
                'crunchbase.com', 'pitchbook.com'
            ],
            # Developer & Product
            'developer': [
                'hacker-news.ycombinator.com', 'dev.to', 'stackoverflow.blog',
                'github.blog', 'producthunt.com', 'indiehackers.com',
                'techstars.com', 'ycombinator.com'
            ],
            # Research & Innovation
            'research': [
                'arxiv.org', 'paperswithcode.com', 'distill.pub', 'research.google',
                'openai.com/blog', 'anthropic.com', 'deepmind.com',
                'ai.meta.com', 'microsoft.com/en-us/research'
            ],
            # Community & Content
            'community': [
                'medium.com', 'substack.com', 'hackernoon.com',
                'towards-data-science', 'analyticsvidhya.com', 'kdnuggets.com'
            ]
        }
        
        # Enhanced content categorization and viral indicators
        self.content_categories = {
            'ai_breakthrough': [
                'ai breakthrough', 'machine learning advancement', 'neural network',
                'large language model', 'gpt', 'claude', 'llm', 'generative ai',
                'artificial general intelligence', 'agi', 'computer vision', 'nlp'
            ],
            'startup_funding': [
                'raises', 'funding round', 'series a', 'series b', 'venture capital',
                'vc investment', 'seed funding', 'valuation', 'unicorn', 'ipo'
            ],
            'product_innovation': [
                'launches', 'releases', 'unveils', 'introduces', 'beta',
                'product update', 'new feature', 'platform', 'api', 'integration'
            ],
            'industry_trends': [
                'market shift', 'industry trend', 'adoption rate', 'growth',
                'digital transformation', 'automation', 'efficiency', 'scale'
            ],
            'tech_news': [
                'breaking', 'just announced', 'confirmed', 'exclusive',
                'leaked', 'rumor', 'speculation', 'acquisition', 'merger'
            ]
        }
        
        # Viral content indicators
        self.viral_indicators = [
            'breaking', 'just announced', 'launches', 'raises', 'acquired',
            'breakthrough', 'first ever', 'record', 'milestone', 'disrupting',
            'revolutionary', 'game-changing', 'exclusive', 'leaked', 'confirmed',
            'goes viral', 'trending', 'explodes', 'massive', 'unprecedented'
        ]
        
        # Visited URLs cache
        self.visited_urls: Set[str] = set()
        
        logger.info(f"🕷️ Enhanced Web Scraper initialized with Beautiful Soup ({self.max_workers} concurrent workers, {self.max_content_processors} content processors)")
    
    def search_and_scrape(self, 
                         query: str, 
                         categories: List[str] = None,
                         max_results: int = 10,
                         scrape_content: bool = True,
                         time_priority: bool = True,
                         viral_focus: bool = True) -> List[Dict[str, Any]]:
        """Enhanced comprehensive search and scrape operation with real-time focus"""
        
        if not categories:
            categories = ['news', 'tech', 'business']
        
        all_results = []
        
        # Enhanced query processing for better results
        enhanced_queries = self._generate_enhanced_queries(query, time_priority, viral_focus)
        
        # Prepare all search tasks for concurrent execution
        search_tasks = []
        for category in categories:
            for enhanced_query in enhanced_queries[:2]:  # Top 2 query variations
                search_tasks.append((enhanced_query, category))
        
        logger.info(f"🚀 Starting {len(search_tasks)} concurrent search operations")
        
        # Execute searches concurrently
        all_results = self._concurrent_search_and_scrape(search_tasks, scrape_content)
        
        # Advanced result processing
        processed_results = self._process_results_for_viral_potential(all_results)
        unique_results = self._deduplicate_results(processed_results)
        
        # Smart sorting by relevance, time, and viral potential
        sorted_results = self._smart_sort_results(unique_results)
        
        return sorted_results[:max_results]
    
    def _concurrent_search_and_scrape(self, search_tasks: List[tuple], scrape_content: bool) -> List[Dict[str, Any]]:
        """Execute multiple search and scrape operations concurrently"""
        
        all_results = []
        
        # Use ThreadPoolExecutor for concurrent searches
        with ThreadPoolExecutor(max_workers=self.max_concurrent_searches) as executor:
            # Submit all search tasks
            future_to_task = {
                executor.submit(self._execute_search_task, task, scrape_content): task 
                for task in search_tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    results = future.result(timeout=60)  # 60 second timeout per search
                    if results:
                        all_results.extend(results)
                        logger.info(f"✅ Completed search: {task[0][:50]}... ({len(results)} results)")
                except Exception as e:
                    logger.warning(f"❌ Search failed: {task[0][:50]}... - {e}")
        
        logger.info(f"🎯 Concurrent search completed: {len(all_results)} total results")
        return all_results
    
    def _execute_search_task(self, task: tuple, scrape_content: bool) -> List[Dict[str, Any]]:
        """Execute a single search task"""
        
        enhanced_query, category = task
        worker_id = threading.current_thread().ident
        
        try:
            # Apply per-worker rate limiting
            self._concurrent_rate_limit(worker_id)
            
            # Search using SearXNG with enhanced parameters
            search_results = self._searxng_search(enhanced_query, category)
            
            # Filter for high-quality results
            filtered_results = self._filter_high_quality_results(search_results)
            
            if scrape_content and filtered_results:
                # Enhance results with intelligent scraping (limited to top 3 for speed)
                enhanced_results = self._enhance_with_concurrent_scraping(filtered_results[:3])
                return enhanced_results
            else:
                return filtered_results
                
        except Exception as e:
            logger.warning(f"Error in search task {enhanced_query[:30]}... - {e}")
            return []
    
    def _concurrent_rate_limit(self, worker_id: int):
        """Apply rate limiting per worker"""
        
        with self.request_lock:
            current_time = time.time()
            last_time = self.last_request_times.get(worker_id, 0)
            
            elapsed = current_time - last_time
            if elapsed < self.min_delay:
                sleep_time = self.min_delay - elapsed
                time.sleep(sleep_time)
            
            self.last_request_times[worker_id] = time.time()
    
    def _enhance_with_concurrent_scraping(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced scraping with concurrent processing for top results"""
        
        if not search_results:
            return []
        
        enhanced_results = []
        
        # Use ThreadPoolExecutor for concurrent page scraping
        with ThreadPoolExecutor(max_workers=min(3, len(search_results))) as executor:
            # Submit scraping tasks for priority results only
            future_to_result = {}
            for result in search_results:
                if self._is_priority_scraping_target(result):
                    future = executor.submit(self._scrape_single_page_concurrent, result)
                    future_to_result[future] = result
                else:
                    enhanced_results.append(result)
            
            # Collect enhanced results
            for future in as_completed(future_to_result, timeout=30):
                original_result = future_to_result[future]
                try:
                    enhanced_result = future.result()
                    enhanced_results.append(enhanced_result)
                except Exception as e:
                    logger.debug(f"Concurrent scraping failed: {e}")
                    enhanced_results.append(original_result)
        
        return enhanced_results
    
    def discover_content_by_theme(self, theme: str, content_type: str = "general") -> List[Dict[str, Any]]:
        """Discover content by specific theme with enhanced targeting"""
        
        theme_queries = self._generate_theme_specific_queries(theme, content_type)
        all_results = []
        
        # Use enhanced concurrent processing for theme discovery
        with ThreadPoolExecutor(max_workers=self.max_concurrent_searches) as executor:
            future_to_query = {}
            
            for query in theme_queries:
                # Select appropriate categories based on theme
                categories = self._select_categories_for_theme(theme, content_type)
                future = executor.submit(
                    self.search_and_scrape, 
                    query, 
                    categories,
                    max_results=5,
                    time_priority=True,
                    viral_focus=True
                )
                future_to_query[future] = query
            
            # Collect results with timeout
            for future in as_completed(future_to_query, timeout=45):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.debug(f"Theme discovery failed for query: {e}")
        
        # Enhanced deduplication and ranking
        unique_results = self._deduplicate_and_rank_results(all_results)
        
        return unique_results[:10]  # Return top 10 results
    
    def discover_ai_breakthroughs(self) -> List[Dict[str, Any]]:
        """Specialized method for discovering AI breakthroughs and news"""
        
        ai_queries = [
            "AI breakthrough 2024",
            "large language model advancement",
            "generative AI innovation",
            "machine learning breakthrough",
            "artificial intelligence news today",
            "AI startup funding announcement",
            "neural network advancement",
            "AI research paper",
            "OpenAI Claude GPT news",
            "AI product launch"
        ]
        
        return self._parallel_content_discovery(ai_queries, ['ai_tech', 'research'], max_results=15)
    
    def discover_startup_innovations(self) -> List[Dict[str, Any]]:
        """Specialized method for discovering startup and product innovations"""
        
        startup_queries = [
            "startup funding round announcement",
            "SaaS product launch",
            "venture capital investment",
            "product innovation breakthrough",
            "startup acquisition news",
            "unicorn valuation announcement",
            "Y Combinator demo day",
            "Techstars startup showcase",
            "seed series A funding",
            "product hunt launch"
        ]
        
        return self._parallel_content_discovery(startup_queries, ['business', 'developer'], max_results=15)
    
    def discover_tech_trends(self) -> List[Dict[str, Any]]:
        """Specialized method for discovering technology trends"""
        
        tech_queries = [
            "technology trend 2024",
            "developer tools innovation",
            "API economy growth",
            "cloud computing advancement",
            "cybersecurity breakthrough",
            "blockchain innovation",
            "quantum computing progress",
            "edge computing trend",
            "software development trend",
            "tech industry shift"
        ]
        
        return self._parallel_content_discovery(tech_queries, ['ai_tech', 'developer'], max_results=15)
    
    def _parallel_content_discovery(self, queries: List[str], domain_categories: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """Enhanced parallel content discovery with domain targeting"""
        
        all_results = []
        
        with ThreadPoolExecutor(max_workers=min(len(queries), self.max_concurrent_searches)) as executor:
            future_to_query = {}
            
            for query in queries:
                future = executor.submit(self._targeted_search, query, domain_categories, max_results//len(queries))
                future_to_query[future] = query
            
            # Collect results with extended timeout for comprehensive searches
            for future in as_completed(future_to_query, timeout=60):
                try:
                    results = future.result()
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    logger.debug(f"Parallel discovery failed: {e}")
        
        # Enhanced filtering and ranking
        filtered_results = self._advanced_content_filtering(all_results)
        
        return filtered_results[:max_results]
    
    def _targeted_search(self, query: str, domain_categories: List[str], max_results: int) -> List[Dict[str, Any]]:
        """Perform targeted search within specific domain categories"""
        
        try:
            # Build domain-specific search
            target_domains = []
            for category in domain_categories:
                if category in self.priority_domains:
                    target_domains.extend(self.priority_domains[category])
            
            # Enhanced search with domain targeting
            if target_domains:
                domain_query = f"{query} site:({' OR site:'.join(target_domains[:5])})"
            else:
                domain_query = query
            
            # Perform search with enhanced parameters
            results = self.search_and_scrape(
                domain_query,
                categories=['news', 'tech'],
                max_results=max_results,
                scrape_content=True,
                time_priority=True,
                viral_focus=True
            )
            
            return results
            
        except Exception as e:
            logger.debug(f"Targeted search failed: {e}")
            return []
    
    def _generate_theme_specific_queries(self, theme: str, content_type: str) -> List[str]:
        """Generate theme-specific search queries"""
        
        base_queries = [theme]
        
        # Content type specific enhancements
        if content_type == "ai_breakthrough":
            enhancements = ["breakthrough", "advancement", "innovation", "research", "announcement"]
        elif content_type == "startup_funding":
            enhancements = ["raises", "funding", "investment", "valuation", "acquisition"]
        elif content_type == "product_launch":
            enhancements = ["launches", "releases", "unveils", "introduces", "beta"]
        else:
            enhancements = ["news", "update", "announcement", "trend", "development"]
        
        # Generate enhanced queries
        enhanced_queries = []
        for enhancement in enhancements:
            enhanced_queries.append(f"{theme} {enhancement}")
            enhanced_queries.append(f"{enhancement} {theme}")
        
        # Add time-sensitive variations
        current_year = datetime.now().year
        enhanced_queries.extend([
            f"{theme} {current_year}",
            f"{theme} latest news",
            f"{theme} breaking"
        ])
        
        return enhanced_queries[:8]  # Limit to prevent overload
    
    def _select_categories_for_theme(self, theme: str, content_type: str) -> List[str]:
        """Select appropriate search categories based on theme and content type"""
        
        theme_lower = theme.lower()
        
        if any(keyword in theme_lower for keyword in ['ai', 'ml', 'neural', 'llm', 'gpt']):
            return ['ai_tech', 'research']
        elif any(keyword in theme_lower for keyword in ['startup', 'funding', 'venture', 'investment']):
            return ['business', 'developer']
        elif any(keyword in theme_lower for keyword in ['product', 'launch', 'api', 'platform']):
            return ['developer', 'business']
        else:
            return ['ai_tech', 'business']
    
    def _deduplicate_and_rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced deduplication and ranking of results"""
        
        # Deduplicate by URL and similar titles
        unique_results = []
        seen_urls = set()
        seen_title_hashes = set()
        
        for result in results:
            url = result.get('url', '')
            title = result.get('title', '')
            
            # Simple title similarity check
            import hashlib
            title_hash = hashlib.md5(title.lower()[:50].encode()).hexdigest()
            
            if url not in seen_urls and title_hash not in seen_title_hashes:
                seen_urls.add(url)
                seen_title_hashes.add(title_hash)
                unique_results.append(result)
        
        # Rank by quality score (if available) or viral indicators
        unique_results.sort(key=lambda x: (
            x.get('quality_score', 0),
            len([v for v in self.viral_indicators if v in x.get('title', '').lower()]),
            len(x.get('content', ''))
        ), reverse=True)
        
        return unique_results
    
    def _advanced_content_filtering(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Advanced content filtering with enhanced quality metrics"""
        
        filtered = []
        
        for result in results:
            title = result.get('title', '').lower()
            content = result.get('content', '').lower()
            url = result.get('url', '')
            
            # Enhanced quality scoring
            quality_score = 0
            
            # Domain authority (enhanced)
            for category, domains in self.priority_domains.items():
                for domain in domains:
                    if domain in url:
                        category_scores = {
                            'research': 5, 'ai_tech': 4, 'business': 3, 
                            'developer': 3, 'community': 2
                        }
                        quality_score += category_scores.get(category, 1)
                        break
                if quality_score > 0:
                    break
            
            # Content relevance and depth
            if len(title) > 25 and len(content) > 80:
                quality_score += 2
            elif len(title) > 15 and len(content) > 40:
                quality_score += 1
            
            # Viral potential
            viral_count = sum(1 for indicator in self.viral_indicators if indicator in title or indicator in content)
            quality_score += min(viral_count, 3)
            
            # Time relevance
            time_indicators = ['today', 'this week', 'latest', 'breaking', 'just announced']
            time_matches = sum(1 for indicator in time_indicators if indicator in content)
            quality_score += min(time_matches, 2)
            
            # Apply higher threshold for advanced filtering
            if quality_score >= 4:
                result['quality_score'] = quality_score
                filtered.append(result)
        
        return sorted(filtered, key=lambda x: x.get('quality_score', 0), reverse=True)
    
    def _scrape_single_page_concurrent(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape a single page with concurrency-safe approach"""
        
        worker_id = threading.current_thread().ident
        
        try:
            # Apply worker-specific rate limiting
            self._concurrent_rate_limit(worker_id)
            
            # Scrape the page content
            enhanced = self._scrape_page_content(result)
            
            # Add real-time analysis
            enhanced = self._add_realtime_analysis(enhanced)
            
            return enhanced
            
        except Exception as e:
            logger.debug(f"Concurrent page scraping failed: {e}")
            return result
    
    def _generate_enhanced_queries(self, base_query: str, time_priority: bool, viral_focus: bool) -> List[str]:
        """Generate enhanced search queries for better real-time results"""
        
        queries = [base_query]
        
        if time_priority:
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_month = datetime.now().strftime('%B %Y')
            
            time_enhanced = [
                f"{base_query} {current_date}",
                f"{base_query} today latest",
                f"{base_query} {current_month}",
                f"{base_query} breaking news",
                f"{base_query} just announced"
            ]
            queries.extend(time_enhanced)
        
        if viral_focus:
            viral_enhanced = [
                f"{base_query} trending viral",
                f"{base_query} breakthrough innovation",
                f"{base_query} major announcement",
                f"{base_query} industry disruption"
            ]
            queries.extend(viral_enhanced)
        
        return queries[:5]  # Return top 5 variations
    
    def _filter_high_quality_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter results for high-quality, relevant content"""
        
        filtered = []
        
        for result in results:
            title = result.get('title', '').lower()
            url = result.get('url', '')
            content = result.get('content', '').lower()
            
            # Quality indicators
            quality_score = 0
            
            # Domain quality boost (updated for new structure)
            for category, domains in self.priority_domains.items():
                for domain in domains:
                    if domain in url:
                        quality_score += 2
                        break
                if quality_score > 0:
                    break
            
            # Viral indicator boost
            for indicator in self.viral_indicators:
                if indicator in title or indicator in content:
                    quality_score += 1
            
            # Length and substance check
            if len(title) > 20 and len(content) > 50:
                quality_score += 1
            
            # Technical relevance check
            tech_keywords = ['ai', 'ml', 'startup', 'saas', 'tech', 'innovation', 'product']
            tech_matches = sum(1 for keyword in tech_keywords if keyword in title or keyword in content)
            quality_score += min(tech_matches, 3)
            
            # Only keep results with decent quality
            if quality_score >= 2:
                result['quality_score'] = quality_score
                filtered.append(result)
        
        return filtered
    
    def _enhance_with_intelligent_scraping(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced scraping with intelligent content selection"""
        
        enhanced_results = []
        
        # Prioritize scraping by quality score
        sorted_results = sorted(search_results, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        for result in sorted_results[:8]:  # Limit to top 8 quality results
            try:
                # Check if URL is worth scraping
                if self._is_priority_scraping_target(result):
                    enhanced = self._scrape_page_content(result)
                    # Add real-time analysis
                    enhanced = self._add_realtime_analysis(enhanced)
                    enhanced_results.append(enhanced)
                else:
                    enhanced_results.append(result)
                
                # Adaptive rate limiting based on source
                self._adaptive_rate_limit(result.get('url', ''))
                
            except Exception as e:
                logger.debug(f"Error enhancing result: {e}")
                enhanced_results.append(result)
        
        return enhanced_results
    
    def _is_priority_scraping_target(self, result: Dict[str, Any]) -> bool:
        """Determine if URL deserves priority scraping"""
        
        url = result.get('url', '')
        title = result.get('title', '').lower()
        quality_score = result.get('quality_score', 0)
        
        # Priority conditions
        is_priority_domain = any(domain in url for domain in self.priority_domains)
        has_viral_indicators = any(indicator in title for indicator in self.viral_indicators)
        high_quality = quality_score >= 4
        
        return is_priority_domain or has_viral_indicators or high_quality
    
    def _add_realtime_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Add real-time analysis to scraped content"""
        
        if not result.get('scraped'):
            return result
        
        content = result.get('scraped_content', '') + ' ' + result.get('article_text', '')
        
        # Real-time signals
        signals = {
            'urgency_score': self._calculate_urgency_score(result),
            'viral_potential': self._calculate_viral_potential(result),
            'engagement_indicators': self._extract_engagement_indicators(content),
            'trending_topics': self._extract_trending_topics(content),
            'influence_markers': self._extract_influence_markers(result)
        }
        
        result['realtime_analysis'] = signals
        
        # Boost score based on real-time signals
        signal_boost = (signals['urgency_score'] + signals['viral_potential']) / 2
        result['score'] = result.get('score', 5.0) + signal_boost
        
        return result
    
    def _calculate_urgency_score(self, result: Dict[str, Any]) -> float:
        """Calculate content urgency score"""
        
        published = result.get('published', '').lower()
        title = result.get('title', '').lower()
        
        urgency = 0.0
        
        # Time-based urgency
        if any(term in published for term in ['hour', 'minute', 'just', 'breaking']):
            urgency += 3.0
        elif 'today' in published or 'day' in published:
            urgency += 2.0
        elif 'week' in published:
            urgency += 1.0
        
        # Content urgency indicators
        urgency_terms = ['breaking', 'urgent', 'immediate', 'just', 'now', 'latest', 'developing']
        urgency += sum(0.5 for term in urgency_terms if term in title)
        
        return min(urgency, 5.0)
    
    def _calculate_viral_potential(self, result: Dict[str, Any]) -> float:
        """Calculate viral potential score"""
        
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        url = result.get('url', '')
        
        viral_score = 0.0
        
        # Viral keywords
        viral_terms = ['viral', 'trending', 'explosive', 'massive', 'unprecedented', 'shocking']
        viral_score += sum(0.8 for term in viral_terms if term in title or term in content)
        
        # Numbers and metrics (viral amplifiers)
        import re
        numbers = re.findall(r'\d+[%$MKB]|\d+x|\d+\.\d+[%$MKB]', title + content)
        viral_score += min(len(numbers) * 0.3, 2.0)
        
        # Source credibility boost
        if any(domain in url for domain in self.priority_domains[:5]):  # Top 5 domains
            viral_score += 1.0
        
        return min(viral_score, 5.0)
    
    def _extract_engagement_indicators(self, content: str) -> List[str]:
        """Extract engagement indicators from content"""
        
        indicators = []
        content_lower = content.lower()
        
        engagement_patterns = [
            'comments', 'shares', 'likes', 'views', 'engagement',
            'discussion', 'debate', 'controversy', 'reaction'
        ]
        
        for pattern in engagement_patterns:
            if pattern in content_lower:
                indicators.append(pattern)
        
        return indicators[:5]
    
    def _extract_trending_topics(self, content: str) -> List[str]:
        """Extract trending topics from content"""
        
        # Simple keyword extraction for trending topics
        trending_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'gpt', 'llm',
            'startup', 'funding', 'venture capital', 'ipo', 'acquisition',
            'crypto', 'blockchain', 'bitcoin', 'ethereum', 'web3',
            'climate', 'sustainability', 'renewable', 'green tech',
            'remote work', 'hybrid', 'productivity', 'automation'
        ]
        
        found_topics = []
        content_lower = content.lower()
        
        for keyword in trending_keywords:
            if keyword in content_lower:
                found_topics.append(keyword)
        
        return found_topics[:8]
    
    def _extract_influence_markers(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract influence and authority markers"""
        
        url = result.get('url', '')
        title = result.get('title', '')
        
        markers = {
            'source_authority': 'unknown',
            'content_type': 'article',
            'industry_focus': []
        }
        
        # Determine source authority
        if any(domain in url for domain in ['techcrunch.com', 'bloomberg.com', 'wsj.com']):
            markers['source_authority'] = 'high'
        elif any(domain in url for domain in ['reuters.com', 'cnbc.com', 'theverge.com']):
            markers['source_authority'] = 'medium'
        else:
            markers['source_authority'] = 'low'
        
        # Determine content type
        if 'interview' in title.lower():
            markers['content_type'] = 'interview'
        elif 'analysis' in title.lower() or 'report' in title.lower():
            markers['content_type'] = 'analysis'
        elif 'announcement' in title.lower() or 'launches' in title.lower():
            markers['content_type'] = 'announcement'
        
        return markers
    
    def _adaptive_rate_limit(self, url: str):
        """Adaptive rate limiting based on target domain"""
        
        base_delay = self.min_delay
        
        # Adjust delay based on domain
        if any(domain in url for domain in ['bloomberg.com', 'wsj.com']):
            # Premium sites need more careful handling
            delay = base_delay * 2.0
        elif any(domain in url for domain in self.priority_domains):
            # Established tech sites
            delay = base_delay * 1.2
        else:
            # Standard delay
            delay = base_delay
        
        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request_time = time.time()
    
    def _process_results_for_viral_potential(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process results to enhance viral potential scoring"""
        
        for result in results:
            # Combine various scores into final viral potential
            base_score = result.get('score', 5.0)
            quality_score = result.get('quality_score', 0)
            realtime_analysis = result.get('realtime_analysis', {})
            
            # Calculate composite viral score
            urgency = realtime_analysis.get('urgency_score', 0)
            viral_potential = realtime_analysis.get('viral_potential', 0)
            
            composite_score = (base_score + quality_score + urgency + viral_potential) / 4
            result['final_viral_score'] = min(composite_score, 10.0)
            
            # Add metadata for ranking
            result['processed'] = True
            result['processing_timestamp'] = datetime.now().isoformat()
        
        return results
    
    def _smart_sort_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Smart sorting by multiple factors"""
        
        def sort_key(result):
            viral_score = result.get('final_viral_score', result.get('score', 0))
            quality_score = result.get('quality_score', 0)
            urgency = result.get('realtime_analysis', {}).get('urgency_score', 0)
            
            # Weighted combination
            return (viral_score * 0.4) + (quality_score * 0.3) + (urgency * 0.3)
        
        return sorted(results, key=sort_key, reverse=True)
    
    def _searxng_search(self, query: str, category: str = 'news') -> List[Dict[str, Any]]:
        """Search using SearXNG with fallback to HTML parsing"""
        
        headers = self._get_headers()
        
        try:
            # Try JSON API first
            response = requests.get(
                f"{self.searxng_url}/search",
                params={
                    'q': query,
                    'categories': category,
                    'time_range': 'week',
                    'format': 'json'
                },
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results = data.get('results', [])
                    
                    logger.info(f"✅ JSON API returned {len(results)} results")
                    
                    return [self._normalize_search_result(r, category) for r in results[:10]]
                    
                except (ValueError, KeyError) as e:
                    logger.info("JSON API response invalid, trying HTML parsing")
                    
            # Fallback to HTML parsing
            return self._parse_searxng_html(query, category, headers)
            
        except Exception as e:
            logger.warning(f"SearXNG search failed: {e}")
            return []
    
    def _parse_searxng_html(self, query: str, category: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse SearXNG HTML results using Beautiful Soup"""
        
        if not BeautifulSoup:
            logger.error("Beautiful Soup not available for HTML parsing")
            return []
        
        try:
            response = requests.get(
                f"{self.searxng_url}/search",
                params={'q': query, 'categories': category},
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"SearXNG HTML request failed: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            results = []
            
            # Multiple selectors for different SearXNG versions
            result_selectors = [
                'article.result',
                'div.result',
                '.result',
                '[class*="result"]'
            ]
            
            search_results = []
            for selector in result_selectors:
                search_results = soup.select(selector)
                if search_results:
                    break
            
            logger.info(f"🔍 Found {len(search_results)} HTML results for {category}")
            
            for i, result in enumerate(search_results[:10]):
                try:
                    parsed_result = self._parse_search_result_html(result, category, i)
                    if parsed_result:
                        results.append(parsed_result)
                except Exception as e:
                    logger.debug(f"Error parsing result {i}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"HTML parsing failed: {e}")
            return []
    
    def _parse_search_result_html(self, result_elem, category: str, position: int) -> Optional[Dict[str, Any]]:
        """Parse individual search result from HTML"""
        
        try:
            # Extract title and URL
            title_elem = (result_elem.find('h3') or 
                         result_elem.find('h2') or 
                         result_elem.find('a'))
            
            if not title_elem:
                return None
            
            # Get the link
            if title_elem.name == 'a':
                link = title_elem
                title = title_elem.get_text(strip=True)
            else:
                link = title_elem.find('a')
                title = title_elem.get_text(strip=True)
            
            url = link.get('href', '') if link else ''
            
            if not title or not url:
                return None
            
            # Extract content/description
            content_selectors = [
                '.content', '.description', '.snippet',
                'p', '.summary', '[class*="content"]'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = result_elem.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            # Extract date
            date_elem = (result_elem.find('time') or 
                        result_elem.select_one('[class*="date"]') or
                        result_elem.select_one('[class*="time"]'))
            published = date_elem.get_text(strip=True) if date_elem else 'recent'
            
            return {
                'title': title,
                'url': self._clean_url(url),
                'content': content or title,
                'published': published,
                'score': 8.0 - (position * 0.2),
                'category': category,
                'source': 'searxng_html',
                'position': position + 1
            }
            
        except Exception as e:
            logger.debug(f"Error parsing search result: {e}")
            return None
    
    def _enhance_with_scraping(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance search results with scraped page content"""
        
        enhanced_results = []
        
        for result in search_results[:5]:  # Limit scraping to top 5 results
            try:
                enhanced = self._scrape_page_content(result)
                enhanced_results.append(enhanced)
                
                # Rate limiting between page visits
                self._rate_limit()
                
            except Exception as e:
                logger.debug(f"Error enhancing result: {e}")
                enhanced_results.append(result)
        
        return enhanced_results
    
    def _scrape_page_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape full page content for a search result"""
        
        url = result['url']
        
        # Skip if already visited
        if url in self.visited_urls:
            logger.debug(f"Skipping already visited URL: {url}")
            return result
        
        # Skip problematic URLs
        if not self._should_scrape_url(url):
            return result
        
        try:
            logger.debug(f"🕷️ Scraping: {url}")
            
            headers = self._get_headers()
            response = requests.get(
                url,
                headers=headers,
                timeout=15,
                allow_redirects=True
            )
            
            self.visited_urls.add(url)
            
            if response.status_code != 200:
                logger.debug(f"Failed to fetch {url}: {response.status_code}")
                return result
            
            if not BeautifulSoup:
                return result
                
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract comprehensive content
            enhanced_result = result.copy()
            enhanced_result.update({
                'scraped_content': self._extract_main_content(soup),
                'meta_description': self._extract_meta_description(soup),
                'meta_keywords': self._extract_meta_keywords(soup),
                'article_text': self._extract_article_text(soup),
                'headings': self._extract_headings(soup),
                'links': self._extract_relevant_links(soup, url),
                'scraped': True,
                'scraped_at': datetime.utcnow().isoformat(),
                'word_count': 0  # Will be calculated
            })
            
            # Calculate word count
            all_text = f"{enhanced_result.get('scraped_content', '')} {enhanced_result.get('article_text', '')}"
            enhanced_result['word_count'] = len(all_text.split())
            
            # Boost score for successfully scraped content
            if enhanced_result['word_count'] > 100:
                enhanced_result['score'] += 1.5
                
            logger.debug(f"✅ Scraped {enhanced_result['word_count']} words from {url}")
            
            return enhanced_result
            
        except Exception as e:
            logger.debug(f"Error scraping {url}: {e}")
            return result
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from webpage"""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'advertisement']):
            element.decompose()
        
        # Try content selectors in order of preference
        content_selectors = [
            'article',
            'main',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content-body',
            '.story-body',
            '[role="main"]',
            '.content'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 200:  # Substantial content
                    return text[:2000]  # Limit length
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)[:1000]
        
        return ""
    
    def _extract_article_text(self, soup: BeautifulSoup) -> str:
        """Extract article text from paragraphs"""
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = ' '.join([p.get_text(strip=True) for p in paragraphs[:10]])
            return text[:1500]
        return ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '') if meta_desc else ''
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> str:
        """Extract meta keywords"""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        return meta_keywords.get('content', '') if meta_keywords else ''
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract all headings (h1-h6)"""
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text(strip=True)
                if text and len(text) < 200:
                    headings.append(text)
        return headings[:10]  # Limit to 10 headings
    
    def _extract_relevant_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract relevant internal links"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True)[:20]:  # Limit to 20 links
            href = link.get('href')
            text = link.get_text(strip=True)
            
            if href and text and len(text) < 100:
                full_url = urljoin(base_url, href)
                link_domain = urlparse(full_url).netloc
                
                # Only include same-domain links
                if link_domain == base_domain:
                    links.append({
                        'url': full_url,
                        'text': text
                    })
        
        return links[:5]  # Return top 5 relevant links
    
    def _should_scrape_url(self, url: str) -> bool:
        """Determine if URL should be scraped"""
        
        if not url or url.startswith(('javascript:', 'mailto:', '#', 'tel:')):
            return False
        
        # Skip social media and video platforms
        skip_domains = [
            'youtube.com', 'youtu.be', 'twitter.com', 'facebook.com', 
            'instagram.com', 'tiktok.com', 'linkedin.com', 'reddit.com',
            'pinterest.com', 'snapchat.com'
        ]
        
        for domain in skip_domains:
            if domain in url.lower():
                return False
        
        # Skip file downloads
        file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']
        if any(url.lower().endswith(ext) for ext in file_extensions):
            return False
        
        return True
    
    def _normalize_search_result(self, result: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Normalize search result format"""
        return {
            'title': result.get('title', ''),
            'url': self._clean_url(result.get('url', '')),
            'content': result.get('content', '')[:500],
            'published': result.get('publishedDate', 'recent'),
            'score': self._calculate_relevance_score(result),
            'category': category,
            'source': 'searxng_json'
        }
    
    def _calculate_relevance_score(self, result: Dict[str, Any]) -> float:
        """Calculate relevance score for search result"""
        score = 5.0  # Base score
        
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        
        # Boost for trending keywords
        trending_keywords = [
            'breakthrough', 'innovation', 'trend', 'viral', 'emerging',
            'disrupting', 'revolutionary', 'game-changing', 'new', 'latest'
        ]
        
        for keyword in trending_keywords:
            if keyword in title:
                score += 1.0
            elif keyword in content:
                score += 0.5
        
        # Boost for business/tech keywords
        business_keywords = [
            'startup', 'saas', 'ai', 'ml', 'tech', 'business',
            'strategy', 'growth', 'scale', 'product', 'market'
        ]
        
        for keyword in business_keywords:
            if keyword in title:
                score += 0.8
            elif keyword in content:
                score += 0.3
        
        return min(score, 10.0)  # Cap at 10
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results by URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URL"""
        if not url:
            return ''
        
        # Remove tracking parameters
        url = re.sub(r'[?&](utm_|fbclid|gclid|ref=)', '', url)
        
        return url.strip()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with rotating user agent"""
        import random
        
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()
    
    def get_trending_topics(self, domains: List[str] = None) -> List[Dict[str, Any]]:
        """Get comprehensive trending topics across domains"""
        
        if not domains:
            domains = ['AI trends', 'tech innovation', 'startup news', 'business strategy']
        
        all_trends = []
        
        for domain in domains:
            trends = self.search_and_scrape(
                query=f"{domain} {datetime.now().year}",
                categories=['news', 'tech'],
                max_results=5,
                scrape_content=True
            )
            all_trends.extend(trends)
        
        # Return top trending topics
        return sorted(all_trends, key=lambda x: x.get('score', 0), reverse=True)[:15]
