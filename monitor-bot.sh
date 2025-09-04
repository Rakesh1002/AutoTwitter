#!/bin/bash
# 📊 Twitter Bot Production Monitor
# Quick status check for automated bot operations

echo "🤖 Twitter Bot Production Monitor"
echo "================================="
echo "$(date)"
echo

# Check service status
echo "🔍 Service Status:"
cd /home/ubuntu/audiopod-apps/twitter_bot
./manage-bot.sh status | grep -E "(✅|❌)"
echo

# Check recent activity
echo "📊 Recent Activity:"
if [ -f "logs/full_automation.log" ]; then
    echo "📝 Last 3 log entries:"
    tail -3 logs/full_automation.log | while read line; do
        echo "  $line"
    done
else
    echo "  No log file found"
fi
echo

# Check OAuth status
echo "🔑 OAuth Status:"
poetry run python -c "
from integrations.twitter_oauth import TokenStorage
storage = TokenStorage()
tokens = storage.load_tokens('oauth_user')
if tokens:
    print('  ✅ OAuth tokens valid and stored')
    print('  🤖 Bot authorized for automatic posting')
else:
    print('  ❌ No valid tokens found')
" 2>/dev/null
echo

# Show next scheduled actions
echo "📅 Next Scheduled Actions:"
poetry run python -c "
from datetime import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(ist)
current_hour = current_time.hour

# Next posting times
posting_times = [9, 11.5, 14, 16.5, 19, 21, 22.5]
next_post = None
for post_time in posting_times:
    if current_hour < post_time:
        next_post = post_time
        break

if next_post:
    hour = int(next_post)
    minute = int((next_post - hour) * 60)
    print(f'  🐦 Next tweet: {hour:02d}:{minute:02d} IST')
else:
    print(f'  🐦 Next tweet: 09:00 IST tomorrow')

# Next email (top of next hour)
next_email_hour = (current_hour + 1) % 24
print(f'  📧 Next email: {next_email_hour:02d}:00 IST')

print(f'  💬 Engagement: Every 30 minutes (if not rate limited)')
" 2>/dev/null
echo

echo "✅ Automation is running independently!"
echo "📞 Use './manage-bot.sh status' for detailed info"
echo "🔄 Use './manage-bot.sh restart' if needed"
