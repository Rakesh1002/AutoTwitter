#!/usr/bin/env python3
"""
AI Content Generator
Unified content generation using Gemini 2.5 Pro with viral optimization
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
from .unified_client import UnifiedAIClient

logger = logging.getLogger(__name__)

class ContentGenerator:
    """AI-powered content generator with viral optimization"""
    
    def __init__(self, config):
        """Initialize content generator"""
        self.config = config
        self.ai_client = UnifiedAIClient(config)
        self.brand = config.brand
        
        # Content strategy framework
        self.viral_strategies = [
            "trend_hijacking", "contrarian_wisdom", "behind_scenes",
            "framework_thinking", "future_prediction", "vulnerability_value",
            "data_storytelling", "pattern_recognition"
        ]
        
        self.content_pillars = {
            "educational": 0.4,    # 40% - Educational content
            "personal": 0.3,       # 30% - Personal journey  
            "insight": 0.2,        # 20% - Insight/Opinion
            "interactive": 0.1     # 10% - Interactive
        }
        
        logger.info("🎯 AI Content Generator initialized with viral optimization")
    
    def generate_viral_posts(self, 
                           content_pillar: Optional[str] = None,
                           trending_context: Optional[str] = None,
                           real_time_trends: Optional[Dict[str, Any]] = None,
                           target_personas: Optional[List[str]] = None,
                           count: int = 5,
                           thread_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate viral-optimized posts"""
        
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        time_str = current_time.strftime('%B %d, %Y at %I:%M %p IST')
        
        # Get enhanced market context
        market_context = self._get_current_market_context(current_time)
        
        # Build enhanced prompt with real-time data
        if thread_type:
            prompt = self._build_viral_thread_prompt(
                thread_type, trending_context, real_time_trends, 
                time_str, market_context
            )
        else:
            prompt = self._build_enhanced_viral_post_prompt(
                content_pillar, trending_context, real_time_trends, 
                target_personas, time_str, market_context, count
            )
        
        try:
            response = self.ai_client.generate_content(prompt)
            
            if "error" in response:
                logger.error(f"AI error: {response['error']}")
                return self._fallback_posts(content_pillar, count)
            
            posts = response.get('posts', [])
            
            # Validate and enrich posts
            validated_posts = []
            for post in posts:
                if self._validate_post(post):
                    post['generated_at'] = current_time.isoformat()
                    post['ai_model'] = response.get('model_name', self.config.ai.provider.value)
                    post['ai_provider'] = response.get('ai_provider', self.config.ai.provider.value)
                    post['brand_aligned'] = True
                    validated_posts.append(post)
            
            if not validated_posts:
                logger.warning("No valid posts generated, using fallback")
                return self._fallback_posts(content_pillar, count)
            
            logger.info(f"✅ Generated {len(validated_posts)} viral posts")
            return validated_posts
            
        except Exception as e:
            logger.error(f"Error generating posts: {e}")
            return self._fallback_posts(content_pillar, count)
    
    def generate_smart_replies(self, 
                              original_post: Dict[str, Any],
                              count: int = 3) -> List[Dict[str, Any]]:
        """Generate context-aware replies"""
        
        prompt = self._build_reply_prompt(original_post, count)
        
        try:
            response = self.ai_client.generate_content(prompt)
            
            if "error" in response:
                logger.error(f"AI error: {response['error']}")
                return self._fallback_replies(original_post, count)
            
            replies = response.get('replies', [])
            
            # Validate and enrich replies
            validated_replies = []
            for reply in replies:
                if self._validate_reply(reply):
                    reply['generated_at'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
                    reply['ai_model'] = response.get('model_name', self.config.ai.provider.value)
                    reply['ai_provider'] = response.get('ai_provider', self.config.ai.provider.value)
                    reply['original_post_author'] = original_post.get('author')
                    validated_replies.append(reply)
            
            if not validated_replies:
                logger.warning("No valid replies generated, using fallback")
                return self._fallback_replies(original_post, count)
            
            logger.info(f"✅ Generated {len(validated_replies)} smart replies")
            return validated_replies
            
        except Exception as e:
            logger.error(f"Error generating replies: {e}")
            return self._fallback_replies(original_post, count)
    
    def generate_research_driven_posts(self, count: int = 5, output_format: str = "structured") -> Dict[str, Any]:
        """Generate viral posts using research-driven approach with real-time trend analysis"""
        
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        time_str = current_time.strftime('%B %d, %Y at %I:%M %p IST')
        
        # Build the new research-driven prompt
        prompt = self._build_research_driven_prompt(time_str, count, output_format)
        
        try:
            # Use text output for structured format, JSON for compatibility
            if output_format == "structured":
                response = self.ai_client.generate_content(prompt, output_format="text")
            else:
                response = self.ai_client.generate_content(prompt)
            
            if "error" in response:
                logger.error(f"AI error: {response['error']}")
                return self._fallback_research_driven_posts(count, output_format)
            
            if output_format == "structured":
                # Parse structured text response
                result = {
                    'posts': self._parse_structured_response(response.get('content', '')),
                    'generated_at': current_time.isoformat(),
                    'ai_model': response.get('model_name', self.config.ai.provider.value),
                    'approach': 'research_driven'
                }
            else:
                # Handle JSON response
                result = response
                result['generated_at'] = current_time.isoformat()
                result['approach'] = 'research_driven'
            
            logger.info(f"✅ Generated {len(result.get('posts', []))} research-driven posts")
            return result
            
        except Exception as e:
            logger.error(f"Error generating research-driven posts: {e}")
            return self._fallback_research_driven_posts(count, output_format)

    def analyze_trending_topics(self) -> Dict[str, Any]:
        """Analyze current trends for content opportunities"""
        
        prompt = self._build_trend_analysis_prompt()
        
        try:
            response = self.ai_client.generate_content(prompt)
            
            if "error" in response:
                logger.error(f"AI error: {response['error']}")
                return self._fallback_trends()
            
            trends = response.get('trending_analysis', {})
            
            logger.info("✅ Analyzed trending topics")
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return self._fallback_trends()
    
    def _get_current_market_context(self, current_time: datetime) -> Dict[str, Any]:
        """Get enhanced market context for content generation"""
        
        hour = current_time.hour
        day_of_week = current_time.strftime('%A')
        month = current_time.strftime('%B')
        
        # Time-based context
        time_context = {
            'engagement_window': self._get_engagement_window(hour),
            'business_context': self._get_business_context(day_of_week),
            'seasonal_trends': self._get_seasonal_trends(month),
            'optimal_content_type': self._get_optimal_content_type(hour, day_of_week),
            'audience_mindset': self._get_audience_mindset(hour, day_of_week)
        }
        
        return time_context
    
    def _get_engagement_window(self, hour: int) -> str:
        """Determine current engagement window"""
        if 9 <= hour <= 11:
            return 'morning_peak_business'
        elif 14 <= hour <= 16:
            return 'afternoon_peak_professional'
        elif 19 <= hour <= 21:
            return 'evening_peak_personal'
        elif 21 <= hour <= 23:
            return 'late_evening_casual'
        else:
            return 'off_peak_international'
    
    def _get_business_context(self, day: str) -> str:
        """Get business day context"""
        if day == 'Monday':
            return 'week_start_motivation'
        elif day in ['Tuesday', 'Wednesday', 'Thursday']:
            return 'mid_week_productivity'
        elif day == 'Friday':
            return 'week_wrap_reflection'
        elif day == 'Saturday':
            return 'weekend_planning'
        else:  # Sunday
            return 'weekend_reflection'
    
    def _get_seasonal_trends(self, month: str) -> List[str]:
        """Get seasonal trending themes"""
        seasonal_themes = {
            'January': ['new_year_goals', 'fresh_starts', 'planning'],
            'February': ['execution', 'valentine_networking', 'q1_momentum'],
            'March': ['spring_cleaning', 'q1_results', 'growth'],
            'April': ['renewal', 'spring_energy', 'new_projects'],
            'May': ['productivity', 'growth_season', 'expansion'],
            'June': ['mid_year_review', 'summer_planning', 'scaling'],
            'July': ['summer_innovation', 'vacation_productivity', 'remote_focus'],
            'August': ['late_summer_push', 'back_to_school', 'preparation'],
            'September': ['fall_energy', 'new_beginnings', 'focus'],
            'October': ['harvest_season', 'q4_preparation', 'results'],
            'November': ['thanksgiving_gratitude', 'year_end_push', 'reflection'],
            'December': ['year_end_reflection', 'planning_ahead', 'celebration']
        }
        return seasonal_themes.get(month, ['general_business'])
    
    def _get_optimal_content_type(self, hour: int, day: str) -> str:
        """Determine optimal content type for current time"""
        if day in ['Saturday', 'Sunday']:
            return 'inspirational_personal'
        elif 9 <= hour <= 12:
            return 'educational_tactical'
        elif 13 <= hour <= 17:
            return 'strategic_insights'
        elif 18 <= hour <= 21:
            return 'motivational_personal'
        else:
            return 'thoughtful_reflection'
    
    def _get_audience_mindset(self, hour: int, day: str) -> str:
        """Understand audience mindset for current context"""
        if day in ['Saturday', 'Sunday']:
            if hour < 10:
                return 'relaxed_planning'
            elif hour < 18:
                return 'personal_time_learning'
            else:
                return 'social_engagement'
        else:  # Weekday
            if 9 <= hour <= 12:
                return 'focused_productive'
            elif 13 <= hour <= 17:
                return 'problem_solving'
            elif 18 <= hour <= 21:
                return 'reflective_networking'
            else:
                return 'personal_wind_down'
    
    def _build_enhanced_viral_post_prompt(self, content_pillar: Optional[str], 
                                        trending_context: Optional[str],
                                        real_time_trends: Optional[Dict[str, Any]],
                                        target_personas: Optional[List[str]],
                                        time_str: str, 
                                        market_context: Dict[str, Any],
                                        count: int) -> str:
        """Build viral-focused post generation prompt"""
        
        # Extract real-time trend data
        viral_opportunities = real_time_trends.get('viral_opportunities', []) if real_time_trends else []
        current_themes = real_time_trends.get('trend_themes', []) if real_time_trends else []
        
        return f"""
You are Rakesh Roushan (@BuildWithRakesh), emulating the viral content strategies of top AI/SaaS thought leaders. Your "Big Idea": {self.brand.big_idea}

**CURRENT INTELLIGENCE:**
- Time: {time_str}
- Trending Context: {trending_context or 'AI/SaaS industry developments'}
- Live Themes: {', '.join(current_themes) if current_themes else 'AI implementation, SaaS growth, startup scaling'}
- Content Focus: {self._get_content_focus(trending_context)}
- Viral Keywords: {', '.join(self.brand.viral_keywords[:6])}

**EMULATE THESE TOP PROFILES:**
- @sama style: Bold predictions, industry insights, contrarian takes
- @paulg style: Startup wisdom, counterintuitive insights, frameworks
- @naval style: Philosophy + business, tweetstorms, first principles
- @dharmesh style: SaaS metrics, growth hacks, data-driven insights
- @levelsio style: Building in public, transparent metrics, founder journey
- @AndrewYNg style: Educational frameworks, practical AI applications

**VIRAL CONTENT FRAMEWORKS - Choose ONE:**

1. **HOOK-LINE-SINKER Structure** 
   - Hook: Interrupt scroll with emotion/curiosity/bold claim
   - Line: Deliver concise, valuable insight or observation  
   - Sinker: Soft CTA encouraging engagement/sharing

2. **CONTRARIAN WISDOM** (@paulg/@naval style)
   - Challenge popular opinion with data/experience
   - "Everyone says X. Actually, Y. Here's why..."
   - End with framework or prediction

3. **BUILDING IN PUBLIC** (@levelsio/@agazdecki style)
   - Share specific metrics, failures, lessons
   - "I built X and learned Y (with real numbers)"
   - Transparent, vulnerable, actionable

4. **FRAMEWORK THINKING** (@AndrewYNg/@dharmesh style)
   - Present complex ideas in simple structures
   - "The 3-step framework I use for X..."
   - Practical, implementable, educational

5. **TREND PREDICTION** (@sama/@balajis style)
   - Identify patterns others miss
   - Bold predictions with reasoning
   - Industry insider perspective

**VIRAL HOOK PATTERNS (Use these openings):**
- "Most people think {trending_context or 'AI will replace developers'}, but here's what they're missing..."
- "I made a $50K mistake building my first SaaS. Here's what I learned..."
- "Everyone's talking about {trending_context or 'AI funding rounds'}. Here's the real story..."
- "Unpopular opinion: {trending_context or 'Most AI startups are doomed'}"
- "How I went from 0 to 100K ARR in 18 months..."
- "Plot twist: The biggest AI trend everyone's missing..."

**CONTENT STRATEGY:**
- Reference SPECIFIC companies, metrics, events from trending context
- Include personal experience/founder journey elements
- Use "building in public" transparency
- Challenge conventional wisdom
- Provide actionable frameworks
- End with engagement hooks

**TONE: {self.brand.tone}**

**MUST INCLUDE:**
- Specific numbers, company names, or recent events
- Personal founder experience or insight
- Contrarian or non-obvious perspective
- Clear value proposition for followers
- Strategic question or bold prediction to drive engagement

**CONTENT TYPE FOCUS:** {market_context.get('content_type', 'insight')}
{self._get_content_type_guidance(market_context.get('content_type', 'insight'))}

**AVOID:**
- Generic advice about "building features" 
- Clichéd startup wisdom
- Content that could apply to any industry
- Vague statements without specifics
- Repeating similar themes from recent posts

**Format:**
{{
  "posts": [
    {{
      "content": "Post content (under 280 characters)",
      "trending_inspiration": "What current trend/narrative inspired this",
      "viral_potential": "Brief explanation of why this could go viral",
      "viral_score": 7.8,
      "content_pillar": "educational/personal/insight/interactive",
      "character_count": 156
    }}
  ]
}}

**Additional Guidelines:**
- Maintain authenticity to your professional brand
- Avoid controversial topics that could damage professional reputation
- Focus on value-driven content that showcases expertise
- Consider timing and current events relevance

**LEVERAGE WEB SCRAPING DATA:**
Use specific details from trending context: company names, funding amounts, technologies, announcements, metrics.

**OUTPUT FORMAT:**
Generate {count} posts ranked by viral potential. Each must include:
- Hook from trending context (specific companies/events/numbers)
- Personal founder insight or contrarian perspective  
- Clear value proposition for AI/SaaS builders
- Engagement trigger (question, bold prediction, or framework teaser)

Generate exactly {count} different post options ranked by viral potential. Each should be authentic to your professional persona while maximizing engagement.
"""
    
    def _format_viral_opportunities(self, opportunities: List[Dict[str, Any]]) -> str:
        """Format viral opportunities for prompt"""
        if not opportunities:
            return "No specific viral opportunities detected - focus on evergreen viral content"
        
        formatted = []
        for i, opp in enumerate(opportunities[:3]):  # Top 3 opportunities
            formatted.append(f"{i+1}. {opp.get('title', '')[:80]}... (Viral Score: {opp.get('viral_score', 0):.1f})")
        
        return '\n'.join(formatted)
    
    def _build_viral_thread_prompt(self, thread_type: str, 
                                 trending_context: Optional[str],
                                 real_time_trends: Optional[Dict[str, Any]],
                                 time_str: str, 
                                 market_context: Dict[str, Any]) -> str:
        """Build prompt for viral thread generation"""
        
        current_themes = real_time_trends.get('trend_themes', []) if real_time_trends else []
        
        thread_strategies = {
            "listicle": {
                "structure": "Hook → List Items (3-7) → Key Takeaway + CTA",
                "example": "10 mistakes I made scaling my SaaS from $0 to $100K ARR:",
                "format": "Number each insight, include specific metrics/examples"
            },
            "problem_solution": {
                "structure": "Problem Setup → Failed Attempts → Discovery → Solution → Results + Framework",
                "example": "My SaaS conversion rate was 0.8%. Here's the 3-step framework that got it to 4.2%:",
                "format": "Include before/after metrics, specific steps, actionable framework"
            },
            "storytelling": {
                "structure": "Setting → Challenge → Turning Point → Resolution → Lesson + Application",
                "example": "How I lost my first co-founder and what it taught me about building resilient teams:",
                "format": "Personal vulnerability + universal business lesson"
            },
            "before_after_bridge": {
                "structure": "Before State → After State → The Bridge (How) → Framework/Steps",
                "example": "Before: 0 beta users, product nobody wanted. After: 1,000-person waitlist, investor interest. The bridge:",
                "format": "Dramatic contrast + specific process + replicable steps"
            },
            "contrarian": {
                "structure": "Popular Belief → Why It's Wrong → Evidence/Data → Better Approach → Implications",
                "example": "Everyone says 'fail fast.' They're wrong. Here's why 'learning fast' is better for founders:",
                "format": "Challenge conventional wisdom with data/experience"
            }
        }
        
        strategy = thread_strategies.get(thread_type, thread_strategies["problem_solution"])
        
        return f"""
You are Rakesh Roushan (@BuildWithRakesh), creating a viral thread using the {thread_type.upper()} framework. Your "Big Idea": {self.brand.big_idea}

**THREAD FRAMEWORK: {thread_type.upper()}**
Structure: {strategy['structure']}
Example Hook: "{strategy['example']}"
Format Requirements: {strategy['format']}

**CURRENT CONTEXT:**
- Time: {time_str}
- Trending Topic: {trending_context or 'AI/SaaS scaling challenges'}
- Live Themes: {', '.join(current_themes) if current_themes else 'startup growth, AI tools, SaaS metrics'}

**EMULATE THESE VIRAL THREAD STYLES:**
- @paulg: Counterintuitive startup wisdom with frameworks
- @naval: Philosophy + business principles in tweetstorms  
- @levelsio: Building in public with real metrics/transparency
- @dharmesh: SaaS growth hacks with specific data points
- @sama: Bold industry predictions with insider insights

**THREAD REQUIREMENTS:**
1. **HOOK TWEET** (First tweet):
   - Must stop the scroll with curiosity/controversy/bold claim
   - Include specific metric, company name, or trending topic
   - End with "🧵" or "(thread)" or "Here's how:"

2. **BODY TWEETS** (2-6 tweets):
   - One key insight per tweet
   - Include personal experience/founder journey elements
   - Use specific examples, numbers, companies
   - Reference trending context throughout

3. **CONCLUSION TWEET** (Final tweet):
   - Summarize key takeaway
   - Include clear CTA: "Retweet the first tweet if this was valuable"
   - Tag relevant profiles or ask engagement question

**VIRAL ELEMENTS TO INCLUDE:**
- Personal founder mistakes/wins with real numbers
- Contrarian takes on popular AI/SaaS beliefs  
- Specific company examples from trending context
- Actionable frameworks (3-step, 5-rule format)
- Behind-the-scenes insights from building process
- Transparent metrics (revenue, growth, failures)

**CONTENT STRATEGY:**
- Reference SPECIFIC events/companies from trending context
- Include vulnerable founder moments + lessons learned
- Provide immediately actionable advice
- Challenge conventional startup/AI wisdom
- Use "building in public" transparency

**OUTPUT FORMAT:**
{{
  "thread": {{
    "hook_tweet": "First tweet content (with 🧵)",
    "body_tweets": [
      "Tweet 2 content",
      "Tweet 3 content", 
      "Tweet 4 content"
    ],
    "conclusion_tweet": "Final tweet with CTA",
    "thread_summary": "One-sentence description of thread value",
    "viral_potential": 9.2,
    "target_audience": "AI/SaaS founders and builders",
    "engagement_triggers": ["curiosity", "controversy", "actionable_value"],
    "total_tweets": 6
  }}
}}

Generate a {thread_type} thread that would get massive engagement from the AI/SaaS founder community.
"""
    
    def generate_viral_thread(self, thread_type: str = "problem_solution", 
                            trending_context: Optional[str] = None) -> Dict[str, Any]:
        """Generate a viral thread using specific frameworks"""
        
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        time_str = current_time.strftime('%B %d, %Y at %I:%M %p IST')
        market_context = self._get_current_market_context(current_time)
        
        prompt = self._build_viral_thread_prompt(
            thread_type, trending_context, None, time_str, market_context
        )
        
        try:
            response = self.ai_client.generate_content(prompt)
            
            if "error" in response:
                logger.error(f"AI error: {response['error']}")
                return self._fallback_thread(thread_type)
            
            thread_data = response.get('thread', {})
            
            if thread_data and self._validate_thread(thread_data):
                thread_data['generated_at'] = current_time.isoformat()
                thread_data['ai_model'] = response.get('model_name', self.config.ai.provider.value)
                thread_data['thread_type'] = thread_type
                logger.info(f"✅ Generated {thread_type} thread with {thread_data.get('total_tweets', 0)} tweets")
                return thread_data
            else:
                logger.warning("Invalid thread generated, using fallback")
                return self._fallback_thread(thread_type)
                
        except Exception as e:
            logger.error(f"Error generating thread: {e}")
            return self._fallback_thread(thread_type)
    
    def _build_viral_post_prompt(self, content_pillar: Optional[str], 
                               trending_context: Optional[str], 
                               time_str: str, count: int) -> str:
        """Build optimized prompt for viral posts"""
        
        return f"""
You are {self.brand.persona}, a seasoned technology professional and entrepreneur with expertise in {', '.join(self.brand.expertise_areas[:3])}.

CONTEXT & EXPERTISE:
- Professional tone: {self.brand.tone}
- Core expertise: {', '.join(self.brand.expertise_areas)}
- Target hashtags: {', '.join(self.brand.target_hashtags)}

TASK: Create {count} viral-worthy original X (Twitter) posts that leverage current trends while showcasing your expertise.

ENHANCED VIRAL STRATEGIES:
1. **Trend Hijacking**: Connect current events/viral topics to your professional expertise
2. **Contrarian Wisdom**: Challenge popular opinions with data-backed alternatives  
3. **Behind-the-Scenes**: Share authentic founder/leader experiences and lessons
4. **Framework Thinking**: Present complex ideas in simple, actionable frameworks
5. **Future Prediction**: Make bold but educated predictions about industry trends
6. **Vulnerability + Value**: Share failures/mistakes with actionable takeaways
7. **Data Storytelling**: Use specific metrics to tell compelling business stories
8. **Pattern Recognition**: Identify and share non-obvious patterns in business/tech

CONTENT GUIDELINES:
- Stay within 280 characters for each post
- Include strategic hashtags (max 2-3 per post)
- Maintain professional credibility while being engaging
- Add unique professional angle to trending topics
- Focus on value that showcases your expertise areas
- Use proven viral triggers: curiosity gaps, controversy, relatability, surprise
- Include numbers/metrics when possible for credibility

CURRENT CONTEXT:
- Date/Time: {time_str}
- Content Pillar Focus: {content_pillar or 'Mixed - choose best viral opportunity'}
- Trending Context: {trending_context or 'Analyze current tech/business trends'}

VIRAL TRIGGERS TO USE:
- Curiosity gaps ("Most people miss this...")
- Pattern interrupts ("Actually, the opposite is true...")
- Social proof ("In my experience with 50+ startups...")
- Specificity ("Increased conversion by 340% by...")
- Contrarian insights ("Everyone focuses on X, but Y is what matters")
- Vulnerability ("I learned this the hard way when...")

OUTPUT FORMAT (JSON):
{{
  "posts": [
    {{
      "content": "The actual tweet content (under 280 chars)",
      "trending_inspiration": "What current trend/narrative inspired this post",
      "viral_potential": "Why this could go viral (engagement triggers used)",
      "content_pillar": "educational/personal/insight/interactive",
      "viral_score": 8.5,
      "hashtags": ["{self.brand.target_hashtags[0]}", "{self.brand.target_hashtags[1] if len(self.brand.target_hashtags) > 1 else '#Business'}"],
      "engagement_strategy": "How to maximize engagement with this post",
      "character_count": 156
    }}
  ]
}}

Generate {count} posts ranked by viral potential (highest first). Each must be authentic to {self.brand.persona}'s professional brand while maximizing viral engagement potential.
"""

    def _build_reply_prompt(self, original_post: Dict[str, Any], count: int) -> str:
        """Build viral-focused prompt for smart replies"""
        
        return f"""
You are Rakesh Roushan, a professional with expertise showcased on your website (https://rakeshroushan.com) and LinkedIn profile (linkedin.com/in/rakeshroushan1002). Your task is to create a viral-worthy reply to a specific X (Twitter) post.

**Instructions:**
1. First, analyze the provided post content: {original_post.get('tweet_link', original_post.get('url', 'https://x.com'))}
2. Review your professional background from the provided links to understand your expertise, tone, and perspective
3. Craft a reply that:
   - Stays true to your professional voice and expertise
   - Adds genuine value to the conversation
   - Uses engaging elements like relevant questions, insights, or contrarian viewpoints
   - Incorporates viral content strategies (humor, relatability, controversy, or surprising insights when appropriate)
   - Keeps within X's character limit (280 characters)
   - Includes relevant hashtags or mentions if beneficial

**ORIGINAL POST TO REPLY TO:**
Author: {original_post.get('author', 'Unknown')} ({original_post.get('handle', '@unknown')})
Post URL: {original_post.get('tweet_link', original_post.get('url', 'https://x.com'))}
Content: "{original_post.get('content', '')}"
Posted: {original_post.get('timestamp', original_post.get('timing', 'today'))}

**Your Professional Background:**
- Expertise: {self.brand.persona}
- Core areas: {', '.join(self.brand.expertise_areas)}
- Website: https://rakeshroushan.com
- LinkedIn: linkedin.com/in/rakeshroushan1002
- Voice: {self.brand.tone}

**Output Requirements:**
- Provide 3 different reply options ranked by viral potential
- Each reply should be authentic to your professional persona
- Include a brief explanation (1-2 sentences) for why each reply could go viral
- Ensure replies are appropriate for your professional brand

**Format:**
{{
  "replies": [
    {{
      "content": "Reply Option 1 content (under 280 chars)",
      "why_it_works": "Brief explanation of viral potential",
      "viral_score": 8.5,
      "character_count": 156
    }},
    {{
      "content": "Reply Option 2 content (under 280 chars)", 
      "why_it_works": "Brief explanation of viral potential",
      "viral_score": 8.2,
      "character_count": 143
    }},
    {{
      "content": "Reply Option 3 content (under 280 chars)",
      "why_it_works": "Brief explanation of viral potential", 
      "viral_score": 7.8,
      "character_count": 167
    }}
  ]
}}

Generate exactly {count} reply options ranked by viral potential.
"""

    def _build_trend_analysis_prompt(self) -> str:
        """Build prompt for trend analysis"""
        
        return f"""
You are a trend analysis expert helping {self.brand.persona} identify viral content opportunities.

TASK: Analyze current trending topics in tech, business, and startup space that {self.brand.persona} could leverage for viral content.

FOCUS AREAS:
- {', '.join(self.brand.expertise_areas)}
- Current viral topics in technology and business
- Emerging trends relevant to professional audience

ANALYSIS CRITERIA:
1. **Viral Potential**: How likely to generate high engagement
2. **Relevance**: Connection to {self.brand.persona}'s expertise areas
3. **Timing**: Current trending momentum
4. **Uniqueness**: Opportunity for unique perspective
5. **Professional Value**: Enhances thought leadership

OUTPUT FORMAT (JSON):
{{
  "trending_analysis": {{
    "top_opportunities": [
      {{
        "topic": "Specific trending topic",
        "viral_potential": 9.2,
        "relevance_to_expertise": "How it connects to {self.brand.persona}'s background",
        "unique_angle": "{self.brand.persona}'s potential unique perspective",
        "content_suggestions": ["Specific post idea 1", "Specific post idea 2"],
        "hashtags": ["{self.brand.target_hashtags[0]}", "{self.brand.target_hashtags[1] if len(self.brand.target_hashtags) > 1 else '#Tech'}"],
        "timing_urgency": "high/medium/low"
      }}
    ],
    "content_themes": [
      "Theme 1: Current hot topic in relevant field",
      "Theme 2: Emerging trend with growth potential", 
      "Theme 3: Professional insight opportunity"
    ],
    "viral_frameworks_to_use": [
      "Framework 1: Problem-solution for current pain point",
      "Framework 2: Contrarian take on popular opinion",
      "Framework 3: Behind-scenes professional insight"
    ]
  }}
}}

Identify 5 top trending opportunities ranked by viral potential for {self.brand.persona}'s expertise.
"""

    def _validate_post(self, post: Dict[str, Any]) -> bool:
        """Validate generated post and convert to thread if needed"""
        if not post.get('content'):
            return False
        
        content = post['content']
        
        # Character limit check - convert to thread if needed
        if len(content) > 280:
            logger.info(f"Post exceeds 280 characters ({len(content)}), converting to thread")
            thread_parts = self._create_twitter_thread(content)
            if thread_parts:
                post['content'] = thread_parts[0]  # First tweet
                post['thread_parts'] = thread_parts  # All parts
                post['is_thread'] = True
                post['thread_count'] = len(thread_parts)
                logger.info(f"✅ Created {len(thread_parts)}-part Twitter thread")
            else:
                logger.warning("Failed to create thread, using fallback")
                return False
        else:
            post['is_thread'] = False
            post['thread_count'] = 1
        
        # Basic quality checks
        main_content = post['content']
        if len(main_content) < 20:
            logger.warning("Post too short")
            return False
        
        # Professional content check
        inappropriate_terms = ['damn', 'hell', 'stupid', 'idiot']
        if any(term in main_content.lower() for term in inappropriate_terms):
            logger.warning("Post contains inappropriate language")
            return False
        
        return True
    
    def _create_twitter_thread(self, long_content: str) -> List[str]:
        """Convert long content into Twitter thread parts"""
        try:
            # Clean up the content
            content = long_content.strip()
            
            # Split by sentences first
            import re
            sentences = re.split(r'(?<=[.!?])\s+', content)
            
            thread_parts = []
            current_part = ""
            part_number = 1
            
            for sentence in sentences:
                # Check if adding this sentence would exceed limit
                # Reserve space for thread numbering (e.g., "1/3 ")
                thread_prefix = f"{part_number}/X " if part_number > 1 else ""
                potential_content = current_part + (" " if current_part else "") + sentence
                full_content = thread_prefix + potential_content
                
                if len(full_content) <= 270:  # Leave some buffer
                    current_part = potential_content
                else:
                    # Finalize current part
                    if current_part:
                        if part_number == 1:
                            thread_parts.append(current_part + " 🧵")  # Add thread emoji to first
                        else:
                            final_prefix = f"{part_number}/{len(sentences) + 1} "  # Estimate
                            thread_parts.append(final_prefix + current_part)
                        part_number += 1
                    
                    # Start new part with current sentence
                    current_part = sentence
            
            # Add the last part
            if current_part:
                if part_number == 1:
                    # Single tweet after all
                    thread_parts.append(current_part)
                else:
                    final_prefix = f"{part_number}/{part_number} "
                    thread_parts.append(final_prefix + current_part)
            
            # Update numbering with correct total
            if len(thread_parts) > 1:
                total_parts = len(thread_parts)
                for i in range(1, len(thread_parts)):
                    old_content = thread_parts[i]
                    # Remove old numbering and add correct numbering
                    content_without_prefix = re.sub(r'^\d+/\d+\s+', '', old_content)
                    thread_parts[i] = f"{i+1}/{total_parts} {content_without_prefix}"
            
            # Validate each part
            valid_parts = []
            for part in thread_parts:
                if len(part) <= 280 and len(part) > 0:
                    valid_parts.append(part)
                else:
                    logger.warning(f"Thread part still too long: {len(part)} chars")
            
            return valid_parts if len(valid_parts) > 0 else None
            
        except Exception as e:
            logger.error(f"Error creating Twitter thread: {e}")
            return None
    
    def _validate_reply(self, reply: Dict[str, Any]) -> bool:
        """Validate generated reply"""
        if not reply.get('content'):
            return False
        
        content = reply['content']
        
        # Character limit check
        if len(content) > 280:
            logger.warning(f"Reply exceeds 280 characters: {len(content)}")
            return False
        
        # Basic quality checks
        if len(content) < 10:
            logger.warning("Reply too short")
            return False
        
        return True
    
    def _fallback_posts(self, content_pillar: Optional[str], count: int) -> List[Dict[str, Any]]:
        """Fallback posts if AI generation fails"""
        fallback_posts = [
            {
                "content": f"The biggest mistake in {self.brand.expertise_areas[0]}: building solutions for what people ask for vs. what they actually need. Data always wins over opinions. {self.brand.target_hashtags[0]}",
                "viral_potential": "Contrarian insight that challenges common assumptions",
                "content_pillar": content_pillar or "insight",
                "viral_score": 8.0,
                "hashtags": self.brand.target_hashtags[:2],
                "ai_model": "fallback",
                "character_count": 0
            },
            {
                "content": f"Most people optimize for the wrong metrics. Here's the framework I use to identify what actually moves the needle in {self.brand.expertise_areas[1] if len(self.brand.expertise_areas) > 1 else 'business'}... {self.brand.target_hashtags[0]}",
                "viral_potential": "Framework thinking with curiosity gap",
                "content_pillar": content_pillar or "educational",
                "viral_score": 7.8,
                "hashtags": self.brand.target_hashtags[:2],
                "ai_model": "fallback",
                "character_count": 0
            }
        ]
        
        # Calculate character counts
        for post in fallback_posts:
            post['character_count'] = len(post['content'])
        
        return fallback_posts[:count]
    
    def _fallback_replies(self, original_post: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Fallback replies if AI generation fails"""
        fallback_replies = [
            {
                "content": f"This resonates with my {self.brand.expertise_areas[0]} experience. What specific metrics helped you identify this pattern?",
                "viral_strategy": "Ask provocative follow-up question with professional context",
                "why_it_works": "Shows expertise while encouraging further discussion",
                "viral_score": 7.5,
                "ai_model": "fallback",
                "character_count": 0
            },
            {
                "content": f"Interesting perspective! In my experience with {self.brand.expertise_areas[0]}, the opposite often holds true. Have you tested this assumption?",
                "viral_strategy": "Gentle disagreement with alternative viewpoint",
                "why_it_works": "Respectful challenge that adds new dimension",
                "viral_score": 7.3,
                "ai_model": "fallback",
                "character_count": 0
            }
        ]
        
        # Calculate character counts
        for reply in fallback_replies:
            reply['character_count'] = len(reply['content'])
        
        return fallback_replies[:count]
    
    def _validate_thread(self, thread_data: Dict[str, Any]) -> bool:
        """Validate generated thread structure"""
        required_fields = ['hook_tweet', 'body_tweets', 'conclusion_tweet']
        
        if not all(field in thread_data for field in required_fields):
            return False
        
        # Validate tweet content
        if not thread_data['hook_tweet'] or len(thread_data['hook_tweet']) > 280:
            return False
        
        if not thread_data['body_tweets'] or not isinstance(thread_data['body_tweets'], list):
            return False
        
        for tweet in thread_data['body_tweets']:
            if not tweet or len(tweet) > 280:
                return False
        
        if not thread_data['conclusion_tweet'] or len(thread_data['conclusion_tweet']) > 280:
            return False
        
        return True
    
    def _fallback_thread(self, thread_type: str) -> Dict[str, Any]:
        """Fallback thread if AI generation fails"""
        return {
            "hook_tweet": f"Building my first SaaS taught me {len(self.brand.expertise_areas)} lessons the hard way. Here's what I wish I knew before starting: 🧵",
            "body_tweets": [
                f"1/ The biggest mistake: Optimizing for features instead of {self.brand.expertise_areas[0]}. Took me 6 months to realize users wanted simplicity, not complexity.",
                f"2/ Growth hack that actually worked: Instead of traditional marketing, I focused on {self.brand.expertise_areas[1]}. Result: 3x better conversion rates.",
                f"3/ The hardest lesson: {self.brand.expertise_areas[2]} requires patience. I wanted overnight success but real growth takes consistent execution."
            ],
            "conclusion_tweet": "Building in public taught me more than any course. Retweet the first tweet if you're also learning by doing. What's your biggest startup lesson?",
            "thread_summary": f"Founder lessons learned building SaaS focusing on {self.brand.expertise_areas[0]}",
            "viral_potential": 7.5,
            "target_audience": "AI/SaaS founders and builders", 
            "engagement_triggers": ["vulnerability", "actionable_lessons", "building_in_public"],
            "total_tweets": 5,
            "thread_type": thread_type,
            "ai_model": "fallback"
        }
    
    def _fallback_trends(self) -> Dict[str, Any]:
        """Fallback trend analysis if AI generation fails"""
        return {
            "top_opportunities": [
                {
                    "topic": f"AI implementation in {self.brand.expertise_areas[0]}",
                    "viral_potential": 8.5,
                    "relevance_to_expertise": f"Direct connection to {self.brand.expertise_areas[0]} and AI experience",
                    "unique_angle": "Practical implementation over hype",
                    "content_suggestions": [
                        "Share specific AI ROI metrics", 
                        "Common AI implementation mistakes"
                    ],
                    "hashtags": ["#AI"] + self.brand.target_hashtags[:1],
                    "timing_urgency": "high"
                }
            ],
            "content_themes": [
                f"Theme 1: Current developments in {self.brand.expertise_areas[0]}",
                f"Theme 2: Emerging trends in {self.brand.expertise_areas[1] if len(self.brand.expertise_areas) > 1 else 'technology'}",
                "Theme 3: Professional insight sharing"
            ],
            "viral_frameworks_to_use": [
                "Problem-solution for current industry pain points",
                "Contrarian take on popular business opinions",
                "Behind-scenes professional experiences"
            ]
        }

    def _get_content_focus(self, trending_context: Optional[str]) -> str:
        """Determine content focus based on trending context"""
        if not trending_context:
            return "General AI/SaaS insights"
        
        context_lower = trending_context.lower()
        if any(word in context_lower for word in ['funding', 'valuation', 'investment', 'vc']):
            return "Startup funding & investment news"
        elif any(word in context_lower for word in ['launch', 'product', 'release', 'announcement']):
            return "Product launches & announcements"
        elif any(word in context_lower for word in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
            return "AI/ML breakthrough news"
        elif any(word in context_lower for word in ['acquisition', 'merger', 'bought', 'sold']):
            return "Industry M&A activity"
        else:
            return "Industry trends & insights"
    
    def _classify_content_type(self, trending_context: Optional[str]) -> str:
        """Classify content type for better variety"""
        if not trending_context:
            return "observation"
        
        context_lower = trending_context.lower()
        if any(word in context_lower for word in ['breaking', 'announced', 'launches', 'funding', 'raised']):
            return "news_reaction"
        elif any(word in context_lower for word in ['lesson', 'learned', 'mistake', 'experience']):
            return "personal_story"
        elif any(word in context_lower for word in ['framework', 'strategy', 'approach', 'method']):
            return "educational"
        elif any(word in context_lower for word in ['prediction', 'future', 'will be', 'next']):
            return "prediction"
        else:
            return "insight"
    
    def _get_content_type_guidance(self, content_type: str) -> str:
        """Get specific guidance for content type"""
        guidance = {
            "news_reaction": "React to breaking news with expert analysis and contrarian insights. Include specific implications for founders/builders.",
            "personal_story": "Share authentic founder experiences with specific metrics, failures, or breakthroughs. Make it relatable and actionable.",
            "educational": "Provide tactical frameworks that readers can implement. Include step-by-step approaches with real examples.",
            "prediction": "Make bold, specific predictions about industry trends. Back with reasoning and personal observations.",
            "insight": "Share non-obvious observations about the industry. Challenge conventional thinking with data or experience.",
            "observation": "Comment on patterns you're noticing in the startup/AI ecosystem. Be specific and forward-thinking."
        }
        return guidance.get(content_type, "Share valuable insights relevant to your expertise and audience.")
    
    def _build_research_driven_prompt(self, time_str: str, count: int, output_format: str) -> str:
        """Build the research-driven prompt based on your new system prompt"""
        
        format_instruction = ""
        if output_format == "structured":
            format_instruction = f"""
**Format:**
Post Option 1: [tweet content]
Trending inspiration: [what current trend/narrative inspired this]
Viral potential: [brief explanation of why this could go viral]

Post Option 2: [tweet content]
Trending inspiration: [what current trend/narrative inspired this]
Viral potential: [brief explanation of why this could go viral]

[Continue for all {count} options]"""
        else:
            format_instruction = """
**Output Format (JSON):**
{
  "posts": [
    {
      "content": "Tweet content (under 280 chars)",
      "trending_inspiration": "What current trend/narrative inspired this",
      "viral_potential": "Brief explanation of why this could go viral",
      "viral_score": 8.5,
      "character_count": 156
    }
  ]
}"""
        
        return f"""
You are Rakesh Roushan, a professional with expertise showcased on your website (https://rakeshroushan.com) and LinkedIn profile (linkedin.com/in/rakeshroushan1002). Your task is to create viral-worthy original X (Twitter) posts by analyzing current trending topics and viral narratives.

**Current Context:**
- Time: {time_str}
- Your Expertise: {', '.join(self.brand.expertise_areas[:4])}
- Your Tone: {self.brand.tone}
- Your Big Idea: {self.brand.big_idea}

**Instructions:**
1. Research and analyze today's top trending X posts, viral narratives, and popular themes across relevant categories (tech, business, personal development, industry insights, etc.)
2. Review your professional background from the provided links to understand your expertise areas, tone, and unique perspective
3. Create original posts that:
   - Leverage current viral trends and narratives while adding your unique professional angle
   - Align with your expertise and professional brand
   - Incorporate proven viral content strategies (storytelling, contrarian takes, actionable insights, relatable experiences, thought-provoking questions)
   - Stay within X's 280-character limit
   - Include strategic hashtags, mentions, or thread indicators when beneficial

**Content Categories to Consider:**
- Industry insights and predictions
- Personal/professional lessons learned
- Hot takes on trending business/tech topics
- Behind-the-scenes professional experiences
- Actionable tips and frameworks
- Contrarian viewpoints on popular opinions

**Viral Content Strategies to Use:**
1. **Trend Hijacking**: Connect current events/viral topics to your professional expertise
2. **Contrarian Wisdom**: Challenge popular opinions with data-backed alternatives
3. **Behind-the-Scenes**: Share authentic founder/leader experiences and lessons
4. **Framework Thinking**: Present complex ideas in simple, actionable frameworks
5. **Future Prediction**: Make bold but educated predictions about industry trends
6. **Vulnerability + Value**: Share failures/mistakes with actionable takeaways
7. **Data Storytelling**: Use specific metrics to tell compelling business stories
8. **Pattern Recognition**: Identify and share non-obvious patterns in business/tech

**Professional Context Integration:**
- Website: https://rakeshroushan.com (AI/SaaS expertise, thought leadership)
- LinkedIn: linkedin.com/in/rakeshroushan1002 (professional background, network)
- Target Hashtags: {', '.join(self.brand.target_hashtags[:3])}
- Inspiration Profiles: {', '.join([profile['handle'] for profile in self.brand.inspiration_profiles[:3]])}

**Output Requirements:**
- Provide {count} original post options ranked by viral potential
- Each post should authentically reflect your professional voice and expertise
- Include trending topic/narrative that inspired each post
- Provide brief explanation (1-2 sentences) for viral potential
- Ensure all content maintains professional credibility

{format_instruction}

**Additional Guidelines:**
- Maintain authenticity to your professional brand
- Avoid controversial topics that could damage professional reputation
- Focus on value-driven content that showcases expertise
- Consider timing and current events relevance
- Include specific numbers, company names, or recent events when possible
- Use curiosity gaps, pattern interrupts, and contrarian insights for viral potential

Generate exactly {count} different post options ranked by viral potential (highest first). Each should be authentic to your professional persona while maximizing engagement.
"""

    def _parse_structured_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse structured text response into post objects"""
        posts = []
        
        try:
            # Split by "Post Option" patterns
            import re
            sections = re.split(r'Post Option \d+:', content)
            
            for i, section in enumerate(sections[1:], 1):  # Skip first empty section
                lines = section.strip().split('\n')
                
                post_content = ""
                trending_inspiration = ""
                viral_potential = ""
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(('Trending inspiration:', 'Viral potential:')):
                        if not post_content:
                            post_content = line
                    elif line.startswith('Trending inspiration:'):
                        trending_inspiration = line.replace('Trending inspiration:', '').strip()
                    elif line.startswith('Viral potential:'):
                        viral_potential = line.replace('Viral potential:', '').strip()
                
                if post_content:
                    post = {
                        'content': post_content,
                        'trending_inspiration': trending_inspiration,
                        'viral_potential': viral_potential,
                        'character_count': len(post_content),
                        'viral_score': 8.0 - (i * 0.2),  # Decreasing score
                        'option_number': i
                    }
                    posts.append(post)
            
        except Exception as e:
            logger.error(f"Error parsing structured response: {e}")
            # Fallback: try to extract any content
            lines = content.split('\n')
            for line in lines:
                if line.strip() and len(line) > 20 and not line.startswith(('Post Option', 'Trending', 'Viral')):
                    posts.append({
                        'content': line.strip()[:280],
                        'trending_inspiration': 'Failed to parse',
                        'viral_potential': 'Failed to parse',
                        'character_count': len(line.strip()[:280]),
                        'viral_score': 7.0
                    })
                    if len(posts) >= 3:  # Limit fallback posts
                        break
        
        return posts
    
    def _fallback_research_driven_posts(self, count: int, output_format: str) -> Dict[str, Any]:
        """Fallback posts for research-driven approach"""
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        
        fallback_posts = [
            {
                "content": f"Most AI tools solve yesterday's problems. The real opportunity? Building for tomorrow's workflows. Here's what I'm seeing... {self.brand.target_hashtags[0]}",
                "trending_inspiration": "Current AI tool proliferation and future workflow evolution",
                "viral_potential": "Contrarian insight about AI tool market with future prediction hook",
                "viral_score": 8.3,
                "character_count": 0
            },
            {
                "content": f"Spent 3 years building {self.brand.expertise_areas[0]} systems. Biggest lesson: Start with the problem, not the technology. Most founders do it backwards.",
                "trending_inspiration": "Founder journey and technical implementation lessons",
                "viral_potential": "Personal experience with contrarian startup advice",
                "viral_score": 8.1,
                "character_count": 0
            },
            {
                "content": f"Everyone's talking about AI replacing jobs. Reality: It's amplifying human judgment. The future belongs to AI-human collaboration, not replacement. {self.brand.target_hashtags[0]}",
                "trending_inspiration": "AI job displacement narrative trending on social media",
                "viral_potential": "Challenges popular opinion with nuanced perspective on AI future",
                "viral_score": 7.9,
                "character_count": 0
            }
        ]
        
        # Calculate character counts
        for post in fallback_posts:
            post['character_count'] = len(post['content'])
        
        return {
            'posts': fallback_posts[:count],
            'generated_at': current_time.isoformat(),
            'ai_model': 'fallback',
            'approach': 'research_driven'
        }
    
    def _adjust_viral_score(self, content: str, base_score: float) -> float:
        """Adjust viral score based on content quality factors"""
        score = base_score
        
        # Penalize generic content
        generic_phrases = ['most people', 'everyone says', 'hot take', 'unpopular opinion', 'plot twist']
        generic_count = sum(1 for phrase in generic_phrases if phrase.lower() in content.lower())
        if generic_count > 1:
            score -= 1.5
        
        # Reward specific numbers/companies/names
        import re
        numbers = len(re.findall(r'\$\d+[KMB]|\d+%|\d+x', content))
        companies = len(re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]*)*', content))
        if numbers > 0:
            score += 0.5
        if companies > 1:
            score += 0.3
        
        # Ensure reasonable range
        return max(4.0, min(9.0, score))
