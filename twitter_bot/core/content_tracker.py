#!/usr/bin/env python3
"""
Content Tracker with Cosine Similarity
Tracks used content to prevent duplicates and ensure freshness using semantic similarity
"""

import logging
import json
import re
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class ContentTracker:
    """Tracks used content to prevent duplicates using cosine similarity"""
    
    def __init__(self, tracker_file: str = "content_tracker_v2.json"):
        self.tracker_file = Path(tracker_file)
        
        # Cosine similarity settings  
        self.similarity_threshold = 0.15  # 15% similarity threshold (practical for short text)
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        
        # Content type classifications for similarity checking
        self.similarity_content_types = {
            'personal_growth', 'advice', 'observation', 'insight', 
            'opinion', 'experience', 'lesson', 'framework'
        }
        
        # News content types (skip similarity check)
        self.news_content_types = {
            'news', 'announcement', 'breaking', 'funding', 'launch', 
            'acquisition', 'merger', 'earnings', 'ipo'
        }
        
        # Initialize data structure
        self.data = self._load_tracker_data()
        
        logger.info("📋 Content Tracker v2 initialized with cosine similarity")
    
    def _load_tracker_data(self) -> Dict[str, Any]:
        """Load tracking data from file"""
        try:
            if self.tracker_file.exists():
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'replied_tweets': {},  # Keep as dict for tweet IDs
                    'used_rss_posts': {},  # Keep as dict for RSS content
                    'email_content': [],   # New: list of content entries
                    'posted_content': [],  # New: list of content entries
                    'content_themes': {}   # Keep as dict for themes
                }
        except Exception as e:
            logger.error(f"Failed to load content tracker: {e}")
            return {
                'replied_tweets': {},
                'used_rss_posts': {},
                'email_content': [],
                'posted_content': [],
                'content_themes': {}
            }
    
    def _save_tracker_data(self):
        """Save tracking data to file"""
        try:
            with open(self.tracker_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save content tracker: {e}")
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for similarity comparison"""
        # Remove URLs, mentions, hashtags
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        content = re.sub(r'@[a-zA-Z0-9_]+', '', content)
        content = re.sub(r'#[a-zA-Z0-9_]+', '', content)
        
        # Remove extra whitespace and special characters
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'[^\w\s]', ' ', content)
        
        return content.strip().lower()
    
    def _classify_content_type(self, content: str, context: str = "") -> str:
        """Classify content type to determine if similarity check should apply"""
        content_lower = (content + " " + context).lower()
        
        # Check for news content (skip similarity)
        for news_type in self.news_content_types:
            if news_type in content_lower:
                return "news"
        
        # Check for personal content (apply similarity)
        for personal_type in self.similarity_content_types:
            if personal_type in content_lower:
                return "personal"
        
        # Default to personal content (safer for avoiding repetition)
        return "personal"
    
    def _calculate_similarity(self, new_content: str, existing_contents: List[str]) -> float:
        """Calculate maximum cosine similarity between new content and existing contents"""
        if not existing_contents:
            return 0.0
        
        try:
            # Preprocess all content
            new_content_clean = self._preprocess_content(new_content)
            existing_contents_clean = [self._preprocess_content(content) for content in existing_contents]
            
            # Create corpus
            all_content = [new_content_clean] + existing_contents_clean
            
            # Vectorize
            tfidf_matrix = self.vectorizer.fit_transform(all_content)
            
            # Calculate similarity between new content (index 0) and all existing content
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            
            # Return maximum similarity
            return float(similarities.max()) if similarities.size > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0
    
    def _clean_old_entries(self):
        """Remove old entries based on retention periods"""
        now = datetime.now()
        retention_periods = {
            'replied_tweets': timedelta(days=30),
            'used_rss_posts': timedelta(days=7),
            'email_content': timedelta(days=14),
            'posted_content': timedelta(days=30),
            'content_themes': timedelta(hours=6)
        }
        
        for content_type, retention_period in retention_periods.items():
            if content_type in self.data:
                cutoff_time = now - retention_period
                
                if content_type in ['email_content', 'posted_content']:
                    # List structure: filter by timestamp
                    self.data[content_type] = [
                        item for item in self.data[content_type]
                        if datetime.fromisoformat(item.get('timestamp', '2025-01-01T00:00:00')) >= cutoff_time
                    ]
                else:
                    # Dict structure: remove old keys
                    old_keys = []
                    for key, timestamp_str in self.data[content_type].items():
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if timestamp < cutoff_time:
                                old_keys.append(key)
                        except (ValueError, TypeError):
                            old_keys.append(key)
                    
                    for key in old_keys:
                        del self.data[content_type][key]
    
    # Posted Content Tracking with Cosine Similarity
    def has_posted_similar_content(self, content: str, content_type: str = "", context: str = "") -> bool:
        """Check if we've posted similar content recently using cosine similarity"""
        self._clean_old_entries()
        
        # Classify content type
        classified_type = self._classify_content_type(content, context)
        
        # Skip similarity check for news content
        if classified_type == "news":
            logger.debug(f"📋 Skipping similarity check for news content")
            return False
        
        # Get existing posted content
        existing_contents = [item['content'] for item in self.data['posted_content']]
        
        if not existing_contents:
            return False
        
        # Calculate similarity
        max_similarity = self._calculate_similarity(content, existing_contents)
        
        is_similar = max_similarity > self.similarity_threshold
        logger.debug(f"📋 Content similarity: {max_similarity:.3f} (threshold: {self.similarity_threshold}, similar: {is_similar})")
        
        return is_similar
    
    def mark_content_posted(self, content: str, content_type: str = "", context: str = ""):
        """Mark content as posted with full content storage"""
        classified_type = self._classify_content_type(content, context)
        
        content_entry = {
            'content': content,
            'content_type': classified_type,
            'original_type': content_type,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        self.data['posted_content'].append(content_entry)
        self._save_tracker_data()
        logger.debug(f"📋 Marked content as posted (type: {classified_type})")
    
    # Email Content Tracking with Cosine Similarity
    def has_generated_similar_email(self, content: str, content_type: str = "", context: str = "") -> bool:
        """Check if we've generated similar email content recently using cosine similarity"""
        self._clean_old_entries()
        
        # Classify content type
        classified_type = self._classify_content_type(content, context)
        
        # Skip similarity check for news content
        if classified_type == "news":
            logger.debug(f"📋 Skipping email similarity check for news content")
            return False
        
        # Get existing email content
        existing_contents = [item['content'] for item in self.data['email_content']]
        
        if not existing_contents:
            return False
        
        # Calculate similarity
        max_similarity = self._calculate_similarity(content, existing_contents)
        
        is_similar = max_similarity > self.similarity_threshold
        logger.debug(f"📋 Email similarity: {max_similarity:.3f} (threshold: {self.similarity_threshold}, similar: {is_similar})")
        
        return is_similar
    
    def mark_email_content_generated(self, content: str, content_type: str = "", context: str = ""):
        """Mark email content as generated with full content storage"""
        classified_type = self._classify_content_type(content, context)
        
        content_entry = {
            'content': content,
            'content_type': classified_type,
            'original_type': content_type,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        self.data['email_content'].append(content_entry)
        self._save_tracker_data()
        logger.debug(f"📋 Marked email content as generated (type: {classified_type})")
    
    # Keep existing methods for RSS and tweet tracking
    def mark_tweet_replied(self, tweet_id: str, reply_id: str = ""):
        """Mark tweet as replied to"""
        if 'replied_tweets' not in self.data:
            self.data['replied_tweets'] = {}
        
        self.data['replied_tweets'][tweet_id] = {
            'reply_id': reply_id,
            'timestamp': datetime.now().isoformat()
        }
        self._save_tracker_data()
        logger.debug(f"📋 Marked tweet {tweet_id} as replied")
    
    def has_replied_to_tweet(self, tweet_id: str) -> bool:
        """Check if we've already replied to a specific tweet"""
        if 'replied_tweets' not in self.data:
            self.data['replied_tweets'] = {}
            return False
        
        return tweet_id in self.data['replied_tweets']
    
    def has_used_rss_post(self, username: str, content: str) -> bool:
        """Check if RSS post has been used"""
        self._clean_old_entries()
        content_hash = f"{username}:{hash(content) % 10000000}"
        return content_hash in self.data['used_rss_posts']
    
    def mark_rss_post_used(self, username: str, content: str):
        """Mark RSS post as used"""
        content_hash = f"{username}:{hash(content) % 10000000}"
        self.data['used_rss_posts'][content_hash] = datetime.now().isoformat()
        self._save_tracker_data()
        logger.debug(f"📋 Marked RSS post from {username} as used")
    
    # Theme tracking (keep existing)
    def has_used_theme_recently(self, theme: str, timeframe_hours: int = 6) -> bool:
        """Check if we've used this theme/topic recently"""
        self._clean_old_entries()
        if theme in self.data['content_themes']:
            theme_time = datetime.fromisoformat(self.data['content_themes'][theme])
            time_diff = datetime.now() - theme_time
            return time_diff.total_seconds() < (timeframe_hours * 3600)
        return False
    
    def mark_theme_used(self, theme: str):
        """Mark theme as recently used"""
        self.data['content_themes'][theme] = datetime.now().isoformat()
        self._save_tracker_data()
        logger.debug(f"📋 Marked theme '{theme}' as used")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get content tracking statistics"""
        self._clean_old_entries()
        return {
            'replied_tweets': len(self.data['replied_tweets']),
            'used_rss_posts': len(self.data['used_rss_posts']),
            'email_content': len(self.data['email_content']),
            'posted_content': len(self.data['posted_content']),
            'content_themes': len(self.data['content_themes']),
            'similarity_threshold': self.similarity_threshold
        }
