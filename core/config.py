#!/usr/bin/env python3
"""
Unified Configuration Management
Secure, type-safe configuration with environment detection
"""

import os
import yaml
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

@dataclass
class TwitterConfig:
    """Twitter API configuration - supports both OAuth 1.0a and OAuth 2.0"""
    # Legacy OAuth 1.0a credentials (optional)
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str
    bearer_token: str
    
    # OAuth 2.0 credentials (preferred for write permissions)
    oauth_client_id: str
    oauth_client_secret: str
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_user_id: str
    
    def is_valid(self) -> bool:
        """Validate Twitter configuration - OAuth 2.0 OR OAuth 1.0a"""
        # Check OAuth 2.0 credentials first (preferred)
        oauth2_fields = [
            self.oauth_client_id, self.oauth_client_secret, self.oauth_access_token
        ]
        if all(field and len(field) > 10 for field in oauth2_fields):
            return True
        
        # Fallback to legacy OAuth 1.0a credentials
        legacy_fields = [
            self.api_key, self.api_secret, self.access_token,
            self.access_token_secret, self.bearer_token
        ]
        return all(field and len(field) > 10 for field in legacy_fields)
    
    def has_oauth2(self) -> bool:
        """Check if OAuth 2.0 credentials are available"""
        oauth2_fields = [
            self.oauth_client_id, self.oauth_client_secret, self.oauth_access_token
        ]
        return all(field and len(field) > 10 for field in oauth2_fields)
    
    def has_legacy(self) -> bool:
        """Check if legacy OAuth 1.0a credentials are available"""
        legacy_fields = [
            self.api_key, self.api_secret, self.access_token,
            self.access_token_secret, self.bearer_token
        ]
        return all(field and len(field) > 10 for field in legacy_fields)

class AIProvider(Enum):
    """AI provider options"""
    GEMINI = "gemini"
    CLAUDE = "claude"
    OPENAI = "openai"

@dataclass
class GeminiConfig:
    """Gemini AI configuration"""
    api_key: str
    model_name: str = "gemini-2.5-pro"
    temperature: float = 0.8
    top_p: float = 0.9
    top_k: int = 40
    max_output_tokens: int = 2048
    
    def is_valid(self) -> bool:
        """Validate Gemini configuration"""
        return bool(self.api_key and len(self.api_key) > 10)

@dataclass
class ClaudeConfig:
    """Claude AI configuration"""
    api_key: str
    model_name: str = "claude-sonnet-4-20250514"  # Latest reasoning model
    temperature: float = 0.8
    max_tokens: int = 2048
    
    def is_valid(self) -> bool:
        """Validate Claude configuration"""
        return bool(self.api_key and len(self.api_key) > 10)

@dataclass
class OpenAIConfig:
    """OpenAI configuration"""
    api_key: str
    model_name: str = "gpt-5-mini-2025-08-07" 
    temperature: float = 0.8
    max_tokens: int = 2048
    
    def is_valid(self) -> bool:
        """Validate OpenAI configuration"""
        return bool(self.api_key and len(self.api_key) > 10)

@dataclass
class AIConfig:
    """Unified AI configuration"""
    provider: AIProvider = AIProvider.GEMINI
    gemini: GeminiConfig = None
    claude: ClaudeConfig = None
    openai: OpenAIConfig = None
    
    def get_current_provider_config(self):
        """Get configuration for current provider"""
        if self.provider == AIProvider.GEMINI:
            return self.gemini
        elif self.provider == AIProvider.CLAUDE:
            return self.claude
        elif self.provider == AIProvider.OPENAI:
            return self.openai
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")
    
    def is_valid(self) -> bool:
        """Validate current provider configuration"""
        current_config = self.get_current_provider_config()
        return current_config and current_config.is_valid()

@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_secure: bool
    from_email: str
    to_email: str
    
    def is_valid(self) -> bool:
        """Validate email configuration"""
        required_fields = [
            self.smtp_host, self.smtp_user, self.smtp_password,
            self.from_email, self.to_email
        ]
        return all(field for field in required_fields) and self.smtp_port > 0

