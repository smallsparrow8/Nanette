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
    channel_title: Optional[str] = None  # Group name or None for DMs
    username: Optional[str] = None
    message_id: Optional[str] = None
    is_group: bool = False
    directly_addressed: bool = False
    image_base64: Optional[str] = None
    image_media_type: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    analysis_mode: Optional[str] = None  # 'standard', 'esoteric', 'forensic'


class StoreMessageRequest(BaseModel):
    chat_id: str
    user_id: str
    role: str  # 'user' or 'assistant'
    content: str
    username: Optional[str] = None
    chat_title: Optional[str] = None
    message_id: Optional[str] = None
    is_private_dm: bool = False
    is_group: bool = False
    has_media: bool = False
    media_type: Optional[str] = None
    platform: str = "telegram"


class GrantDMShareRequest(BaseModel):
    user_id: str
    target_chat_id: str


class GetMemoryContextRequest(BaseModel):
    user_id: str
    chat_id: str
    include_dms: bool = False
    limit: int = 50


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
        Nanette's response and whether she chose to respond
    """
    try:
        result = await orchestrator.chat_with_nanette(
            message=request.message or "",
            conversation_history=request.conversation_history,
            username=request.username,
            is_group=request.is_group,
            directly_addressed=request.directly_addressed,
            image_base64=request.image_base64,
            image_media_type=request.image_media_type,
            file_name=request.file_name,
            file_size=request.file_size,
            analysis_mode=request.analysis_mode,
            user_id=request.user_id,
            channel_id=request.channel_id
        )

        # Handle both old (string) and new (dict) return formats
        if isinstance(result, dict):
            return result
        return {"response": result, "should_respond": True}

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


# Memory endpoints for persistent conversation storage
@app.post("/memory/store")
async def store_message(request: StoreMessageRequest):
    """Store a message in Nanette's persistent memory"""
    try:
        memory = orchestrator.store_memory(
            chat_id=request.chat_id,
            user_id=request.user_id,
            role=request.role,
            content=request.content,
            username=request.username,
            chat_title=request.chat_title,
            message_id=request.message_id,
            is_private_dm=request.is_private_dm,
            is_group=request.is_group,
            has_media=request.has_media,
            media_type=request.media_type,
            platform=request.platform
        )
        return {"success": True, "memory_id": memory.id if memory else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/grant-dm-share")
async def grant_dm_share(request: GrantDMShareRequest):
    """Grant permission to share DMs in a specific group"""
    try:
        count = orchestrator.grant_dm_share_permission(
            user_id=request.user_id,
            target_chat_id=request.target_chat_id
        )
        return {"success": True, "messages_updated": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/revoke-dm-share")
async def revoke_dm_share(request: GrantDMShareRequest):
    """Revoke permission to share DMs in a specific group"""
    try:
        count = orchestrator.revoke_dm_share_permission(
            user_id=request.user_id,
            target_chat_id=request.target_chat_id
        )
        return {"success": True, "messages_updated": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/context")
async def get_memory_context(request: GetMemoryContextRequest):
    """Get conversation context for a user in a chat"""
    try:
        context = orchestrator.get_memory_context(
            user_id=request.user_id,
            chat_id=request.chat_id,
            include_dms=request.include_dms,
            limit=request.limit
        )
        return {"success": True, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ImportHistoryRequest(BaseModel):
    source: str = "all"  # "rin", "hoichi", or "all"
    batch_size: int = 100


# Privacy filter patterns to exclude from Pinecone
import re
import threading
PRIVACY_PATTERNS = [
    re.compile(r'shockstar\w*aes', re.IGNORECASE),
    re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),  # emails
    re.compile(r'\b0x[a-fA-F0-9]{64}\b'),  # private keys (64 hex chars)
]

# Track import status
_import_status = {"running": False, "progress": "", "results": None}


def passes_privacy_filter(text: str) -> bool:
    """Return False if text contains sensitive content"""
    for pattern in PRIVACY_PATTERNS:
        if pattern.search(text):
            return False
    return True


def _run_import(source: str, batch_size: int):
    """Background import worker"""
    global _import_status
    from core.nanette.rin_chat_history import get_rin_history
    from core.nanette.hoichi_chat_history import get_hoichi_history

    results = {}
    skipped_privacy = 0

    try:
        # Import RIN
        if source in ("rin", "all"):
            _import_status["progress"] = "Preparing RIN messages..."
            rin = get_rin_history()
            if rin and rin.is_loaded:
                rin_messages = []
                for msg in rin.messages:
                    text = msg.get('text', '')
                    if not text or len(text.strip()) < 5:
                        continue
                    if not passes_privacy_filter(text):
                        skipped_privacy += 1
                        continue
                    rin_messages.append({
                        'id': msg.get('id', ''),
                        'text': text,
                        'chat_id': 'rin_telegram',
                        'username': msg.get('sender', ''),
                        'chat_title': 'RinTinTin Official',
                        'timestamp': msg.get('timestamp', ''),
                    })

                _import_status["progress"] = f"Embedding RIN: {len(rin_messages)} messages..."
                count = orchestrator.vector_memory.bulk_import(
                    rin_messages,
                    batch_size=batch_size,
                    source_label="rin"
                )
                results['rin'] = {'imported': count, 'total_eligible': len(rin_messages)}
            else:
                results['rin'] = {'error': 'RIN history not loaded'}

        # Import HOICHI
        if source in ("hoichi", "all"):
            _import_status["progress"] = "Preparing HOICHI messages..."
            hoichi = get_hoichi_history()
            if hoichi and hoichi.is_loaded:
                hoichi_messages = []
                for msg in hoichi.messages:
                    text = msg.get('text', '')
                    if not text or len(text.strip()) < 5:
                        continue
                    if not passes_privacy_filter(text):
                        skipped_privacy += 1
                        continue
                    hoichi_messages.append({
                        'id': msg.get('id', ''),
                        'text': text,
                        'chat_id': 'hoichi_telegram',
                        'username': msg.get('sender', ''),
                        'chat_title': 'HOICHI Community',
                        'timestamp': msg.get('timestamp', ''),
                    })

                _import_status["progress"] = f"Embedding HOICHI: {len(hoichi_messages)} messages..."
                count = orchestrator.vector_memory.bulk_import(
                    hoichi_messages,
                    batch_size=batch_size,
                    source_label="hoichi"
                )
                results['hoichi'] = {'imported': count, 'total_eligible': len(hoichi_messages)}
            else:
                results['hoichi'] = {'error': 'HOICHI history not loaded'}

        results['skipped_privacy'] = skipped_privacy
        _import_status["results"] = results
        _import_status["progress"] = "Complete!"
        print(f"[Import] Complete: {results}")

    except Exception as e:
        _import_status["progress"] = f"Error: {e}"
        _import_status["results"] = {"error": str(e)}
        print(f"[Import] Error: {e}")
    finally:
        _import_status["running"] = False


@app.post("/import-history")
async def import_history(request: ImportHistoryRequest):
    """
    Bulk import RIN/HOICHI chat history into Pinecone.
    Runs in background. Check /import-status for progress.
    """
    if not orchestrator.vector_memory.is_ready:
        raise HTTPException(status_code=503, detail="Vector memory (Pinecone) not connected")

    if _import_status["running"]:
        return {"status": "already_running", "progress": _import_status["progress"]}

    _import_status["running"] = True
    _import_status["progress"] = "Starting..."
    _import_status["results"] = None

    thread = threading.Thread(
        target=_run_import,
        args=(request.source, request.batch_size),
        daemon=True
    )
    thread.start()

    return {"status": "started", "message": "Import running in background. Check /import-status for progress."}


@app.get("/import-status")
async def import_status():
    """Check the status of a bulk import"""
    return {
        "running": _import_status["running"],
        "progress": _import_status["progress"],
        "results": _import_status["results"],
    }


if __name__ == "__main__":
    # Railway sets PORT env var; use it if available
    port = settings.port if settings.port > 0 else settings.api_port
    print("Starting Nanette API...")
    print(f"Environment: {settings.environment}")
    print(f"Database: {settings.database_url}")
    print(f"Listening on port: {port}")

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
