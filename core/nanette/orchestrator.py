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
from shared.database import (
    Database, ProjectRepository, ContractAnalysisRepository,
    InteractionAnalysisRepository, CreatorAnalysisRepository,
    ChannelMessageRepository, ServerConfigRepository,
    DetectedClueRepository, MemberProfileRepository
)
from shared.config import settings


class AnalysisOrchestrator:
    """Orchestrates complete contract analysis pipeline"""

    def __init__(self):
        """Initialize orchestrator with all analyzers"""
        self.nanette = Nanette()
        self.vulnerability_scanner = VulnerabilityScanner()
        self.tokenomics_analyzer = TokenomicsAnalyzer()
        self.safety_scorer = SafetyScorer()
        self.educational_analyzer = EducationalAnalyzer()
        self.interaction_analyzer = InteractionAnalyzer()
        self.graph_renderer = GraphRenderer()
        self.channel_analyzer = ChannelAnalyzer()

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

        # Call Nanette with member context
        result = await self.nanette.chat(
            message, conversation_history,
            username=username, is_group=is_group, directly_addressed=directly_addressed,
            image_base64=image_base64, image_media_type=image_media_type,
            file_name=file_name, file_size=file_size, analysis_mode=analysis_mode,
            member_context=member_context
        )

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
