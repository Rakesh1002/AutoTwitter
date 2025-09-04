#!/bin/bash
# 📊 Twitter API Usage Monitor
# Real-time monitoring of API usage and optimization metrics

echo "📊 Twitter API Usage Monitor"
echo "============================"
echo "$(date)"
echo

cd /home/ubuntu/audiopod-apps/twitter_bot

# Check API usage statistics
echo "🔍 Current API Usage Statistics:"
poetry run python -c "
from api_usage_tracker import APIUsageTracker
from ai.rss_engagement_generator import RSSEngagementGenerator
from core.config import get_config

tracker = APIUsageTracker()
stats = tracker.get_usage_stats()

print('📈 Monthly Usage:')
for key, value in stats['monthly_usage'].items():
    print(f'  {key}: {value}')

print()
print('📅 Daily Usage:')
for key, value in stats['daily_usage'].items():
    print(f'  {key}: {value}')

print()
print('🚦 Current Limits Status:')
for key, value in stats['limits_status'].items():
    status = '✅' if value else '❌'
    print(f'  {status} {key}: {value}')

print()
print('⚡ Efficiency Metrics:')
for key, value in stats['efficiency_metrics'].items():
    print(f'  {key}: {value}')

print()
print('📡 RSS Engagement Status:')
try:
    config = get_config('production.env')
    rss_gen = RSSEngagementGenerator(config)
    rss_status = rss_gen.get_rss_status()
    print(f'  RSS feeds: {rss_status[\"working_feeds\"]}/{rss_status[\"total_feeds\"]} working')
    print(f'  Cache size: {rss_status[\"cache_size\"]} recent posts')
    print(f'  Status: {\"✅ Active\" if rss_status[\"working_feeds\"] > 0 else \"❌ Inactive\"}')
except Exception as e:
    print(f'  Status: ❌ RSS system error: {e}')

print()
print('📋 Content Deduplication Status:')
try:
    from core.content_tracker import ContentTracker
    content_tracker = ContentTracker()
    stats = content_tracker.get_statistics()
    print(f'  Replied tweets tracked: {stats[\"replied_tweets\"]}')
    print(f'  Used RSS posts: {stats[\"used_rss_posts\"]}')
    print(f'  Email variations: {stats[\"email_content_variations\"]}')
    print(f'  Posted content variations: {stats[\"posted_content_variations\"]}')
    print(f'  Status: ✅ Active deduplication')
except Exception as e:
    print(f'  Status: ❌ Content tracking error: {e}')
" 2>/dev/null

echo
echo "🎯 CORRECTED Content Discovery Strategy:"
echo "========================================="
echo "📝 STANDALONE POSTS (6/day): 100% Web Scraper"
echo "💬 REPLIES/ENGAGEMENTS (10/day): 70% RSS + 30% API"
echo ""
echo "📡 RSS Feeds Purpose: Find posts to reply to"
echo "- Discover content from Naval, Sama, Paul Graham, etc."
echo "- Generate inspired standalone tweets (not direct replies)"
echo "- Usage: Unlimited reads, 24-hour content caching"
echo ""
echo "🐦 Twitter API Purpose: Find viral posts for strategic replies"  
echo "- Discover high-engagement content (3 precious reads/day)"
echo "- Generate direct replies to viral tweets"
echo "- Usage: Strategic viral content targeting"
echo ""
echo "🕷️ Web Scraper Purpose: Generate standalone posts"
echo "- Research trending topics via SearXNG + Beautiful Soup"
echo "- Create original posts from fresh trends and ideas"
echo "- Usage: Unlimited research for 100% of standalone posts"
echo ""
echo "📧 Email Strategy:"
echo "- RSS: Reply opportunities (posts to engage with)"
echo "- Web Scraper: Standalone post ideas (trending topics)" 
echo "- Twitter API: Viral reply opportunities"
echo "- 19 hourly emails (6 AM - 12 AM IST)"
echo

echo "🚀 Service Status:"
./manage-bot.sh status | grep -E "(✅|❌)" | head -5

echo
echo "💡 Pro Tips:"
echo "- Peak efficiency target: 80-90% utilization"
echo "- Monitor daily limits to prevent over-usage"
echo "- Engagement reads count toward read quota"
echo "- Rate limits reset every 15 minutes"
echo
echo "📞 Commands:"
echo "  ./api-usage-monitor.sh  - View this report"
echo "  ./manage-bot.sh logs    - View detailed logs"
echo "  ./monitor-bot.sh        - General service status"
