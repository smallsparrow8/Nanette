"""
Configuration settings for Nanette
Loads environment variables and provides typed configuration
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # =========================================================================
    # ESSENTIAL API KEYS
    # =========================================================================
    anthropic_api_key: str = Field(..., description="Claude API key from Anthropic")
    discord_bot_token: Optional[str] = Field(None, description="Discord bot token")
    discord_client_id: Optional[str] = Field(None, description="Discord client ID")
    telegram_bot_token: Optional[str] = Field(None, description="Telegram bot token")

    # =========================================================================
    # BLOCKCHAIN RPC PROVIDERS
    # =========================================================================
    alchemy_api_key: Optional[str] = Field(None, description="Alchemy API key")
    infura_api_key: Optional[str] = Field(None, description="Infura API key")
    helius_api_key: Optional[str] = Field(None, description="Helius API key for Solana")

    # EVM Networks
    ethereum_rpc_url: str = Field("https://eth.llamarpc.com", description="Ethereum RPC URL")
    bsc_rpc_url: str = Field("https://bsc-dataseed.binance.org/", description="BSC RPC URL")
    polygon_rpc_url: str = Field("https://polygon-rpc.com/", description="Polygon RPC URL")
    arbitrum_rpc_url: str = Field("https://arb1.arbitrum.io/rpc", description="Arbitrum RPC URL")
    base_rpc_url: str = Field("https://mainnet.base.org", description="Base RPC URL")
    optimism_rpc_url: str = Field("https://mainnet.optimism.io", description="Optimism RPC URL")

    # Solana
    solana_rpc_url: str = Field("https://api.mainnet-beta.solana.com", description="Solana RPC URL")

    # =========================================================================
    # BLOCKCHAIN EXPLORERS
    # =========================================================================
    etherscan_api_key: Optional[str] = Field(None, description="Etherscan API key")
    bscscan_api_key: Optional[str] = Field(None, description="BscScan API key")
    polygonscan_api_key: Optional[str] = Field(None, description="PolygonScan API key")
    arbiscan_api_key: Optional[str] = Field(None, description="Arbiscan API key")
    basescan_api_key: Optional[str] = Field(None, description="Basescan API key")
    optimism_etherscan_api_key: Optional[str] = Field(None, description="Optimism Etherscan API key")
    solscan_api_key: Optional[str] = Field(None, description="Solscan API key")

    # =========================================================================
    # SOCIAL MEDIA APIs
    # =========================================================================
    twitter_api_key: Optional[str] = Field(None, description="Twitter API key")
    twitter_api_secret: Optional[str] = Field(None, description="Twitter API secret")
    twitter_bearer_token: Optional[str] = Field(None, description="Twitter bearer token")
    twitter_access_token: Optional[str] = Field(None, description="Twitter access token")
    twitter_access_secret: Optional[str] = Field(None, description="Twitter access secret")

    reddit_client_id: Optional[str] = Field(None, description="Reddit client ID")
    reddit_client_secret: Optional[str] = Field(None, description="Reddit client secret")
    reddit_user_agent: str = Field("Nanette/1.0", description="Reddit user agent")

    telegram_api_id: Optional[str] = Field(None, description="Telegram API ID")
    telegram_api_hash: Optional[str] = Field(None, description="Telegram API hash")

    # =========================================================================
    # DATABASE
    # =========================================================================
    database_url: str = Field("sqlite:///nanette.db", description="Database connection URL")

    # =========================================================================
    # REDIS
    # =========================================================================
    redis_url: str = Field("redis://localhost:6379/0", description="Redis connection URL")

    # =========================================================================
    # APPLICATION SETTINGS
    # =========================================================================
    environment: str = Field("development", description="Environment: development, staging, production")
    log_level: str = Field("INFO", description="Logging level")

    api_host: str = Field("0.0.0.0", description="API server host")
    api_port: int = Field(8000, description="API server port")

    rate_limit_per_minute: int = Field(30, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(500, description="Rate limit per hour")

    max_concurrent_analyses: int = Field(5, description="Maximum concurrent contract analyses")
    analysis_timeout_seconds: int = Field(300, description="Analysis timeout in seconds")

    cache_ttl_seconds: int = Field(3600, description="Cache TTL in seconds")
    enable_cache: bool = Field(True, description="Enable caching")

    # =========================================================================
    # SECURITY
    # =========================================================================
    api_secret_key: str = Field("change-me-in-production", description="API secret key")
    cors_origins: str = Field("http://localhost:3000,http://localhost:8000", description="Allowed CORS origins")

    # =========================================================================
    # FEATURE FLAGS
    # =========================================================================
    enable_social_monitoring: bool = Field(False, description="Enable social media monitoring")
    enable_telegram_bot: bool = Field(True, description="Enable Telegram bot")
    enable_discord_bot: bool = Field(True, description="Enable Discord bot")
    enable_solana_analysis: bool = Field(True, description="Enable Solana analysis")

    # =========================================================================
    # CHANNEL ANALYSIS
    # =========================================================================
    enable_channel_analysis: bool = Field(True, description="Enable channel/group message analysis")
    channel_response_cooldown: int = Field(300, description="Seconds between unsolicited channel responses")
    channel_max_stored_messages: int = Field(10000, description="Max messages stored per channel")
    channel_cleanup_days: int = Field(30, description="Delete messages older than this many days")

    # =========================================================================
    # NANETTE PERSONALITY
    # =========================================================================
    nanette_personality_mode: str = Field("mystical_guardian", description="Nanette's personality mode")
    nanette_response_style: str = Field("friendly_but_cautious", description="Nanette's response style")

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"

    def get_explorer_api_key(self, blockchain: str) -> Optional[str]:
        """Get the appropriate explorer API key for a blockchain"""
        explorer_map = {
            'ethereum': self.etherscan_api_key,
            'eth': self.etherscan_api_key,
            'bsc': self.bscscan_api_key,
            'polygon': self.polygonscan_api_key,
            'arbitrum': self.arbiscan_api_key,
            'arb': self.arbiscan_api_key,
            'base': self.basescan_api_key,
            'optimism': self.optimism_etherscan_api_key,
            'op': self.optimism_etherscan_api_key,
            'solana': self.solscan_api_key,
            'sol': self.solscan_api_key,
        }
        return explorer_map.get(blockchain.lower())

    def get_rpc_url(self, blockchain: str) -> str:
        """Get the RPC URL for a blockchain"""
        rpc_map = {
            'ethereum': self.ethereum_rpc_url,
            'eth': self.ethereum_rpc_url,
            'bsc': self.bsc_rpc_url,
            'polygon': self.polygon_rpc_url,
            'matic': self.polygon_rpc_url,
            'arbitrum': self.arbitrum_rpc_url,
            'arb': self.arbitrum_rpc_url,
            'base': self.base_rpc_url,
            'optimism': self.optimism_rpc_url,
            'op': self.optimism_rpc_url,
            'solana': self.solana_rpc_url,
            'sol': self.solana_rpc_url,
        }
        url = rpc_map.get(blockchain.lower())
        if not url:
            raise ValueError(f"Unsupported blockchain: {blockchain}")
        return url


# Global settings instance
settings = Settings()
