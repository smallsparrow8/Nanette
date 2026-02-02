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
    ServerConfig, ChannelMessage, DetectedClue
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
