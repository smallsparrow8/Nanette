"""
Nanette API Service
FastAPI application for contract analysis
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from core.nanette.orchestrator import AnalysisOrchestrator
from shared.config import settings
from shared.database import Database, ServerConfigRepository

# Create FastAPI app
app = FastAPI(
    title="Nanette API",
    description="AI-powered cryptocurrency contract analyzer",
    version="1.0.0"
)

# Add CORS middleware
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = AnalysisOrchestrator()

# Server config repository (shares orchestrator's DB)
config_repo = ServerConfigRepository(orchestrator.db)


# Request/Response models
class AnalyzeRequest(BaseModel):
    contract_address: str
    blockchain: str = "ethereum"
    save_to_db: bool = True


class QuickCheckRequest(BaseModel):
    contract_address: str
    blockchain: str = "ethereum"


class InteractionsRequest(BaseModel):
    contract_address: str
    blockchain: str = "ethereum"


class ConfigGetRequest(BaseModel):
    server_id: str
    platform: str
    user_id: str
    server_name: Optional[str] = None
    owner_id: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    server_id: str
    platform: str
    user_id: str
    action: str  # enable, disable, add_admin, remove_admin, cooldown
    target: str  # feature/category name or user_id for admin ops
    value: Optional[str] = None  # for cooldown seconds


class ConfigCheckRequest(BaseModel):
    server_id: str
    platform: str
    feature: str


class ChannelMessageRequest(BaseModel):
    chat_id: str
    chat_title: Optional[str] = None
    chat_type: Optional[str] = None
    message_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    is_admin: bool = False
    text: str = ""
    reply_to_message_id: Optional[str] = None
    timestamp: Optional[str] = None
    platform: str = "telegram"


class ChannelSummaryRequest(BaseModel):
    chat_id: str


class TraceCreatorRequest(BaseModel):
    contract_address: str
    blockchain: str = "ethereum"


class ChatRequest(BaseModel):
    message: Optional[str] = ""
    conversation_history: Optional[list] = None
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    image_base64: Optional[str] = None
    image_media_type: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    analysis_mode: Optional[str] = None  # 'standard', 'esoteric', 'forensic'


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Nanette API",
        "version": "1.0.0",
        "status": "online",
        "message": "Nanette is watching."
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze_contract(request: AnalyzeRequest):
    """
    Analyze a smart contract

    Args:
        request: Analysis request with contract address and blockchain

    Returns:
        Complete analysis results including Nanette's response
    """
    try:
        result = await orchestrator.analyze_contract(
            contract_address=request.contract_address,
            blockchain=request.blockchain,
            save_to_db=request.save_to_db
        )

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quick-check")
async def quick_check(request: QuickCheckRequest):
    """
    Perform a quick contract check

    Args:
        request: Quick check request

    Returns:
        Quick check results
    """
    try:
        result = await orchestrator.quick_check(
            contract_address=request.contract_address,
            blockchain=request.blockchain
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with Nanette

    Args:
        request: Chat request with message

    Returns:
        Nanette's response
    """
    try:
        response = await orchestrator.chat_with_nanette(
            message=request.message or "",
            conversation_history=request.conversation_history,
            image_base64=request.image_base64,
            image_media_type=request.image_media_type,
            file_name=request.file_name,
            file_size=request.file_size,
            analysis_mode=request.analysis_mode
        )

        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-interactions")
