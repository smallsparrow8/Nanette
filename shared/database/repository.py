"""
Database repository for CRUD operations
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from .models import (
    Base, Project, ContractAnalysis, SocialMetric,
    AnalysisRequest, NanetteInteraction,
    InteractionAnalysis, CreatorAnalysis,
    ServerConfig, ChannelMessage, DetectedClue,
    MemberProfile, ConversationMemory
)


class Database:
    """Database manager for Nanette"""

    def __init__(self, database_url: str = "sqlite:///nanette.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class ProjectRepository:
    """Repository for Project model operations"""

    def __init__(self, db: Database):
        self.db = db

    def create_or_get(self, contract_address: str, blockchain: str,
                     name: Optional[str] = None,
                     token_name: Optional[str] = None,
                     token_symbol: Optional[str] = None) -> Project:
        """Create a new project or get existing one"""
        with self.db.get_session() as session:
            # Try to find existing project
            project = session.query(Project).filter_by(
                contract_address=contract_address.lower()
            ).first()

            if project:
                # Update fields if provided
                if name:
                    project.name = name
                if token_name:
                    project.token_name = token_name
                if token_symbol:
                    project.token_symbol = token_symbol
                project.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(project)
                return project

            # Create new project
            project = Project(
                contract_address=contract_address.lower(),
                blockchain=blockchain.lower(),
                name=name,
                token_name=token_name,
                token_symbol=token_symbol
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            return project

    def get_by_address(self, contract_address: str) -> Optional[Project]:
        """Get project by contract address"""
        with self.db.get_session() as session:
            return session.query(Project).filter_by(
                contract_address=contract_address.lower()
            ).first()

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        with self.db.get_session() as session:
            return session.query(Project).filter_by(id=project_id).first()


class ContractAnalysisRepository:
    """Repository for ContractAnalysis model operations"""

    def __init__(self, db: Database):
        self.db = db

    def create(self, project_id: int, safety_score: int, risk_level: str,
               vulnerabilities: list, **kwargs) -> ContractAnalysis:
        """Create a new contract analysis"""
        with self.db.get_session() as session:
            analysis = ContractAnalysis(
                project_id=project_id,
                safety_score=safety_score,
                risk_level=risk_level,
                vulnerabilities=vulnerabilities,
                **kwargs
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis

    def get_latest_for_project(self, project_id: int) -> Optional[ContractAnalysis]:
        """Get the most recent analysis for a project"""
        with self.db.get_session() as session:
            return session.query(ContractAnalysis).filter_by(
                project_id=project_id
            ).order_by(desc(ContractAnalysis.analyzed_at)).first()

    def get_all_for_project(self, project_id: int) -> List[ContractAnalysis]:
        """Get all analyses for a project"""
        with self.db.get_session() as session:
            return session.query(ContractAnalysis).filter_by(
                project_id=project_id
            ).order_by(desc(ContractAnalysis.analyzed_at)).all()


class SocialMetricRepository:
    """Repository for SocialMetric model operations"""

    def __init__(self, db: Database):
        self.db = db

    def create(self, project_id: int, platform: str, **kwargs) -> SocialMetric:
        """Create a new social metric"""
        with self.db.get_session() as session:
            metric = SocialMetric(
                project_id=project_id,
                platform=platform,
                **kwargs
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric

    def get_latest_for_project(self, project_id: int, platform: str) -> Optional[SocialMetric]:
        """Get the most recent social metric for a project and platform"""
        with self.db.get_session() as session:
            return session.query(SocialMetric).filter_by(
                project_id=project_id,
                platform=platform
            ).order_by(desc(SocialMetric.collected_at)).first()


class AnalysisRequestRepository:
    """Repository for AnalysisRequest model operations"""

    def __init__(self, db: Database):
        self.db = db

    def create(self, user_id: str, platform: str, request_type: str, **kwargs) -> AnalysisRequest:
        """Create a new analysis request"""
        with self.db.get_session() as session:
            request = AnalysisRequest(
                user_id=user_id,
                platform=platform,
                request_type=request_type,
                **kwargs
            )
            session.add(request)
            session.commit()
            session.refresh(request)
            return request

    def update_status(self, request_id: int, status: str, **kwargs):
        """Update request status"""
        with self.db.get_session() as session:
            request = session.query(AnalysisRequest).filter_by(id=request_id).first()
            if request:
                request.status = status
                for key, value in kwargs.items():
                    setattr(request, key, value)
                session.commit()


class NanetteInteractionRepository:
    """Repository for NanetteInteraction model operations"""

    def __init__(self, db: Database):
        self.db = db

    def create(self, user_id: str, platform: str, **kwargs) -> NanetteInteraction:
        """Create a new interaction record"""
        with self.db.get_session() as session:
            interaction = NanetteInteraction(
                user_id=user_id,
                platform=platform,
                **kwargs
            )
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            return interaction


class InteractionAnalysisRepository:
    """Repository for InteractionAnalysis model operations"""

    def __init__(self, db: Database):
        self.db = db

    def create(self, contract_address: str, blockchain: str, **kwargs) -> InteractionAnalysis:
        """Create a new interaction analysis record"""
        with self.db.get_session() as session:
            analysis = InteractionAnalysis(
                contract_address=contract_address.lower(),
                blockchain=blockchain.lower(),
                **kwargs
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis

    def get_recent(self, contract_address: str, blockchain: str,
                   max_age_hours: int = 1) -> Optional[InteractionAnalysis]:
        """Get recent analysis if cached (within max_age_hours)"""
        from datetime import timedelta
        with self.db.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
            return session.query(InteractionAnalysis).filter(
                InteractionAnalysis.contract_address == contract_address.lower(),
                InteractionAnalysis.blockchain == blockchain.lower(),
                InteractionAnalysis.analyzed_at >= cutoff
            ).order_by(desc(InteractionAnalysis.analyzed_at)).first()


class ServerConfigRepository:
    """Repository for ServerConfig — per-server admin control"""

    def __init__(self, db: Database):
        self.db = db

    def get_or_create(
        self, server_id: str, platform: str,
        server_name: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> ServerConfig:
        """Get existing config or create default one"""
        with self.db.get_session() as session:
            config = session.query(ServerConfig).filter_by(
                server_id=str(server_id),
                platform=platform
            ).first()

            if config:
                if server_name and config.server_name != server_name:
                    config.server_name = server_name
                if owner_id and config.owner_id != owner_id:
                    config.owner_id = str(owner_id)
                config.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(config)
                return config

            config = ServerConfig(
                server_id=str(server_id),
                platform=platform,
                server_name=server_name,
                owner_id=str(owner_id) if owner_id else None,
                admin_ids=[],
                enabled_features={},
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            return config

    def get(self, server_id: str, platform: str) -> Optional[ServerConfig]:
        """Get config for a server/chat"""
        with self.db.get_session() as session:
            return session.query(ServerConfig).filter_by(
                server_id=str(server_id),
                platform=platform
            ).first()

    def update_feature(
        self, server_id: str, platform: str,
        feature: str, enabled: bool
    ) -> Optional[ServerConfig]:
        """Toggle a specific feature on/off"""
        with self.db.get_session() as session:
            config = session.query(ServerConfig).filter_by(
                server_id=str(server_id),
                platform=platform
            ).first()
            if not config:
                return None

            features = config.enabled_features or {}
            features[feature] = enabled
            config.enabled_features = features
            config.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(config)
            return config

    def update_category(
        self, server_id: str, platform: str,
        category: str, enabled: bool
    ) -> Optional[ServerConfig]:
        """Toggle a feature category on/off"""
        category_columns = {
            'analysis': 'allow_analysis',
            'interactions': 'allow_interactions',
            'chat': 'allow_chat',
            'fun': 'allow_fun',
            'crypto': 'allow_crypto_data',
            'auto_respond': 'auto_respond',
            'channel_analysis': 'channel_analysis_enabled',
            'clues': 'rin_clue_detection',
        }

        col = category_columns.get(category)
        if not col:
            return None

        with self.db.get_session() as session:
            config = session.query(ServerConfig).filter_by(
                server_id=str(server_id),
                platform=platform
            ).first()
            if not config:
                return None

            setattr(config, col, enabled)
            config.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(config)
            return config

    def add_admin(
        self, server_id: str, platform: str, user_id: str
    ) -> Optional[ServerConfig]:
        """Add a user as admin"""
        with self.db.get_session() as session:
            config = session.query(ServerConfig).filter_by(
                server_id=str(server_id),
                platform=platform
            ).first()
            if not config:
                return None

            admins = config.admin_ids or []
            uid = str(user_id)
            if uid not in admins:
                admins.append(uid)
                config.admin_ids = admins
                config.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(config)
            return config

    def remove_admin(
        self, server_id: str, platform: str, user_id: str
    ) -> Optional[ServerConfig]:
        """Remove a user from admin list"""
        with self.db.get_session() as session:
            config = session.query(ServerConfig).filter_by(
                server_id=str(server_id),
                platform=platform
            ).first()
            if not config:
                return None

            admins = config.admin_ids or []
            uid = str(user_id)
            if uid in admins:
                admins.remove(uid)
                config.admin_ids = admins
                config.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(config)
            return config

    def is_admin(
        self, server_id: str, platform: str, user_id: str
    ) -> bool:
        """Check if user is admin or owner for this server"""
        with self.db.get_session() as session:
            config = session.query(ServerConfig).filter_by(
                server_id=str(server_id),
                platform=platform
            ).first()
            if not config:
                return False

            uid = str(user_id)
            if config.owner_id == uid:
                return True
            return uid in (config.admin_ids or [])

    def set_cooldown(
        self, server_id: str, platform: str,
        seconds: int
    ) -> Optional[ServerConfig]:
        """Set response cooldown for a server"""
        with self.db.get_session() as session:
            config = session.query(ServerConfig).filter_by(
                server_id=str(server_id),
                platform=platform
            ).first()
            if not config:
                return None

            config.response_cooldown = max(0, seconds)
            config.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(config)
            return config


class ChannelMessageRepository:
    """Repository for ChannelMessage — stores group messages"""

    def __init__(self, db: Database):
        self.db = db

    def create(
        self, chat_id: str, platform: str = 'telegram',
        **kwargs
    ) -> ChannelMessage:
        """Store a new channel message"""
        with self.db.get_session() as session:
            msg = ChannelMessage(
                chat_id=str(chat_id),
                platform=platform,
                **kwargs
            )
            session.add(msg)
            session.commit()
            session.refresh(msg)
            return msg

    def get_recent(
        self, chat_id: str, limit: int = 50
    ) -> List[ChannelMessage]:
        """Get recent messages for a chat"""
        with self.db.get_session() as session:
            return session.query(ChannelMessage).filter_by(
                chat_id=str(chat_id)
            ).order_by(
                desc(ChannelMessage.created_at)
            ).limit(limit).all()

    def get_crypto_relevant(
        self, chat_id: str, limit: int = 20
    ) -> List[ChannelMessage]:
        """Get recent crypto-relevant messages"""
        with self.db.get_session() as session:
            return session.query(ChannelMessage).filter(
                ChannelMessage.chat_id == str(chat_id),
                ChannelMessage.is_crypto_relevant.is_(True)
            ).order_by(
                desc(ChannelMessage.created_at)
            ).limit(limit).all()

    def get_admin_messages(
        self, chat_id: str, limit: int = 50
    ) -> List[ChannelMessage]:
        """Get recent messages from admins"""
        with self.db.get_session() as session:
            return session.query(ChannelMessage).filter(
                ChannelMessage.chat_id == str(chat_id),
                ChannelMessage.is_admin.is_(True)
            ).order_by(
                desc(ChannelMessage.created_at)
            ).limit(limit).all()

    def count_messages(self, chat_id: str) -> int:
        """Count total messages stored for a chat"""
        with self.db.get_session() as session:
            return session.query(ChannelMessage).filter_by(
                chat_id=str(chat_id)
            ).count()

    def cleanup_old(
        self, chat_id: str, max_messages: int = 10000
    ):
        """Remove oldest messages if over limit"""
        with self.db.get_session() as session:
            count = session.query(ChannelMessage).filter_by(
                chat_id=str(chat_id)
            ).count()

            if count > max_messages:
                excess = count - max_messages
                oldest = session.query(ChannelMessage).filter_by(
                    chat_id=str(chat_id)
                ).order_by(
                    ChannelMessage.created_at
                ).limit(excess).all()

                for msg in oldest:
                    session.delete(msg)
                session.commit()


class DetectedClueRepository:
    """Repository for DetectedClue — tracks clue detections"""

    def __init__(self, db: Database):
        self.db = db

    def create(
        self, chat_id: str, platform: str = 'telegram',
        **kwargs
    ) -> DetectedClue:
        """Store a new detected clue"""
        with self.db.get_session() as session:
            clue = DetectedClue(
                chat_id=str(chat_id),
                platform=platform,
                **kwargs
            )
            session.add(clue)
            session.commit()
            session.refresh(clue)
            return clue

    def get_recent(
        self, chat_id: str, limit: int = 20
    ) -> List[DetectedClue]:
        """Get recent clue detections for a chat"""
        with self.db.get_session() as session:
            return session.query(DetectedClue).filter_by(
                chat_id=str(chat_id)
            ).order_by(
                desc(DetectedClue.detected_at)
            ).limit(limit).all()

    def get_by_type(
        self, chat_id: str, clue_type: str,
        limit: int = 10
    ) -> List[DetectedClue]:
        """Get clues by type"""
        with self.db.get_session() as session:
            return session.query(DetectedClue).filter(
                DetectedClue.chat_id == str(chat_id),
                DetectedClue.clue_type == clue_type
            ).order_by(
                desc(DetectedClue.detected_at)
            ).limit(limit).all()

    def get_high_confidence(
        self, chat_id: str, min_confidence: float = 0.8,
        limit: int = 10
    ) -> List[DetectedClue]:
        """Get high-confidence clue detections"""
        with self.db.get_session() as session:
            return session.query(DetectedClue).filter(
                DetectedClue.chat_id == str(chat_id),
                DetectedClue.confidence >= min_confidence
            ).order_by(
                desc(DetectedClue.detected_at)
            ).limit(limit).all()


class CreatorAnalysisRepository:
    """Repository for CreatorAnalysis — creator wallet trace results"""

    def __init__(self, db: Database):
        self.db = db

    def create(self, contract_address: str, blockchain: str,
               deployer_address: str, **kwargs) -> CreatorAnalysis:
        """Create a new creator analysis record"""
        with self.db.get_session() as session:
            analysis = CreatorAnalysis(
                contract_address=contract_address.lower(),
                blockchain=blockchain.lower(),
                deployer_address=deployer_address.lower(),
                **kwargs
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis

    def get_recent(self, contract_address: str, blockchain: str,
                   max_age_hours: int = 6) -> Optional[CreatorAnalysis]:
        """Get cached creator analysis if recent enough"""
        from datetime import timedelta
        with self.db.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
            return session.query(CreatorAnalysis).filter(
                CreatorAnalysis.contract_address == contract_address.lower(),
                CreatorAnalysis.blockchain == blockchain.lower(),
                CreatorAnalysis.analyzed_at >= cutoff
            ).order_by(desc(CreatorAnalysis.analyzed_at)).first()

    def get_by_deployer(self, deployer_address: str,
                        limit: int = 20) -> List[CreatorAnalysis]:
        """Get all analyses for contracts by a specific deployer"""
        with self.db.get_session() as session:
            return session.query(CreatorAnalysis).filter(
                CreatorAnalysis.deployer_address == deployer_address.lower()
            ).order_by(desc(CreatorAnalysis.analyzed_at)).limit(limit).all()


class MemberProfileRepository:
    """Repository for MemberProfile — tracks community members"""

    def __init__(self, db: Database):
        self.db = db

    def get_or_create(
        self, user_id: str, platform: str = 'telegram',
        chat_id: Optional[str] = None,
        username: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> MemberProfile:
        """Get existing member profile or create a new one"""
        with self.db.get_session() as session:
            profile = session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

            if profile:
                # Update last seen and any changed info
                profile.last_seen = datetime.utcnow()
                if username and profile.username != username:
                    profile.username = username
                if display_name and profile.display_name != display_name:
                    profile.display_name = display_name
                if chat_id and not profile.chat_id:
                    profile.chat_id = str(chat_id)
                session.commit()
                session.refresh(profile)
                return profile

            # Create new profile
            profile = MemberProfile(
                user_id=str(user_id),
                platform=platform,
                chat_id=str(chat_id) if chat_id else None,
                username=username,
                display_name=display_name,
                topics_discussed=[],
                interests=[],
                notable_facts=[],
                contracts_asked_about=[],
                custom_tags=[]
            )
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile

    def get(self, user_id: str, platform: str = 'telegram') -> Optional[MemberProfile]:
        """Get a member profile by user ID"""
        with self.db.get_session() as session:
            return session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

    def update_activity(
        self, user_id: str, platform: str = 'telegram',
        message_text: Optional[str] = None,
        interacted_with_nanette: bool = False
    ) -> Optional[MemberProfile]:
        """Update member activity metrics"""
        with self.db.get_session() as session:
            profile = session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

            if not profile:
                return None

            profile.message_count = (profile.message_count or 0) + 1
            profile.last_seen = datetime.utcnow()

            if interacted_with_nanette:
                profile.interaction_count = (profile.interaction_count or 0) + 1
                profile.last_interaction = datetime.utcnow()

            session.commit()
            session.refresh(profile)
            return profile

    def add_topic(
        self, user_id: str, topic: str, platform: str = 'telegram'
    ) -> Optional[MemberProfile]:
        """Add a topic to member's discussed topics"""
        with self.db.get_session() as session:
            profile = session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

            if not profile:
                return None

            topics = profile.topics_discussed or []
            if topic not in topics:
                topics.append(topic)
                # Keep only last 50 topics
                profile.topics_discussed = topics[-50:]
                session.commit()
                session.refresh(profile)
            return profile

    def add_interest(
        self, user_id: str, interest: str, platform: str = 'telegram'
    ) -> Optional[MemberProfile]:
        """Add an interest to member's profile"""
        with self.db.get_session() as session:
            profile = session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

            if not profile:
                return None

            interests = profile.interests or []
            if interest not in interests:
                interests.append(interest)
                # Keep only 20 interests
                profile.interests = interests[-20:]
                session.commit()
                session.refresh(profile)
            return profile

    def add_notable_fact(
        self, user_id: str, fact: str, platform: str = 'telegram'
    ) -> Optional[MemberProfile]:
        """Add a notable fact about a member"""
        with self.db.get_session() as session:
            profile = session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

            if not profile:
                return None

            facts = profile.notable_facts or []
            if fact not in facts:
                facts.append(fact)
                # Keep only 10 notable facts
                profile.notable_facts = facts[-10:]
                session.commit()
                session.refresh(profile)
            return profile

    def add_contract_asked(
        self, user_id: str, contract_address: str, platform: str = 'telegram'
    ) -> Optional[MemberProfile]:
        """Record that member asked about a contract"""
        with self.db.get_session() as session:
            profile = session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

            if not profile:
                return None

            contracts = profile.contracts_asked_about or []
            addr = contract_address.lower()
            if addr not in contracts:
                contracts.append(addr)
                # Keep only last 30 contracts
                profile.contracts_asked_about = contracts[-30:]
                session.commit()
                session.refresh(profile)
            return profile

    def update_insights(
        self, user_id: str, platform: str = 'telegram',
        communication_style: Optional[str] = None,
        typical_sentiment: Optional[str] = None,
        expertise_level: Optional[str] = None
    ) -> Optional[MemberProfile]:
        """Update personality insights for a member"""
        with self.db.get_session() as session:
            profile = session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

            if not profile:
                return None

            if communication_style:
                profile.communication_style = communication_style
            if typical_sentiment:
                profile.typical_sentiment = typical_sentiment
            if expertise_level:
                profile.expertise_level = expertise_level

            session.commit()
            session.refresh(profile)
            return profile

    def set_admin_status(
        self, user_id: str, is_admin: bool, platform: str = 'telegram'
    ) -> Optional[MemberProfile]:
        """Update member's admin status"""
        with self.db.get_session() as session:
            profile = session.query(MemberProfile).filter_by(
                user_id=str(user_id),
                platform=platform
            ).first()

            if not profile:
                return None

            profile.is_group_admin = is_admin
            session.commit()
            session.refresh(profile)
            return profile

    def get_active_members(
        self, chat_id: str, limit: int = 50
    ) -> List[MemberProfile]:
        """Get most active members in a chat"""
        with self.db.get_session() as session:
            return session.query(MemberProfile).filter_by(
                chat_id=str(chat_id)
            ).order_by(
                desc(MemberProfile.message_count)
            ).limit(limit).all()

    def get_recent_interactors(
        self, limit: int = 20
    ) -> List[MemberProfile]:
        """Get members who recently interacted with Nanette"""
        with self.db.get_session() as session:
            return session.query(MemberProfile).filter(
                MemberProfile.last_interaction.isnot(None)
            ).order_by(
                desc(MemberProfile.last_interaction)
            ).limit(limit).all()


