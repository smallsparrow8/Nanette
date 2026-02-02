"""
Database models for Nanette AI Crypto Analyzer
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Project(Base):
    """Cryptocurrency project model"""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    contract_address = Column(String(255), unique=True, nullable=False, index=True)
    blockchain = Column(String(50), nullable=False)  # ethereum, bsc, polygon, solana, etc.
    token_name = Column(String(255), nullable=True)
    token_symbol = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contract_analyses = relationship("ContractAnalysis", back_populates="project", cascade="all, delete-orphan")
    social_metrics = relationship("SocialMetric", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name or 'Unknown'} ({self.contract_address[:10]}...)>"


class ContractAnalysis(Base):
    """Smart contract security analysis results"""
    __tablename__ = 'contract_analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)

    # Overall Safety Metrics
    safety_score = Column(Integer, nullable=False)  # 0-100
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical

    # Analysis Components (stored as JSON)
    vulnerabilities = Column(JSON, nullable=False, default=list)  # List of detected vulnerabilities
    code_quality = Column(JSON, nullable=True)  # Code quality metrics
    tokenomics = Column(JSON, nullable=True)  # Token economics analysis
    liquidity_analysis = Column(JSON, nullable=True)  # Liquidity lock and LP analysis
    ownership_analysis = Column(JSON, nullable=True)  # Owner privileges and controls
    honeypot_check = Column(JSON, nullable=True)  # Honeypot detection results

    # Detailed Scores
    code_quality_score = Column(Integer, nullable=True)  # 0-25
    security_score = Column(Integer, nullable=True)  # 0-40
    tokenomics_score = Column(Integer, nullable=True)  # 0-20
    liquidity_score = Column(Integer, nullable=True)  # 0-15

    # Contract Details
    contract_verified = Column(Boolean, default=False)
    compiler_version = Column(String(50), nullable=True)
    optimization_enabled = Column(Boolean, nullable=True)
    source_code = Column(Text, nullable=True)

    # Analysis Metadata
    analyzer_version = Column(String(20), nullable=True)
    analysis_duration_seconds = Column(Float, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="contract_analyses")

    def __repr__(self):
        return f"<ContractAnalysis {self.id} - Score: {self.safety_score}/100 ({self.risk_level})>"


class SocialMetric(Base):
    """Social media metrics and sentiment analysis"""
    __tablename__ = 'social_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)

    # Platform Information
    platform = Column(String(50), nullable=False)  # twitter, reddit, telegram, discord

    # Sentiment Analysis
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0 (negative to positive)
    sentiment_label = Column(String(20), nullable=True)  # negative, neutral, positive

    # Engagement Metrics (stored as JSON)
    engagement_metrics = Column(JSON, nullable=True)  # likes, shares, comments, members, etc.
    developer_activity = Column(JSON, nullable=True)  # commits, releases, updates
    community_health = Column(JSON, nullable=True)  # growth rate, engagement rate
    red_flags = Column(JSON, nullable=True)  # suspicious activities, bot accounts, etc.

    # Raw Data
    sample_posts = Column(JSON, nullable=True)  # Sample of analyzed posts

    # Metadata
    data_points_analyzed = Column(Integer, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="social_metrics")

    def __repr__(self):
        return f"<SocialMetric {self.platform} - Sentiment: {self.sentiment_score}>"


class AnalysisRequest(Base):
    """Track analysis requests from users"""
    __tablename__ = 'analysis_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Request Details
    user_id = Column(String(255), nullable=False)  # Discord/Telegram user ID
    platform = Column(String(50), nullable=False)  # discord, telegram
    request_type = Column(String(50), nullable=False)  # analyze, check, quick_scan

    # Target Information
    contract_address = Column(String(255), nullable=True)
    blockchain = Column(String(50), nullable=True)
    project_name = Column(String(255), nullable=True)

    # Request Status
    status = Column(String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Results
    result_summary = Column(JSON, nullable=True)

    # Timing
    requested_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    def __repr__(self):
        return f"<AnalysisRequest {self.id} - {self.status}>"


class NanetteInteraction(Base):
    """Track Nanette's interactions for personality learning"""
    __tablename__ = 'nanette_interactions'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # User Information
    user_id = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)

    # Interaction Details
    user_message = Column(Text, nullable=True)
    nanette_response = Column(Text, nullable=True)
    interaction_type = Column(String(50), nullable=True)  # greeting, analysis, question, casual

    # Context
    sentiment = Column(String(20), nullable=True)  # positive, neutral, negative
    topics = Column(JSON, nullable=True)  # Tags/topics discussed

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NanetteInteraction {self.id} - {self.interaction_type}>"


class InteractionAnalysis(Base):
    """Address interaction analysis results with graph data"""
    __tablename__ = 'interaction_analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Target
    contract_address = Column(String(255), nullable=False, index=True)
    blockchain = Column(String(50), nullable=False)

    # Stats
    total_transactions = Column(Integer, nullable=True)
    unique_addresses = Column(Integer, nullable=True)
    total_value_in = Column(Float, nullable=True)
    total_value_out = Column(Float, nullable=True)

    # Analysis results (JSON)
    top_senders = Column(JSON, nullable=True)
    top_receivers = Column(JSON, nullable=True)
    notable_patterns = Column(JSON, nullable=True)
    risk_indicators = Column(JSON, nullable=True)

    # Timing
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<InteractionAnalysis {self.contract_address[:10]}... - {self.total_transactions} txs>"


