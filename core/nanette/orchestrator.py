"""
Analysis Orchestrator
Coordinates the complete analysis pipeline
"""
from typing import Dict, Any, Optional
from datetime import datetime

from analyzers.contract_analyzer.evm_analyzer import EVMAnalyzer
from analyzers.contract_analyzer.vulnerability_scanner import VulnerabilityScanner
from analyzers.contract_analyzer.tokenomics_analyzer import TokenomicsAnalyzer
from analyzers.contract_analyzer.safety_scorer import SafetyScorer
from analyzers.contract_analyzer.educational_analyzer import EducationalAnalyzer
from analyzers.contract_analyzer.interaction_analyzer import InteractionAnalyzer
from analyzers.contract_analyzer.creator_analyzer import CreatorAnalyzer
from analyzers.contract_analyzer.graph_renderer import GraphRenderer
from analyzers.social_monitor.channel_analyzer import ChannelAnalyzer
from core.nanette.personality import Nanette
from core.nanette.rintintin_info import get_rintintin_story, get_short_rintintin_info
from core.nanette.rin_chat_history import initialize_rin_history, get_rin_history
from core.nanette.hoichi_chat_history import initialize_hoichi_history, get_hoichi_history
from core.nanette.okinami_chat_history import initialize_okinami_history, get_okinami_history
from core.nanette.sakura_chat_history import initialize_sakura_history, get_sakura_history
from core.nanette.media_processor import MediaProcessor
from core.nanette.vector_memory import VectorMemory
import os
from shared.database import (
    Database, ProjectRepository, ContractAnalysisRepository,
    InteractionAnalysisRepository, CreatorAnalysisRepository,
    ChannelMessageRepository, ServerConfigRepository,
    DetectedClueRepository, MemberProfileRepository,
    ConversationMemoryRepository
)
from shared.config import settings