async def analyze_interactions(request: InteractionsRequest):
    """
    Analyze address interactions and generate visual graph.

    Returns:
        Analysis data, base64 graph image, and explanation
    """
    try:
        result = await orchestrator.analyze_interactions(
            contract_address=request.contract_address,
            blockchain=request.blockchain
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Analysis failed')
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/get")
async def get_config(request: ConfigGetRequest):
    """Get server/chat configuration"""
    try:
        config = config_repo.get_or_create(
            server_id=request.server_id,
            platform=request.platform,
            server_name=request.server_name,
            owner_id=request.owner_id
        )
        return {
            "server_id": config.server_id,
            "platform": config.platform,
            "server_name": config.server_name,
            "owner_id": config.owner_id,
            "admin_ids": config.admin_ids or [],
            "allow_chat": config.allow_chat,
            "allow_analysis": config.allow_analysis,
            "allow_interactions": config.allow_interactions,
            "allow_fun": config.allow_fun,
            "allow_crypto_data": config.allow_crypto_data,
            "auto_respond": config.auto_respond,
            "response_cooldown": config.response_cooldown,
            "channel_analysis_enabled": config.channel_analysis_enabled,
            "rin_clue_detection": config.rin_clue_detection,
            "enabled_features": config.enabled_features or {},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/update")
async def update_config(request: ConfigUpdateRequest):
    """Update server/chat configuration (admin only)"""
    try:
        # Check if user is admin
        is_admin = config_repo.is_admin(
            request.server_id, request.platform, request.user_id
        )
        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only server owners and admins can change settings."
            )

        action = request.action.lower()
        target = request.target

        if action == 'enable':
            # Check if target is a category or specific feature
            categories = {
                'analysis', 'interactions', 'chat', 'fun',
                'crypto', 'auto_respond', 'channel_analysis',
                'clues'
            }
            if target in categories:
                result = config_repo.update_category(
                    request.server_id, request.platform,
                    target, True
                )
            else:
                result = config_repo.update_feature(
                    request.server_id, request.platform,
                    target, True
                )

        elif action == 'disable':
            categories = {
                'analysis', 'interactions', 'chat', 'fun',
                'crypto', 'auto_respond', 'channel_analysis',
                'clues'
            }
            if target in categories:
                result = config_repo.update_category(
                    request.server_id, request.platform,
                    target, False
                )
            else:
                result = config_repo.update_feature(
                    request.server_id, request.platform,
                    target, False
                )

        elif action == 'add_admin':
            result = config_repo.add_admin(
                request.server_id, request.platform, target
            )

        elif action == 'remove_admin':
            result = config_repo.remove_admin(
                request.server_id, request.platform, target
            )

        elif action == 'cooldown':
            try:
                seconds = int(request.value or target)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Cooldown must be a number (seconds)"
                )
            result = config_repo.set_cooldown(
                request.server_id, request.platform, seconds
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action: {action}"
            )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Server config not found"
            )

        return {"success": True, "action": action, "target": target}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/check-feature")
async def check_feature(request: ConfigCheckRequest):
    """Check if a feature is enabled for a server/chat"""
    try:
        config = config_repo.get(
            request.server_id, request.platform
        )
        if not config:
            # No config = all features enabled by default
            return {"enabled": True, "feature": request.feature}

        enabled = config.is_feature_enabled(request.feature)
        return {"enabled": enabled, "feature": request.feature}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/channel/message")
async def channel_message(request: ChannelMessageRequest):
    """Process a message from a group/channel"""
    try:
        result = await orchestrator.process_channel_message({
            'chat_id': request.chat_id,
            'chat_title': request.chat_title,
            'chat_type': request.chat_type,
            'message_id': request.message_id,
            'user_id': request.user_id,
            'username': request.username,
            'is_admin': request.is_admin,
            'text': request.text,
            'reply_to_message_id': request.reply_to_message_id,
            'timestamp': request.timestamp,
            'platform': request.platform,
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/channel/summary")
async def channel_summary(request: ChannelSummaryRequest):
    """Get summary of recent activity in a channel"""
    try:
        summary = orchestrator.get_channel_summary(request.chat_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trace-creator")
async def trace_creator(request: TraceCreatorRequest):
    """
    Trace the creator/deployer of a smart contract.

    Returns:
        Creator analysis including deployer profile, sibling contracts,
        trust score, and Nanette's explanation
    """
    try:
        result = await orchestrator.trace_creator(
            contract_address=request.contract_address,
            blockchain=request.blockchain
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Creator trace failed')
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/greet")
async def greet():
    """Get Nanette's greeting"""
    return {"message": orchestrator.get_greeting()}


@app.get("/help")
async def help_message():
    """Get help message"""
    return {"message": orchestrator.get_help()}


if __name__ == "__main__":
    print("Starting Nanette API...")
    print(f"Environment: {settings.environment}")
    print(f"Database: {settings.database_url}")

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