@dataclass
class SearxngConfig:
    """SearXNG configuration"""
    base_url: str = "http://localhost:8080"
    timeout: int = 30
    
    def is_valid(self) -> bool:
        """Validate SearXNG configuration"""
        return bool(self.base_url and self.timeout > 0)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///twitter_automation.db"
    echo: bool = False
    pool_size: int = 10
    
    def is_valid(self) -> bool:
        """Validate database configuration"""
        return bool(self.url)

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    encryption_key: Optional[str] = None
    rate_limit_per_hour: int = 100
    max_retries: int = 3
    
    def is_valid(self) -> bool:
        """Validate security configuration"""
        return bool(self.secret_key and len(self.secret_key) >= 32)

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    file_path: str = "logs/twitter_automation.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class BrandConfig:
    """Brand and voice configuration"""
    persona: str = "AI Industry Thought Leader & Tech Strategist"
    tone: str = "authoritative, analytical, forward-thinking, contrarian when necessary"
    big_idea: str = "Building AI/SaaS Startups in Public + Actionable Growth Hacks + Navigating the Founder's Journey"
    
    # Core expertise areas aligned with top profiles
    expertise_areas: list = field(default_factory=lambda: [
        "AI implementation business", "SaaS product strategy", "startup scaling frameworks",
        "prompt engineering business", "MLOps platform strategy", "AI tools productivity",
        "building in public SaaS", "product-led growth", "AI automation workflows",
        "startup founder lessons", "tech leadership insights", "digital transformation AI"
    ])
    
    # Target profiles to emulate
    inspiration_profiles: list = field(default_factory=lambda: [
        {"handle": "@sama", "style": "Bold predictions, industry insights, contrarian takes"},
        {"handle": "@AndrewYNg", "style": "Educational frameworks, AI practical applications"},
        {"handle": "@paulg", "style": "Startup wisdom, counterintuitive insights"},
        {"handle": "@naval", "style": "Philosophy + business, tweetstorms, frameworks"},
        {"handle": "@dharmesh", "style": "SaaS metrics, growth hacks, data-driven insights"},
        {"handle": "@agazdecki", "style": "SaaS acquisition stories, founder journey"},
        {"handle": "@levelsio", "style": "Building in public, indie hacking, transparent metrics"},
        {"handle": "@balajis", "style": "Tech trends, future predictions, data narratives"}
    ])
    
    # Viral content keywords for RSS/trend discovery
    viral_keywords: list = field(default_factory=lambda: [
        "AI implementation business", "SaaS product strategy", "startup scaling frameworks",
        "AI tools productivity", "building in public SaaS", "product-led growth",
        "tech leadership insights", "digital transformation AI", "AI automation workflows",
        "startup founder lessons", "SaaS metrics optimization", "AI ethics business"
    ])
    
    target_hashtags: list = field(default_factory=lambda: [
        "#AI", "#SaaS", "#BuildInPublic", "#StartupLife", "#TechStrategy", 
        "#ProductStrategy", "#AITools", "#FounderJourney", "#Growth", "#Innovation"
    ])
    
    # Viral thread frameworks
    thread_frameworks: list = field(default_factory=lambda: [
        "listicle", "problem_solution", "storytelling", "before_after_bridge", "contrarian"
    ])
    
    # Hook patterns for viral content
    hook_patterns: list = field(default_factory=lambda: [
        "Most people think {common_belief}, but {contrarian_insight}...",
        "I made a $50K mistake in my first startup. Here's what I learned...",
        "Everyone's talking about {trending_topic}. Here's what they're missing...",
        "Unpopular opinion: {controversial_take}",
        "How I went from {before_state} to {after_state} in {timeframe}...",
        "The biggest lie in {industry}: {false_belief}. Here's the truth...",
        "10 lessons from building {specific_achievement}:",
        "Plot twist: {unexpected_insight} (and why it matters)..."
    ])
    