class ConversationMemoryRepository:
    """
    Repository for ConversationMemory — Nanette's persistent memory.
    Stores all conversations with privacy controls for DM sharing.
    """

    def __init__(self, db: Database):
        self.db = db

    def store_message(
        self, chat_id: str, user_id: str, role: str, content: str,
        username: Optional[str] = None, chat_title: Optional[str] = None,
        message_id: Optional[str] = None, is_private_dm: bool = False,
        is_group: bool = False, has_media: bool = False,
        media_type: Optional[str] = None, platform: str = 'telegram'
    ) -> ConversationMemory:
        """Store a message in Nanette's memory"""
        with self.db.get_session() as session:
            memory = ConversationMemory(
                chat_id=str(chat_id),
                chat_title=chat_title,
                user_id=str(user_id),
                username=username,
                platform=platform,
                message_id=str(message_id) if message_id else None,
                role=role,
                content=content[:10000],  # Limit content length
                is_private_dm=is_private_dm,
                is_group=is_group,
                has_media=has_media,
                media_type=media_type,
                dm_share_permissions=[]
            )
            session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory

    def get_chat_history(
        self, chat_id: str, limit: int = 50
    ) -> List[ConversationMemory]:
        """Get recent conversation history for a specific chat"""
        with self.db.get_session() as session:
            return session.query(ConversationMemory).filter_by(
                chat_id=str(chat_id)
            ).order_by(
                desc(ConversationMemory.created_at)
            ).limit(limit).all()[::-1]  # Reverse to get chronological order

    def get_user_history(
        self, user_id: str, limit: int = 100, include_private: bool = True
    ) -> List[ConversationMemory]:
        """Get all conversation history for a user across all chats"""
        with self.db.get_session() as session:
            query = session.query(ConversationMemory).filter_by(
                user_id=str(user_id)
            )
            if not include_private:
                query = query.filter_by(is_private_dm=False)
            return query.order_by(
                desc(ConversationMemory.created_at)
            ).limit(limit).all()[::-1]

    def get_user_dms(
        self, user_id: str, limit: int = 50
    ) -> List[ConversationMemory]:
        """Get a user's private DM history with Nanette"""
        with self.db.get_session() as session:
            return session.query(ConversationMemory).filter_by(
                user_id=str(user_id),
                is_private_dm=True
            ).order_by(
                desc(ConversationMemory.created_at)
            ).limit(limit).all()[::-1]

    def get_shareable_user_dms(
        self, user_id: str, target_chat_id: str, limit: int = 20
    ) -> List[ConversationMemory]:
        """Get DMs that user has given permission to share in a specific chat"""
        with self.db.get_session() as session:
            # Get all DMs and filter by share permission
            dms = session.query(ConversationMemory).filter_by(
                user_id=str(user_id),
                is_private_dm=True
            ).order_by(
                desc(ConversationMemory.created_at)
            ).limit(limit * 2).all()

            # Filter by permission
            shareable = [
                dm for dm in dms
                if dm.dm_share_permissions and
                   target_chat_id in dm.dm_share_permissions
            ]
            return shareable[:limit][::-1]

    def grant_dm_share_permission(
        self, user_id: str, target_chat_id: str
    ) -> int:
        """Grant permission to share all user's DMs in a specific chat"""
        with self.db.get_session() as session:
            dms = session.query(ConversationMemory).filter_by(
                user_id=str(user_id),
                is_private_dm=True
            ).all()

            count = 0
            for dm in dms:
                permissions = dm.dm_share_permissions or []
                if target_chat_id not in permissions:
                    permissions.append(target_chat_id)
                    dm.dm_share_permissions = permissions
                    count += 1

            session.commit()
            return count

    def revoke_dm_share_permission(
        self, user_id: str, target_chat_id: str
    ) -> int:
        """Revoke permission to share user's DMs in a specific chat"""
        with self.db.get_session() as session:
            dms = session.query(ConversationMemory).filter_by(
                user_id=str(user_id),
                is_private_dm=True
            ).all()

            count = 0
            for dm in dms:
                permissions = dm.dm_share_permissions or []
                if target_chat_id in permissions:
                    permissions.remove(target_chat_id)
                    dm.dm_share_permissions = permissions
                    count += 1

            session.commit()
            return count

    def search_memories(
        self, query: str, chat_id: Optional[str] = None,
        user_id: Optional[str] = None, limit: int = 20
    ) -> List[ConversationMemory]:
        """Search conversation memories by content"""
        with self.db.get_session() as session:
            q = session.query(ConversationMemory).filter(
                ConversationMemory.content.ilike(f'%{query}%')
            )
            if chat_id:
                q = q.filter_by(chat_id=str(chat_id))
            if user_id:
                q = q.filter_by(user_id=str(user_id))

            return q.order_by(
                desc(ConversationMemory.created_at)
            ).limit(limit).all()

    def get_cross_chat_context(
        self, user_id: str, current_chat_id: str, limit: int = 30
    ) -> List[ConversationMemory]:
        """
        Get user's history from other chats (for cross-referencing).
        Only includes group messages - never DMs unless explicitly shared.
        """
        with self.db.get_session() as session:
            # Get group messages from other chats
            other_group_msgs = session.query(ConversationMemory).filter(
                ConversationMemory.user_id == str(user_id),
                ConversationMemory.chat_id != str(current_chat_id),
                ConversationMemory.is_private_dm == False
            ).order_by(
                desc(ConversationMemory.created_at)
            ).limit(limit).all()

            # Get shareable DMs for this chat
            shareable_dms = self.get_shareable_user_dms(
                user_id, current_chat_id, limit=10
            )

            # Combine and sort by date
            all_msgs = other_group_msgs + shareable_dms
            all_msgs.sort(key=lambda m: m.created_at, reverse=True)
            return all_msgs[:limit][::-1]

    def get_recent_group_activity(
        self, chat_id: str, hours: int = 24, limit: int = 100
    ) -> List[ConversationMemory]:
        """Get recent activity in a group for context"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        with self.db.get_session() as session:
            return session.query(ConversationMemory).filter(
                ConversationMemory.chat_id == str(chat_id),
                ConversationMemory.created_at >= cutoff
            ).order_by(
                ConversationMemory.created_at
            ).limit(limit).all()

    def cleanup_old_memories(self, days: int = 90) -> int:
        """Remove memories older than specified days (keep DMs longer)"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        dm_cutoff = datetime.utcnow() - timedelta(days=days * 2)  # Keep DMs 2x longer

        with self.db.get_session() as session:
            # Delete old group messages
            group_deleted = session.query(ConversationMemory).filter(
                ConversationMemory.is_private_dm == False,
                ConversationMemory.created_at < cutoff
            ).delete()

            # Delete very old DMs
            dm_deleted = session.query(ConversationMemory).filter(
                ConversationMemory.is_private_dm == True,
                ConversationMemory.created_at < dm_cutoff
            ).delete()

            session.commit()
            return group_deleted + dm_deleted