class AnalysisOrchestrator:
    """Orchestrates complete contract analysis pipeline"""

    # Phrases that tell Nanette to be quiet
    SILENCE_PHRASES = [
        'be quiet', 'shut up', 'stop talking', 'silence', 'hush',
        'quiet down', 'stop responding', 'go away', 'leave us alone',
        'shh', 'shhh', 'shush', 'zip it', 'enough', 'stop it',
        'go to sleep', 'take a break', 'take a nap', 'cool it',
        'pipe down', 'knock it off', 'chill', 'relax nanette',
        'mute', 'stfu', "don't speak", "dont speak", "stop speaking",
    ]

    def __init__(self):
        """Initialize orchestrator with all analyzers"""
        self.nanette = Nanette()
        # Track silenced groups: {channel_id: True}
        self._silenced_groups = {}
        self.vulnerability_scanner = VulnerabilityScanner()
        self.tokenomics_analyzer = TokenomicsAnalyzer()
        self.safety_scorer = SafetyScorer()
        self.educational_analyzer = EducationalAnalyzer()
        self.interaction_analyzer = InteractionAnalyzer()
        self.graph_renderer = GraphRenderer()
        self.channel_analyzer = ChannelAnalyzer()
        self.media_processor = MediaProcessor()

        # Vector memory (Pinecone)
        self.vector_memory = VectorMemory()
        if self.vector_memory.initialize():
            print("Vector memory (Pinecone) connected")
        else:
            print("Vector memory not available (continuing without)")

        # Database
        self.db = Database(settings.database_url)
        self.db.create_tables()
        self.project_repo = ProjectRepository(self.db)
        self.analysis_repo = ContractAnalysisRepository(self.db)
        self.interaction_repo = InteractionAnalysisRepository(self.db)
        self.creator_repo = CreatorAnalysisRepository(self.db)
        self.channel_msg_repo = ChannelMessageRepository(self.db)
        self.config_repo = ServerConfigRepository(self.db)
        self.clue_repo = DetectedClueRepository(self.db)
        self.member_repo = MemberProfileRepository(self.db)
        self.memory_repo = ConversationMemoryRepository(self.db)

        # Initialize RIN chat history knowledge base
        kb_path = os.path.join(os.path.dirname(__file__), 'rin_knowledge_base.json')
        if initialize_rin_history(kb_path):
            print("RIN chat history loaded successfully")
        else:
            print("RIN chat history not available (knowledge base not found)")

        # Initialize HOICHI chat history knowledge base
        hoichi_kb_path = os.path.join(os.path.dirname(__file__), 'hoichi_knowledge_base.json')
        if initialize_hoichi_history(hoichi_kb_path):
            print("HOICHI chat history loaded successfully")
        else:
            print("HOICHI chat history not available (knowledge base not found)")

        # Initialize OKINAMI chat history knowledge base
        okinami_kb_path = os.path.join(os.path.dirname(__file__), 'okinami_knowledge_base.json')
        if initialize_okinami_history(okinami_kb_path):
            print("OKINAMI chat history loaded successfully")
        else:
            print("OKINAMI chat history not available (knowledge base not found)")

        # Initialize Sakura Blossom chat history knowledge base
        sakura_kb_path = os.path.join(os.path.dirname(__file__), 'sakura_knowledge_base.json')
        if initialize_sakura_history(sakura_kb_path):
            print("Sakura Blossom chat history loaded successfully")
        else:
            print("Sakura Blossom chat history not available (knowledge base not found)")

    async def analyze_contract(self, contract_address: str, blockchain: str = "ethereum",
                              save_to_db: bool = True) -> Dict[str, Any]:
        """
        Perform complete contract analysis

        Args:
            contract_address: Contract address to analyze
            blockchain: Blockchain network
            save_to_db: Whether to save results to database

        Returns:
            Complete analysis results with Nanette's response
        """
        start_time = datetime.utcnow()

        try:
            # Step 1: Initialize EVM analyzer
            print(f"Analyzing contract {contract_address} on {blockchain}...")
            evm_analyzer = EVMAnalyzer(blockchain)

            # Step 2: Perform base contract analysis
            base_analysis = await evm_analyzer.analyze_contract(contract_address)

            if 'error' in base_analysis:
                return {
                    'success': False,
                    'error': base_analysis['error'],
                    'contract_address': contract_address,
                    'blockchain': blockchain
                }

            # Step 3: Run advanced vulnerability scan
            if base_analysis.get('source_code'):
                print("Running vulnerability scan...")
                vulnerabilities = self.vulnerability_scanner.scan(
                    base_analysis['source_code'],
                    base_analysis.get('abi')
                )
                base_analysis['vulnerabilities'] = vulnerabilities

            # Step 4: Analyze tokenomics
            if base_analysis.get('source_code'):
                print("Analyzing tokenomics...")
                tokenomics = self.tokenomics_analyzer.analyze(
                    base_analysis['source_code'],
                    base_analysis.get('token_info')
                )
                base_analysis['tokenomics'] = tokenomics

            # Step 5: Calculate safety scores
            print("Calculating safety scores...")
            scores = self.safety_scorer.calculate_score(base_analysis)
            base_analysis['scores'] = scores

            # Step 5.5: Quick creator check (lightweight)
            try:
                print("Checking creator wallet...")
                creator_analyzer = CreatorAnalyzer(blockchain)
                creator_info = await creator_analyzer.get_contract_creator_quick(contract_address)
                if creator_info:
                    base_analysis['creator_info'] = creator_info
            except Exception as e:
                print(f"Creator check failed (non-critical): {e}")

            # Step 6: Get priority issues
            priority_issues = self.safety_scorer.get_priority_issues(base_analysis)
            base_analysis['priority_issues'] = priority_issues

            # Step 6.5: Educational analysis (for learning opportunities)
            if base_analysis.get('source_code'):
                print("Finding learning opportunities...")
                educational_insights = self.educational_analyzer.analyze_for_learning(
                    base_analysis['source_code'],
                    contract_address,
                    base_analysis.get('token_info')
                )
                base_analysis['educational_insights'] = educational_insights

            # Step 7: Generate Nanette's personalized response
            print("Generating Nanette's analysis...")
            nanette_response = await self.nanette.analyze_contract_with_personality(
                base_analysis
            )
            base_analysis['nanette_response'] = nanette_response

            # Step 8: Save to database if requested
            if save_to_db:
                await self._save_analysis(base_analysis)

            # Calculate total analysis time
            end_time = datetime.utcnow()
            base_analysis['total_analysis_time'] = (end_time - start_time).total_seconds()
            base_analysis['success'] = True

            return base_analysis

        except Exception as e:
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'error': str(e),
                'contract_address': contract_address,
                'blockchain': blockchain
            }

    async def quick_check(self, contract_address: str, blockchain: str = "ethereum") -> Dict[str, Any]:
        """
        Perform quick contract check (faster, less detailed)

        Args:
            contract_address: Contract address
            blockchain: Blockchain network

        Returns:
            Quick check results
        """
        evm_analyzer = EVMAnalyzer(blockchain)
        return await evm_analyzer.quick_scan(contract_address)

    async def _save_analysis(self, analysis: Dict[str, Any]):
        """Save analysis results to database"""
        try:
            # Create or get project
            project = self.project_repo.create_or_get(
                contract_address=analysis['contract_address'],
                blockchain=analysis['blockchain'],
                name=analysis.get('contract_name'),
                token_name=analysis.get('token_info', {}).get('name'),
                token_symbol=analysis.get('token_info', {}).get('symbol')
            )

            # Create contract analysis record
            scores = analysis.get('scores', {})
            tokenomics = analysis.get('tokenomics', {})

            self.analysis_repo.create(
                project_id=project.id,
                safety_score=scores.get('overall_score', 0),
                risk_level=scores.get('risk_level', 'unknown'),
                vulnerabilities=analysis.get('vulnerabilities', []),
                code_quality=analysis.get('code_quality', {}),
                tokenomics=tokenomics,
                liquidity_analysis=analysis.get('liquidity', {}),
                code_quality_score=scores.get('code_quality_score'),
                security_score=scores.get('security_score'),
                tokenomics_score=scores.get('tokenomics_score'),
                liquidity_score=scores.get('liquidity_score'),
                contract_verified=analysis.get('is_verified', False),
                compiler_version=analysis.get('compiler_version'),
                optimization_enabled=analysis.get('optimization_enabled'),
                analysis_duration_seconds=analysis.get('analysis_duration_seconds')
            )

            print(f"Analysis saved to database for project {project.id}")

        except Exception as e:
            print(f"Error saving to database: {e}")
            # Don't fail the whole analysis if database save fails
            pass

    async def analyze_interactions(
        self, contract_address: str,
        blockchain: str = "ethereum"
    ) -> Dict[str, Any]:
        """
        Analyze address interactions and generate visual graph.

        Args:
            contract_address: Address to analyze
            blockchain: Blockchain network

        Returns:
            Dict with analysis data, graph image bytes,
            and Nanette's explanation
        """
        import base64

        try:
            # Check cache first
            cached = self.interaction_repo.get_recent(
                contract_address, blockchain, max_age_hours=1
            )
            if cached:
                print("Using cached interaction analysis")

            # Run interaction analysis
            print(f"Analyzing interactions for "
                  f"{contract_address[:10]}... on {blockchain}")
            analysis = await self.interaction_analyzer.analyze_interactions(
                contract_address,
                blockchain=blockchain
            )

            if not analysis.get('success'):
                return {
                    'success': False,
                    'error': analysis.get(
                        'error', 'Interaction analysis failed'
                    ),
                    'contract_address': contract_address,
                    'blockchain': blockchain
                }

            # Render the graph
            print("Rendering interaction graph...")
            graph = analysis.get('graph')
            stats = analysis.get('stats', {})
            patterns = analysis.get('patterns', [])

            graph_bytes = self.graph_renderer.render_interaction_graph(
                graph=graph,
                center_address=contract_address,
                title="Address Interaction Map",
                stats=stats,
                patterns=patterns
            )

            graph_b64 = base64.b64encode(graph_bytes).decode('utf-8')

            # Generate Nanette's explanation
            print("Generating Nanette's explanation...")
            explanation = await self.nanette.explain_interaction_graph(
                analysis
            )

            # Save to database
            try:
                self.interaction_repo.create(
                    contract_address=contract_address,
                    blockchain=blockchain,
                    total_transactions=stats.get(
                        'total_transactions', 0
                    ),
                    unique_addresses=stats.get(
                        'unique_addresses', 0
                    ),
                    total_value_in=stats.get('total_value_in', 0),
                    total_value_out=stats.get('total_value_out', 0),
                    top_senders=analysis.get('top_senders'),
                    top_receivers=analysis.get('top_receivers'),
                    notable_patterns=[
                        p.get('description', '')
                        for p in patterns
                    ],
                    risk_indicators=analysis.get(
                        'risk_indicators'
                    )
                )
            except Exception as e:
                print(f"Error saving interaction analysis: {e}")

            return {
                'success': True,
                'contract_address': contract_address,
                'blockchain': blockchain,
                'stats': stats,
                'top_senders': analysis.get('top_senders', []),
                'top_receivers': analysis.get('top_receivers', []),
                'patterns': patterns,
                'risk_indicators': analysis.get(
                    'risk_indicators', []
                ),
                'graph_image': graph_b64,
                'nanette_explanation': explanation
            }

        except Exception as e:
            print(f"Error in interaction analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'contract_address': contract_address,
                'blockchain': blockchain
            }

    async def chat_with_nanette(self, message: str, conversation_history: Optional[list] = None,
                               username: Optional[str] = None, is_group: bool = False,
                               directly_addressed: bool = False,
                               image_base64: Optional[str] = None, image_media_type: Optional[str] = None,
                               file_name: Optional[str] = None, file_size: Optional[int] = None,
                               analysis_mode: Optional[str] = None,
                               user_id: Optional[str] = None, channel_id: Optional[str] = None):
        """
        Chat with Nanette

        Args:
            message: User message
            conversation_history: Optional conversation history
            username: Optional username of the person messaging
            is_group: Whether this is a group chat message
            directly_addressed: Whether Nanette was directly addressed
            image_base64: Optional base64-encoded image data
            image_media_type: Optional MIME type of the image
            file_name: Optional original filename for context
            file_size: Optional file size in bytes
            analysis_mode: Optional analysis mode ('standard', 'esoteric', 'forensic')
            user_id: Optional user ID for member profile tracking
            channel_id: Optional channel/chat ID

        Returns:
            Dict with response and should_respond flag
        """
        # === SILENCE MODE FOR GROUPS ===
        if is_group and channel_id and message:
            msg_lower = message.lower()

            # Check if someone is telling Nanette to be quiet
            if directly_addressed and any(phrase in msg_lower for phrase in self.SILENCE_PHRASES):
                self._silenced_groups[channel_id] = True
                return {
                    "response": "*lowers her head and rests quietly, ears still perked*",
                    "should_respond": True
                }

            # If group is silenced, only respond if directly addressed by name
            if channel_id in self._silenced_groups:
                if directly_addressed:
                    # Someone said her name — she wakes up
                    del self._silenced_groups[channel_id]
                else:
                    # Stay quiet
                    return {"response": None, "should_respond": False}

        member_context = None

        # Track member profile if we have user_id
        if user_id:
            try:
                # Get or create member profile
                profile = self.member_repo.get_or_create(
                    user_id=user_id,
                    platform='telegram',
                    chat_id=channel_id,
                    username=username
                )

                # Build context summary (Nanette knows but doesn't volunteer)
                if profile:
                    member_context = profile.get_context_summary()

                    # Update activity (will mark interaction after response)
                    self.member_repo.update_activity(
                        user_id=user_id,
                        platform='telegram',
                        message_text=message,
                        interacted_with_nanette=False  # Will update after response
                    )
            except Exception as e:
                print(f"Error tracking member profile: {e}")

        # Get historical context from community chat histories if relevant
        historical_context = None
        rin_history = get_rin_history()
        hoichi_history = get_hoichi_history()
        okinami_history = get_okinami_history()
        sakura_history = get_sakura_history()

        if message:
            msg_lower = message.lower()
            context_parts = []

            # Keywords that might benefit from historical context
            history_keywords = [
                'clue', 'clues', 'mystery', 'hidden', 'history',
                'remember when', 'did anyone', 'who said', 'what happened',
                'old messages', 'past', 'before', 'early days', 'original'
            ]

            # RIN-specific keywords
            rin_keywords = ['rin', 'rintintin', '$rin']

            # HOICHI-specific keywords
            hoichi_keywords = ['hoichi', '$hoichi', 'hoi']

            # OKINAMI-specific keywords
            okinami_keywords = ['okinami', '$okinami', 'oki']

            # Sakura-specific keywords
            sakura_keywords = ['sakura', '$sakura', 'blossom']

            # Extract key terms for search
            search_terms = [w for w in message.split() if len(w) > 3][:3]
            search_query = ' '.join(search_terms) if search_terms else message[:50]

            # Check RIN history
            if rin_history and rin_history.is_loaded:
                if any(kw in msg_lower for kw in rin_keywords) or any(kw in msg_lower for kw in history_keywords):
                    rin_context = rin_history.get_context_for_query(search_query, max_messages=5)
                    if rin_context:
                        context_parts.append(rin_context)

            # Check HOICHI history
            if hoichi_history and hoichi_history.is_loaded:
                if any(kw in msg_lower for kw in hoichi_keywords) or any(kw in msg_lower for kw in history_keywords):
                    hoichi_context = hoichi_history.get_context_for_query(search_query, max_messages=5)
                    if hoichi_context:
                        context_parts.append(hoichi_context)

            # Check OKINAMI history
            if okinami_history and okinami_history.is_loaded:
                if any(kw in msg_lower for kw in okinami_keywords) or any(kw in msg_lower for kw in history_keywords):
                    okinami_context = okinami_history.get_context_for_query(search_query, max_messages=5)
                    if okinami_context:
                        context_parts.append(okinami_context)

            # Check Sakura history
            if sakura_history and sakura_history.is_loaded:
                if any(kw in msg_lower for kw in sakura_keywords) or any(kw in msg_lower for kw in history_keywords):
                    sakura_context = sakura_history.get_context_for_query(search_query, max_messages=5)
                    if sakura_context:
                        context_parts.append(sakura_context)

            # Also search Pinecone vector memory
            if self.vector_memory.is_ready:
                vec_context = self.vector_memory.get_context_for_query(
                    search_query, top_k=5
                )
                if vec_context:
                    context_parts.append(vec_context)

            if context_parts:
                historical_context = "\n\n".join(context_parts)

        # Build conversation context from persistent memory
        conversation_context = None
        if channel_id and user_id:
            try:
                conversation_context = self.build_conversation_context_for_nanette(
                    user_id=user_id,
                    chat_id=channel_id,
                    is_group=is_group
                )
            except Exception as e:
                print(f"Error building conversation context: {e}")

        # Process media (transcribe audio, extract video frames)
        media_transcript = None
        video_frames = []
        if image_base64 and image_media_type:
            try:
                import base64 as b64
                media_bytes = b64.b64decode(image_base64)
                media_result = await self.media_processor.process_media(
                    media_bytes, image_media_type, file_name
                )
                media_transcript = media_result.get('transcript')
                video_frames = media_result.get('frames', [])
            except Exception as e:
                print(f"Error processing media: {e}")

        # If we got a transcript, append it to the message
        enhanced_message = message or ''
        if media_transcript:
            enhanced_message = (
                f"{enhanced_message}\n\n"
                f"[Audio transcript: \"{media_transcript}\"]"
            ).strip()

        # Store user's message in memory
        is_private_dm = not is_group
        store_text = enhanced_message or message
        if user_id and channel_id and store_text:
            try:
                self.store_memory(
                    chat_id=channel_id,
                    user_id=user_id,
                    role='user',
                    content=store_text,
                    username=username,
                    is_private_dm=is_private_dm,
                    is_group=is_group,
                    has_media=bool(image_base64)
                )
                # Also store in vector memory for semantic search
                if self.vector_memory.is_ready:
                    self.vector_memory.store_message(
                        message_id=f"msg_{datetime.utcnow().timestamp()}",
                        text=store_text,
                        chat_id=channel_id,
                        user_id=user_id,
                        username=username,
                        is_group=is_group,
                    )
            except Exception as e:
                print(f"Error storing user message: {e}")

        # If we extracted video frames, use the first as the image
        if video_frames and not any(
            t in (image_media_type or '')
            for t in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        ):
            image_base64 = video_frames[0]
            image_media_type = 'image/jpeg'

        # Call Nanette with all context
        result = await self.nanette.chat(
            enhanced_message, conversation_history,
            username=username, is_group=is_group, directly_addressed=directly_addressed,
            image_base64=image_base64, image_media_type=image_media_type,
            file_name=file_name, file_size=file_size, analysis_mode=analysis_mode,
            member_context=member_context, historical_context=historical_context,
            conversation_context=conversation_context
        )

        # Store Nanette's response in memory
        if result.get('should_respond', True) and result.get('response'):
            if user_id and channel_id:
                try:
                    self.store_memory(
                        chat_id=channel_id,
                        user_id=user_id,
                        role='assistant',
                        content=result['response'],
                        username='Nanette',
                        is_private_dm=is_private_dm,
                        is_group=is_group
                    )
                except Exception as e:
                    print(f"Error storing Nanette response: {e}")

        # If Nanette responded, update interaction count
        if user_id and result.get('should_respond', True):
            try:
                self.member_repo.update_activity(
                    user_id=user_id,
                    platform='telegram',
                    interacted_with_nanette=True
                )
            except Exception as e:
                print(f"Error updating member interaction: {e}")

        return result

    async def process_channel_message(
        self, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an incoming group/channel message.

        Args:
            message_data: Dict with chat_id, chat_title, chat_type,
                message_id, user_id, username, is_admin, text,
                timestamp, platform

        Returns:
            Dict with analysis results and optional Nanette response
        """
        chat_id = str(message_data.get('chat_id', ''))
        platform = message_data.get('platform', 'telegram')

        try:
            # Check if channel analysis is enabled for this chat
            config = self.config_repo.get(chat_id, platform)
            if config and not config.channel_analysis_enabled:
                return {
                    'stored': False,
                    'reason': 'channel_analysis_disabled'
                }

            # Pass clue detection flag from config into message
            if config and config.rin_clue_detection:
                message_data['rin_clue_detection'] = True

            # Run through channel analyzer
            analysis = self.channel_analyzer.process_message(message_data)

            # Store in database
            try:
                self.channel_msg_repo.create(
                    chat_id=chat_id,
                    platform=platform,
                    chat_title=message_data.get('chat_title'),
                    chat_type=message_data.get('chat_type'),
                    message_id=str(message_data.get('message_id', '')),
                    user_id=str(message_data.get('user_id', '')),
                    username=message_data.get('username'),
                    is_admin=message_data.get('is_admin', False),
                    text=message_data.get('text', ''),
                    reply_to_message_id=str(
                        message_data.get('reply_to_message_id', '')
                    ) if message_data.get('reply_to_message_id') else None,
                    is_crypto_relevant=analysis.get(
                        'is_crypto_relevant', False
                    ),
                    detected_topics=analysis.get('detected_topics'),
                    detected_addresses=analysis.get('detected_addresses'),
                    detected_tokens=analysis.get('detected_tokens'),
                )

                # Cleanup old messages periodically
                count = self.channel_msg_repo.count_messages(chat_id)
                if count > settings.channel_max_stored_messages:
                    self.channel_msg_repo.cleanup_old(
                        chat_id,
                        max_messages=settings.channel_max_stored_messages
                    )
            except Exception as e:
                print(f"Error storing channel message: {e}")

            # If analyzer says respond, generate Nanette's response
            nanette_response = None
            if analysis.get('should_respond'):
                clue = analysis.get('clue_detection')
                if clue and clue.get('has_potential_clue'):
                    # Clue-mode response
                    from core.nanette.rin_theme_prompts import (
                        build_clue_response_prompt
                    )
                    themes = list(
                        clue.get('matched_themes', {}).keys()
                    )
                    knowledge_ctx = '\n'.join(
                        m['text']
                        for m in clue.get('knowledge_matches', [])
                    ) or 'No specific lore matches.'
                    prompt = build_clue_response_prompt(
                        message_text=message_data.get('text', ''),
                        clue_type=clue.get('clue_type', 'unknown'),
                        confidence=clue.get('confidence', 0),
                        themes=themes,
                        knowledge_context=knowledge_ctx,
                    )
                else:
                    # Normal crypto-relevant response
                    context = analysis.get('suggested_context', '')
                    prompt = (
                        f"You're in a group chat. Respond naturally "
                        f"to the conversation based on this "
                        f"context:\n\n{context}\n\n"
                        f"Keep it brief (2-3 sentences max). Be "
                        f"helpful about crypto topics. Don't be "
                        f"pushy or over-eager. If a contract address "
                        f"was posted, mention they can use /analyze "
                        f"to check it."
                    )
                nanette_response = await self.nanette.chat(prompt)
                analysis['nanette_response'] = nanette_response

                # Update the stored message with Nanette's response
                try:
                    with self.db.get_session() as session:
                        from shared.database.models import (
                            ChannelMessage as CM
                        )
                        # Query by chat_id and message_id directly to avoid
                        # detached session issues
                        db_msg = session.query(CM).filter_by(
                            chat_id=chat_id,
                            message_id=str(message_data.get('message_id', ''))
                        ).first()
                        if db_msg:
                            db_msg.nanette_responded = True
                            db_msg.nanette_response = nanette_response
                            session.commit()
                except Exception as e:
                    print(f"Error updating response record: {e}")

                # Save clue detection to database if applicable
                clue = analysis.get('clue_detection')
                if clue and clue.get('has_potential_clue'):
                    try:
                        self.clue_repo.create(
                            chat_id=chat_id,
                            platform=platform,
                            message_id=str(
                                message_data.get('message_id', '')
                            ),
                            user_id=str(
                                message_data.get('user_id', '')
                            ),
                            username=message_data.get('username'),
                            message_text=message_data.get('text'),
                            clue_type=clue.get('clue_type'),
                            confidence=clue.get('confidence', 0),
                            thematic_connections=clue.get(
                                'thematic_connections'
                            ),
                            matched_themes=clue.get(
                                'matched_themes'
                            ),
                            scores=clue.get('scores'),
                            nanette_response=nanette_response,
                        )
                    except Exception as e:
                        print(f"Error saving clue: {e}")

            return analysis

        except Exception as e:
            print(f"Error processing channel message: {e}")
            return {
                'stored': False,
                'error': str(e)
            }

    async def trace_creator(
        self, contract_address: str,
        blockchain: str = "ethereum"
    ) -> Dict[str, Any]:
        """
        Trace the creator wallet for a contract and analyze
        deployer history.
        """
        try:
            # Check cache first
            cached = self.creator_repo.get_recent(
                contract_address, blockchain, max_age_hours=6
            )
            if cached:
                print("Using cached creator analysis")
                return {
                    'success': True,
                    'contract_address': contract_address,
                    'blockchain': blockchain,
                    'deployer': {
                        'address': cached.deployer_address,
                        'wallet_age_days': cached.deployer_wallet_age_days,
                        'total_transactions': cached.deployer_total_transactions,
                        'balance_eth': cached.deployer_balance_eth,
                        'funding_source': cached.funding_source or {},
                    },
                    'sibling_contracts': cached.sibling_contracts or [],
                    'creator_trust_score': cached.score_breakdown or {},
                    'red_flags': cached.red_flags or [],
                    'summary': {
                        'total_siblings': cached.total_siblings,
                        'alive_siblings': cached.alive_siblings,
                    },
                    'cached': True,
                }

            # Run full creator analysis
            print(f"Tracing creator for {contract_address[:10]}... on {blockchain}")
            creator_analyzer = CreatorAnalyzer(blockchain)
            analysis = await creator_analyzer.analyze_creator(contract_address)

            if not analysis.get('success'):
                return analysis

            # Generate Nanette's explanation
            print("Generating Nanette's creator analysis explanation...")
            explanation = await self.nanette.explain_creator_trace(analysis)
            analysis['nanette_explanation'] = explanation

            # Save to database
            try:
                score_data = analysis.get('creator_trust_score', {})
                self.creator_repo.create(
                    contract_address=contract_address,
                    blockchain=blockchain,
                    deployer_address=analysis['deployer']['address'],
                    deployer_wallet_age_days=analysis['deployer'].get('wallet_age_days'),
                    deployer_total_transactions=analysis['deployer'].get('total_transactions'),
                    deployer_balance_eth=analysis['deployer'].get('balance_eth'),
                    funding_source=analysis['deployer'].get('funding_source'),
                    sibling_contracts=analysis.get('sibling_contracts'),
                    total_siblings=analysis.get('summary', {}).get('total_siblings', 0),
                    alive_siblings=analysis.get('summary', {}).get('alive_siblings', 0),
                    creator_trust_score=score_data.get('overall_score'),
                    risk_level=score_data.get('risk_level'),
                    score_breakdown=score_data,
                    red_flags=analysis.get('red_flags'),
                )
            except Exception as e:
                print(f"Error saving creator analysis: {e}")

            return analysis

        except Exception as e:
            print(f"Error in creator trace: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'contract_address': contract_address,
                'blockchain': blockchain,
            }

    def get_channel_summary(
        self, chat_id: str
    ) -> Dict[str, Any]:
        """Get summary of recent channel activity."""
        return self.channel_analyzer.get_chat_summary(chat_id)

    def get_greeting(self) -> str:
        """Get Nanette's greeting"""
        return self.nanette.get_greeting()

    def get_help(self) -> str:
        """Get help message"""
        return self.nanette.get_help_message()

    # Memory methods for persistent conversation storage
    def store_memory(
        self, chat_id: str, user_id: str, role: str, content: str,
        username: Optional[str] = None, chat_title: Optional[str] = None,
        message_id: Optional[str] = None, is_private_dm: bool = False,
        is_group: bool = False, has_media: bool = False,
        media_type: Optional[str] = None, platform: str = 'telegram'
    ):
        """Store a message in Nanette's persistent memory"""
        return self.memory_repo.store_message(
            chat_id=chat_id,
            user_id=user_id,
            role=role,
            content=content,
            username=username,
            chat_title=chat_title,
            message_id=message_id,
            is_private_dm=is_private_dm,
            is_group=is_group,
            has_media=has_media,
            media_type=media_type,
            platform=platform
        )

    def grant_dm_share_permission(self, user_id: str, target_chat_id: str) -> int:
        """Grant permission to share user's DMs in a specific chat"""
        return self.memory_repo.grant_dm_share_permission(user_id, target_chat_id)

    def revoke_dm_share_permission(self, user_id: str, target_chat_id: str) -> int:
        """Revoke permission to share user's DMs in a specific chat"""
        return self.memory_repo.revoke_dm_share_permission(user_id, target_chat_id)

    def get_memory_context(
        self, user_id: str, chat_id: str,
        include_dms: bool = False, limit: int = 50
    ) -> Dict[str, Any]:
        """
        Build comprehensive memory context for a user in a chat.
        Includes chat history, cross-group references, and shareable DMs.
        """
        context = {
            'chat_history': [],
            'user_history_other_chats': [],
            'shareable_dms': [],
            'user_stats': {}
        }

        # Get current chat history
        chat_history = self.memory_repo.get_chat_history(chat_id, limit=limit)
        context['chat_history'] = [
            {
                'role': m.role,
                'content': m.content[:500],
                'username': m.username,
                'timestamp': m.created_at.isoformat() if m.created_at else None
            }
            for m in chat_history
        ]

        # Get user's history from other groups (for cross-referencing)
        if user_id:
            cross_chat = self.memory_repo.get_cross_chat_context(
                user_id, chat_id, limit=20
            )
            context['user_history_other_chats'] = [
                {
                    'chat_title': m.chat_title or 'Unknown group',
                    'content': m.content[:300],
                    'timestamp': m.created_at.isoformat() if m.created_at else None
                }
                for m in cross_chat if not m.is_private_dm
            ]

            # Get shareable DMs (only if user has given permission)
            if include_dms:
                shareable = self.memory_repo.get_shareable_user_dms(
                    user_id, chat_id, limit=10
                )
                context['shareable_dms'] = [
                    {
                        'role': m.role,
                        'content': m.content[:300],
                        'timestamp': m.created_at.isoformat() if m.created_at else None
                    }
                    for m in shareable
                ]

        return context

    def build_conversation_context_for_nanette(
        self, user_id: str, chat_id: str, is_group: bool = False
    ) -> str:
        """
        Build formatted context string for Nanette's prompt.
        Respects privacy - only includes shareable content.
        """
        parts = []

        # Get recent chat history (last 20 messages)
        chat_history = self.memory_repo.get_chat_history(chat_id, limit=20)
        if chat_history:
            parts.append("[Recent conversation in this chat:]")
            for m in chat_history[-10:]:
                sender = m.username or 'Someone'
                if m.role == 'assistant':
                    parts.append(f"Nanette: {m.content[:200]}")
                else:
                    parts.append(f"{sender}: {m.content[:200]}")

        # If in a group, check if user has shared DM content
        if is_group and user_id:
            shareable_dms = self.memory_repo.get_shareable_user_dms(
                user_id, chat_id, limit=5
            )
            if shareable_dms:
                parts.append("\n[From your private conversations with this user that they've shared:]")
                for m in shareable_dms:
                    if m.role == 'user':
                        parts.append(f"They told you: {m.content[:200]}")

        # Get cross-group context
        if user_id and is_group:
            cross_chat = self.memory_repo.get_cross_chat_context(
                user_id, chat_id, limit=10
            )
            other_groups = [m for m in cross_chat if not m.is_private_dm and m.chat_title]
            if other_groups:
                parts.append("\n[This user has also said in other groups:]")
                for m in other_groups[:5]:
                    parts.append(f"In {m.chat_title}: {m.content[:150]}")

        return "\n".join(parts) if parts else ""
