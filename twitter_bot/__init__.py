"""
Twitter Automation Platform
A unified system for Twitter bot automation and email content pipeline
"""

__version__ = "2.0.0"
__author__ = "AI Assistant"
__description__ = "AI-powered Twitter automation"

# Core modules
from .core.config import Config
from .core.database import Database
from .core.security import SecurityManager

# Main components
from .bot.client import TwitterBotClient
from .email_pipeline.pipeline import EmailPipeline
from .ai.unified_client import UnifiedAIClient

__all__ = [
    "Config",
    "Database", 
    "SecurityManager",
    "TwitterBotClient",
    "EmailPipeline",
    "UnifiedAIClient",
]