class ServerConfig(Base):
    """Per-server/chat configuration for admin control"""
    __tablename__ = 'server_configs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Server/chat identification
    server_id = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # discord, telegram, reddit
    server_name = Column(String(255), nullable=True)

    # Owner
    owner_id = Column(String(255), nullable=True)

    # Admin user IDs (JSON list)
    admin_ids = Column(JSON, nullable=True, default=list)

    # Feature toggles (JSON dict: feature_name -> bool)
    # Default: all enabled. Admins can disable specific features.
    enabled_features = Column(JSON, nullable=True, default=dict)

    # Behavior settings
    auto_respond = Column(Boolean, default=True)
    response_cooldown = Column(Integer, default=300)  # seconds
    allow_chat = Column(Boolean, default=True)
    allow_analysis = Column(Boolean, default=True)
    allow_interactions = Column(Boolean, default=True)
    allow_fun = Column(Boolean, default=True)
    allow_crypto_data = Column(Boolean, default=True)

    # Channel analysis (Phase 2)
    channel_analysis_enabled = Column(Boolean, default=False)
    rin_clue_detection = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<ServerConfig {self.platform}:"
            f"{self.server_id}>"
        )

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled"""
        # Feature category mapping
        category_map = {
            'analyze': 'allow_analysis',
            'trace': 'allow_analysis',
            'interactions': 'allow_interactions',
            'price': 'allow_crypto_data',
            'gas': 'allow_crypto_data',
            'info': 'allow_crypto_data',
            'trending': 'allow_crypto_data',
            'ca': 'allow_crypto_data',
            'chat': 'allow_chat',
            'meme': 'allow_fun',
            'joke': 'allow_fun',
            'tip': 'allow_fun',
            'fact': 'allow_fun',
            '8ball': 'allow_fun',
            'flip': 'allow_fun',
            'roll': 'allow_fun',
            'quote': 'allow_fun',
            'fortune': 'allow_fun',
            'paw': 'allow_fun',
            'bork': 'allow_fun',
        }

        # Core commands always enabled
        always_on = {
            'help', 'about', 'greet', 'rintintin',
            'start', 'nanette_config'
        }
        if feature in always_on:
            return True

        # Check per-feature override first
        if self.enabled_features and feature in self.enabled_features:
            return self.enabled_features[feature]

        # Fall back to category toggle
        category = category_map.get(feature)
        if category:
            return getattr(self, category, True)

        return True


class CreatorAnalysis(Base):
    """Creator wallet trace analysis results"""
    __tablename__ = 'creator_analyses'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Target contract
    contract_address = Column(String(255), nullable=False, index=True)
    blockchain = Column(String(50), nullable=False)

    # Deployer info
    deployer_address = Column(String(255), nullable=False, index=True)
    deployer_wallet_age_days = Column(Integer, nullable=True)
    deployer_total_transactions = Column(Integer, nullable=True)
    deployer_balance_eth = Column(Float, nullable=True)
    funding_source = Column(JSON, nullable=True)

    # Sibling contracts (JSON array)
    sibling_contracts = Column(JSON, nullable=True)
    total_siblings = Column(Integer, default=0)
    alive_siblings = Column(Integer, default=0)

    # Creator Trust Score
    creator_trust_score = Column(Integer, nullable=True)
    risk_level = Column(String(20), nullable=True)
    score_breakdown = Column(JSON, nullable=True)

    # Red flags (JSON array)
    red_flags = Column(JSON, nullable=True)

    # Timing
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CreatorAnalysis {self.contract_address[:10]}... deployer={self.deployer_address[:10]}...>"


class ChannelMessage(Base):
    """Stores messages from groups Nanette is monitoring"""
    __tablename__ = 'channel_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Chat identification
    chat_id = Column(String(255), nullable=False, index=True)
    chat_title = Column(String(255), nullable=True)
    chat_type = Column(String(50), nullable=True)
    platform = Column(String(50), nullable=False, default='telegram')

    # Message details
    message_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    text = Column(Text, nullable=True)
    reply_to_message_id = Column(String(255), nullable=True)

    # Analysis results
    is_crypto_relevant = Column(Boolean, default=False)
    detected_topics = Column(JSON, nullable=True)
    detected_addresses = Column(JSON, nullable=True)
    detected_tokens = Column(JSON, nullable=True)

    # Nanette's response (if she responded)
    nanette_responded = Column(Boolean, default=False)
    nanette_response = Column(Text, nullable=True)

    # Timing
    message_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<ChannelMessage {self.chat_id}:"
            f"{self.message_id}>"
        )


class DetectedClue(Base):
    """Tracks RIN clue detections from admin messages"""
    __tablename__ = 'detected_clues'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to the source message
    chat_id = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False, default='telegram')
    message_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)

    # Original message text
    message_text = Column(Text, nullable=True)

    # Detection results
    clue_type = Column(
        String(50), nullable=True
    )  # riddle, thematic_reference, encoded, timeline_hint
    confidence = Column(Float, nullable=False, default=0.0)
    thematic_connections = Column(JSON, nullable=True)
    matched_themes = Column(JSON, nullable=True)
    scores = Column(JSON, nullable=True)

    # Nanette's response
    nanette_response = Column(Text, nullable=True)

    # Timing
    detected_at = Column(DateTime, default=datetime.utcnow)
