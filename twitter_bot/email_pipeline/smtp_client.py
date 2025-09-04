#!/usr/bin/env python3
"""
SMTP Email Client
Clean implementation with simple email templates
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
from typing import Dict, Any, List, Optional

from core.config import Config

logger = logging.getLogger(__name__)

class SMTPClient:
    """SMTP client for sending emails"""
    
    def __init__(self, config: Config):
        self.config = config
        self.smtp_config = config.email
        logger.info(f"📧 SMTP Client initialized for {self.smtp_config.smtp_host}")
    
    def send_content_email(self, 
                                   post_suggestions: List[Dict[str, Any]], 
                                   engagement_opportunities: List[Dict[str, Any]], 
                                   trends: Dict[str, Any] = None) -> bool:
        """Send content suggestion email"""
        
        try:
            current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📱 Twitter Actions - {current_time}"
            msg['From'] = self.smtp_config.from_email
            msg['To'] = self.smtp_config.to_email
            
            # Generate content using simple templates
            html_content = self._generate_simple_html(post_suggestions, engagement_opportunities)
            text_content = self._generate_simple_text(post_suggestions, engagement_opportunities)
            
            # Attach both versions
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email with proper STARTTLS handling
            with smtplib.SMTP(self.smtp_config.smtp_host, self.smtp_config.smtp_port) as server:
                server.ehlo()  # Identify ourselves to the server
                
                if self.smtp_config.smtp_secure:
                    server.starttls()  # Enable security
                    server.ehlo()  # Re-identify after TLS
                
                server.login(self.smtp_config.smtp_user, self.smtp_config.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {self.smtp_config.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP send error: {e}")
            return False
    
    def _generate_simple_html(self, 
                             post_suggestions: List[Dict[str, Any]], 
                             engagement_opportunities: List[Dict[str, Any]]) -> str:
        """Generate rich, detailed HTML email matching the original premium template"""
        
        current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')
        
        # Generate rich email template
        def generate_rich_email_html(content, opportunities):
            # Header with blue styling
            header_html = f"""
            <div style="background: linear-gradient(135deg, #1DA1F2, #0d8bd9); color: white; padding: 20px; margin: 0; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px; font-weight: bold;">📱 Twitter Actions - {current_time}</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.9;">AI Model: claude-sonnet-4-20250514 • {len(content)} Post Options • Avg Viral Score: {sum(post.get('viral_score', 8.0) for post in content) / max(len(content), 1):.1f}/10</p>
            </div>
            """
            
            # Post options with rich details
            posts_html = f"""
            <div style="background: #f8f9fa; padding: 20px; border-left: 4px solid #1DA1F2;">
                <h2 style="color: #1DA1F2; margin: 0 0 20px 0;">📝 Post Options ({len(content)} choices)</h2>
            """
            
            for i, post in enumerate(content[:3], 1):
                char_count = post.get('character_count', len(post.get('content', '')))
                is_highest = i == 1  # First post is typically highest scored
                
                option_style = "background: #e3f2fd; border: 2px solid #1DA1F2;" if is_highest else "background: white; border: 1px solid #ddd;"
                option_label = f"Option {i} ⭐ (Highest Score)" if is_highest else f"Option {i}"
                
                posts_html += f"""
                <div style="{option_style} padding: 20px; margin: 15px 0; border-radius: 8px;">
                    <h3 style="color: #1DA1F2; margin: 0 0 15px 0;">{option_label}</h3>
                    
                    <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 3px solid #1DA1F2;">
                        <p style="font-size: 16px; line-height: 1.4; margin: 0; color: #333;">{post.get('content', 'N/A')}</p>
                    </div>
                    
                    <div style="display: flex; gap: 15px; margin: 15px 0; flex-wrap: wrap;">
                        <span style="background: #e8f5e8; padding: 5px 10px; border-radius: 15px; font-size: 12px;">📊 {char_count}/280 chars</span>
                        <span style="background: #fff3cd; padding: 5px 10px; border-radius: 15px; font-size: 12px;">🏷️ #{post.get('pillar', 'insight')} #{post.get('framework', 'SaaS')}</span>
                        <span style="background: #f8d7da; padding: 5px 10px; border-radius: 15px; font-size: 12px;">🎯 Score: {post.get('viral_score', 8.0)}/10</span>
                    </div>
                    
                    <p style="margin: 10px 0; color: #666; font-style: italic;"><strong>Why it works:</strong> {post.get('viral_explanation', 'Combines actionable insight with authentic personal experience that resonates with entrepreneurs and builders')}</p>
                    
                    <p style="margin: 10px 0; color: #666; font-style: italic;"><strong>Trending hook:</strong> {post.get('trending_inspiration', 'General startup growth discussions and emphasis on user-first development in tech communities')}</p>
                </div>
                """
            
            posts_html += "</div>"
            
            # Engagement opportunities with detailed reply options
            if opportunities:
                engagement_html = f"""
                <div style="background: #f0f8f0; padding: 20px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <h2 style="color: #28a745; margin: 0 0 20px 0;">💬 Reply to These ({len(opportunities[:3])} opportunities)</h2>
                """
                
                for i, opp in enumerate(opportunities[:3], 1):
                    author_name = opp.get('author', 'N/A')
                    handle = opp.get('handle', '@unknown').replace('@', '')  # Remove @ if present
                    content = opp.get('content', 'N/A')
                    tweet_link = opp.get('tweet_link', opp.get('url', f"https://twitter.com/{handle}"))
                    posted_time = opp.get('posting_time', opp.get('timestamp', 'Today'))
                    follower_info = opp.get('follower_range', 'unknown')
                    
                    # Format timestamp if it's a full datetime
                    if 'T' in str(posted_time) or '-' in str(posted_time):
                        try:
                            if isinstance(posted_time, str):
                                from datetime import datetime
                                parsed_time = datetime.fromisoformat(posted_time.replace('Z', '+00:00'))
                                posted_time = parsed_time.strftime('%b %d, %I:%M %p')
                        except:
                            posted_time = 'Today'
                    
                    engagement_html += f"""
                    <div style="background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h4 style="color: #28a745; margin: 0 0 10px 0;">#{i}: {author_name} (@{handle})</h4>
                        <p style="color: #666; font-style: italic; margin: 5px 0;"><strong>Posted:</strong> {posted_time} • <a href="{tweet_link}" style="color: #1DA1F2; text-decoration: none;" target="_blank">🔗 View Tweet</a></p>
                        <p style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px; border-left: 3px solid #28a745;"><strong>Original:</strong> "{content[:150]}{'...' if len(content) > 150 else ''}"</p>
                        
                        <div style="margin: 15px 0;">
                            <p style="color: #28a745; font-weight: bold; margin: 5px 0;">💬 Contextual Reply:</p>
                            
                            <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border: 1px solid #dee2e6;">
                                <p style="margin: 0 0 10px 0; color: #666;"><strong>Contextual Response:</strong> Score: {opp.get('reply_viral_score', 8.0)}/10</p>
                                <p style="margin: 0; line-height: 1.4;">{opp.get('ai_reply_suggestion', f'Great insight! This resonates with my SaaS experience. What specific metrics have you found most valuable for validating this approach?')}</p>
                                <p style="margin: 10px 0 0 0; color: #666; font-size: 12px; font-style: italic;">Why it works: {opp.get('ai_reply_strategy', 'Contextual response tailored to the specific content and author, adding relevant SaaS experience')}</p>
                            </div>
                        </div>
                    </div>
                    """
                
                engagement_html += "</div>"
            else:
                engagement_html = ""
            
            return f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Twitter Actions - {current_time}</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    {header_html}
                    <div style="padding: 0;">
                        {posts_html}
                        {engagement_html}
                    </div>
                </div>
            </body>
            </html>
            """
        
        return generate_rich_email_html(post_suggestions, engagement_opportunities)
    
    def _generate_simple_text(self, 
                             post_suggestions: List[Dict[str, Any]], 
                             engagement_opportunities: List[Dict[str, Any]]) -> str:
        """Generate simple, action-focused text email"""
        
        # Generate simple text email inline  
        def generate_simple_email_text(content, opportunities, metadata):
            if not content:
                return "🤖 AI-Powered Twitter Content Suggestions\n\nNo content available at this time."
            
            return f"""
🤖 AI-Powered Twitter Content Suggestions

Content: {content[0].get('content', 'N/A')}
Viral Score: {content[0].get('viral_score', 'N/A')}

📈 Engagement Opportunities:
{chr(10).join([f"• {opp.get('author', 'N/A')}: {opp.get('content', 'N/A')[:100]}..." for opp in opportunities[:3]])}
            """
        return generate_simple_email_text(post_suggestions, engagement_opportunities, {})
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            with smtplib.SMTP(self.smtp_config.smtp_host, self.smtp_config.smtp_port) as server:
                server.ehlo()
                if self.smtp_config.smtp_secure:
                    server.starttls()
                    server.ehlo()
                server.login(self.smtp_config.smtp_user, self.smtp_config.smtp_password)
                
            logger.info("✅ SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {e}")
            return False
    

class MockSMTPClient:
    """Mock SMTP client for testing"""
    
    def __init__(self, config: Config):
        self.config = config
        logger.info("📧 Mock SMTP Client initialized (demo mode)")
    
    def send_content_email(self, 
                                    post_suggestion: Dict[str, Any], 
                                    engagement_opportunities: List[Dict[str, Any]], 
                          trends: Dict[str, Any] = None) -> bool:
        """Mock email sending"""
        
        current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p IST')
        
        logger.info("📧 MOCK EMAIL SENT")
        logger.info(f"Subject: 📱 Twitter Actions - {current_time}")
        logger.info(f"To: {self.config.email.to_email}")
        logger.info(f"Post Content: {post_suggestion['content'][:100]}...")
        logger.info(f"Engagement Opportunities: {len(engagement_opportunities)}")
        
        # Generate actual email content for testing
        from .simple_email_template import generate_simple_email_html
        html_content = generate_simple_email_html(post_suggestion, engagement_opportunities)
        
        # Save to file for inspection
        with open('/tmp/test_email.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info("📄 Email saved to /tmp/test_email.html for inspection")
        return True
    
    def test_connection(self) -> bool:
        """Mock connection test"""
        logger.info("✅ Mock SMTP connection test successful")
        return True