class Config:
    """Unified configuration manager"""
    
    def __init__(self, env_path: Optional[str] = None, config_path: Optional[str] = None):
        """Initialize configuration"""
        self.env_path = env_path or ".env"
        self.config_path = config_path or "config/config.yml"
        self.environment = self._detect_environment()
        
        # Load configurations
        self._load_env_file()
        self._load_yaml_config()
        
        # Initialize configuration objects
        self.twitter = self._load_twitter_config()
        self.ai = self._load_ai_config()
        self.email = self._load_email_config()
        self.searxng = self._load_searxng_config()
        self.database = self._load_database_config()
        self.security = self._load_security_config()
        self.logging = self._load_logging_config()
        self.brand = self._load_brand_config()
        
        # Backward compatibility - expose current AI provider as 'gemini'
        self.gemini = self.ai.get_current_provider_config()
        
        logger.info(f"Configuration loaded for environment: {self.environment.value}")
    
    def _detect_environment(self) -> Environment:
        """Detect current environment"""
        env = os.getenv("ENVIRONMENT", "development").lower()
        try:
            return Environment(env)
        except ValueError:
            logger.warning(f"Unknown environment '{env}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_env_file(self):
        """Load environment variables.
        Priority:
        1) Explicit env_path if provided
        2) production.env when ENVIRONMENT=production
        3) .env as default
        Note: We do not override existing process env values.
        """
        loaded_any = False
        # 1) Explicit path
        if self.env_path and Path(self.env_path).exists():
            load_dotenv(self.env_path, override=False)
            logger.info(f"Loaded environment from: {self.env_path}")
            loaded_any = True
        else:
            if self.env_path:
                logger.warning(f"Environment file not found: {self.env_path}")
        
        # 2) If production and production.env exists, load it (non-override)
        if self.environment == Environment.PRODUCTION:
            prod_path = Path("production.env")
            if prod_path.exists():
                load_dotenv(str(prod_path), override=False)
                logger.info("Merged environment from: production.env")
                loaded_any = True
        
        # 3) Load .env as baseline if nothing loaded yet and it exists
        default_env = Path(".env")
        if not loaded_any and default_env.exists():
            load_dotenv(str(default_env), override=False)
            logger.info("Loaded environment from: .env")
        elif not loaded_any:
            logger.warning("No environment file found (.env or production.env)")
    
    def _load_yaml_config(self):
        """Load YAML configuration"""
        self.yaml_config = {}
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                self.yaml_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded YAML config from: {self.config_path}")
        else:
            logger.info(f"YAML config not found: {self.config_path}")
    
    def _get_config_value(self, key: str, default: Any = None, 
                         config_section: Optional[str] = None) -> Any:
        """Get configuration value from env or YAML"""
        # Try environment variable first
        env_value = os.getenv(key.upper())
        if env_value is not None:
            return env_value
        
        # Try YAML configuration
        if config_section and config_section in self.yaml_config:
            section = self.yaml_config[config_section]
            if key.lower() in section:
                return section[key.lower()]
        
        # Try root YAML configuration
        if key.lower() in self.yaml_config:
            return self.yaml_config[key.lower()]
        
        return default
    
    def _load_twitter_config(self) -> TwitterConfig:
        """Load Twitter configuration - supports both OAuth 1.0a and OAuth 2.0"""
        return TwitterConfig(
            # Legacy OAuth 1.0a credentials
            api_key=self._get_config_value("TWITTER_API_KEY", ""),
            api_secret=self._get_config_value("TWITTER_API_SECRET", ""),
            access_token=self._get_config_value("TWITTER_ACCESS_TOKEN", ""),
            access_token_secret=self._get_config_value("TWITTER_ACCESS_TOKEN_SECRET", ""),
            bearer_token=self._get_config_value("TWITTER_BEARER_TOKEN", ""),
            
            # OAuth 2.0 credentials
            oauth_client_id=self._get_config_value("TWITTER_OAUTH_CLIENT_ID", "").strip('"'),
            oauth_client_secret=self._get_config_value("TWITTER_OAUTH_CLIENT_SECRET", "").strip('"'),
            oauth_access_token=self._get_config_value("TWITTER_OAUTH_ACCESS_TOKEN", ""),
            oauth_refresh_token=self._get_config_value("TWITTER_OAUTH_REFRESH_TOKEN", ""),
            oauth_user_id=self._get_config_value("TWITTER_OAUTH_USER_ID", "")
        )
    
    def _load_ai_config(self) -> AIConfig:
        """Load AI configuration with multiple provider support"""
        
        # Determine AI provider from environment or config
        provider_str = self._get_config_value("AI_PROVIDER", "gemini").lower()
        try:
            provider = AIProvider(provider_str)
        except ValueError:
            logger.warning(f"Unknown AI provider '{provider_str}', defaulting to Gemini")
            provider = AIProvider.GEMINI
        
        # Load Gemini configuration
        gemini_config = GeminiConfig(
            api_key=self._get_config_value("GEMINI_API_KEY", ""),
            model_name=self._get_config_value("GEMINI_MODEL", "gemini-2.5-pro"),
            temperature=float(self._get_config_value("GEMINI_TEMPERATURE", "0.8")),
            top_p=float(self._get_config_value("GEMINI_TOP_P", "0.9")),
            top_k=int(self._get_config_value("GEMINI_TOP_K", "40")),
            max_output_tokens=int(self._get_config_value("GEMINI_MAX_TOKENS", "2048"))
        )
        
        # Load Claude configuration
        claude_config = ClaudeConfig(
            api_key=self._get_config_value("CLAUDE_API_KEY", ""),
            model_name=self._get_config_value("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            temperature=float(self._get_config_value("CLAUDE_TEMPERATURE", "0.8")),
            max_tokens=int(self._get_config_value("CLAUDE_MAX_TOKENS", "2048"))
        )
        
        # Load OpenAI configuration
        openai_config = OpenAIConfig(
            api_key=self._get_config_value("OPENAI_API_KEY", ""),
            model_name=self._get_config_value("OPENAI_MODEL", "gpt-4o"),
            temperature=float(self._get_config_value("OPENAI_TEMPERATURE", "0.8")),
            max_tokens=int(self._get_config_value("OPENAI_MAX_TOKENS", "2048"))
        )
        
        return AIConfig(
            provider=provider,
            gemini=gemini_config,
            claude=claude_config,
            openai=openai_config
        )
    
    def _load_email_config(self) -> EmailConfig:
        """Load email configuration"""
        
        smtp_host = self._get_config_value("SMTP_HOST", "")
        smtp_port = int(self._get_config_value("SMTP_PORT", "587"))
        
        # Automatically enable STARTTLS for common secure SMTP providers
        smtp_secure = self._get_config_value("SMTP_SECURE", "auto").lower()
        
        if smtp_secure == "auto":
            # Auto-detect based on host and port
            if ("amazonaws.com" in smtp_host or 
                "gmail.com" in smtp_host or 
                "fastmail.com" in smtp_host or
                smtp_port in [587, 465]):
                smtp_secure = True
            else:
                smtp_secure = False
        else:
            smtp_secure = smtp_secure == "true"
        
        return EmailConfig(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=self._get_config_value("SMTP_USER", ""),
            smtp_password=self._get_config_value("SMTP_PASSWORD", ""),
            smtp_secure=smtp_secure,
            from_email=self._get_config_value("SMTP_FROM", ""),
            to_email=self._get_config_value("TO_EMAIL", "")
        )
    
    def _load_searxng_config(self) -> SearxngConfig:
        """Load SearXNG configuration"""
        return SearxngConfig(
            base_url=self._get_config_value("SEARXNG_URL", "http://localhost:8080"),
            timeout=int(self._get_config_value("SEARXNG_TIMEOUT", "30"))
        )
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            url=self._get_config_value("DATABASE_URL", "sqlite:///twitter_automation.db"),
            echo=self._get_config_value("DATABASE_ECHO", "false").lower() == "true",
            pool_size=int(self._get_config_value("DATABASE_POOL_SIZE", "10"))
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        secret_key = self._get_config_value("SECRET_KEY")
        if not secret_key:
            # Generate a default secret key for development
            import secrets
            secret_key = secrets.token_urlsafe(32)
            logger.warning("Generated temporary secret key - set SECRET_KEY in production")
        
        return SecurityConfig(
            secret_key=secret_key,
            encryption_key=self._get_config_value("ENCRYPTION_KEY"),
            rate_limit_per_hour=int(self._get_config_value("RATE_LIMIT_PER_HOUR", "100")),
            max_retries=int(self._get_config_value("MAX_RETRIES", "3"))
        )
    
    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration"""
        return LoggingConfig(
            level=self._get_config_value("LOG_LEVEL", "INFO"),
            format=self._get_config_value("LOG_FORMAT", 
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
            file_path=self._get_config_value("LOG_FILE", "logs/twitter_automation.log"),
            max_bytes=int(self._get_config_value("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
            backup_count=int(self._get_config_value("LOG_BACKUP_COUNT", "5"))
        )
    
    def _load_brand_config(self) -> BrandConfig:
        """Load brand configuration"""
        brand_section = self.yaml_config.get("brand", {})
        
        return BrandConfig(
            persona=brand_section.get("persona", "Rakesh Roushan"),
            tone=brand_section.get("tone", "professional, analytical, authentic"),
            big_idea=brand_section.get("big_idea", "Building AI/SaaS Startups in Public + Actionable Growth Hacks + Navigating the Founder's Journey"),
            expertise_areas=brand_section.get("expertise_areas", [
                "AI implementation business", "SaaS product strategy", "startup scaling frameworks",
                "prompt engineering business", "MLOps platform strategy", "AI tools productivity",
                "building in public SaaS", "product-led growth", "AI automation workflows",
                "startup founder lessons", "tech leadership insights", "digital transformation AI"
            ]),
            viral_keywords=brand_section.get("viral_keywords", [
                "AI implementation business", "SaaS product strategy", "startup scaling frameworks",
                "AI tools productivity", "building in public SaaS", "product-led growth"
            ]),
            target_hashtags=brand_section.get("target_hashtags", [
                "#AI", "#SaaS", "#BuildInPublic", "#StartupLife", "#TechStrategy", 
                "#ProductStrategy", "#AITools", "#FounderJourney", "#Growth", "#Innovation"
            ])
        )
    
    def validate(self) -> Dict[str, bool]:
        """Validate all configurations"""
        validation_results = {
            "twitter": self.twitter.is_valid(),
            "ai": self.ai.is_valid(),
            "email": self.email.is_valid(),
            "searxng": self.searxng.is_valid(),
            "database": self.database.is_valid(),
            "security": self.security.is_valid(),
        }
        
        # Add backward compatibility
        validation_results["gemini"] = validation_results["ai"]
        
        return validation_results
    
    def get_validation_report(self) -> str:
        """Get detailed validation report"""
        results = self.validate()
        
        report = f"🔍 Configuration Validation Report - {self.environment.value.title()}\n"
        report += "=" * 60 + "\n\n"
        
        for service, is_valid in results.items():
            status = "✅ VALID" if is_valid else "❌ INVALID"
            report += f"{service.capitalize():15} {status}\n"
        
        # Add recommendations for invalid configurations
        if not results["twitter"]:
            report += "\n🔧 Twitter: Configure API keys in environment variables"
        if not results["ai"]:
            current_provider = self.ai.provider.value
            report += f"\n🔧 AI: Configure {current_provider.upper()}_API_KEY for AI-powered content"
            report += f"\n   Current provider: {current_provider.upper()}"
            report += "\n   Available providers: Gemini, Claude, OpenAI (set AI_PROVIDER=gemini/claude/openai)"
        if not results["email"]:
            report += "\n🔧 Email: Configure SMTP settings for email pipeline"
        
        return report
    
    def is_production_ready(self) -> bool:
        """Check if configuration is production ready"""
        results = self.validate()
        required_for_production = ["twitter", "ai", "email", "security"]
        
        return all(results[service] for service in required_for_production)

# Global configuration instance
_config_instance: Optional[Config] = None

def get_config(env_path: Optional[str] = None, 
               config_path: Optional[str] = None,
               force_reload: bool = False) -> Config:
    """Get global configuration instance"""
    global _config_instance
    
    if _config_instance is None or force_reload:
        _config_instance = Config(env_path, config_path)
    
    return _config_instance
