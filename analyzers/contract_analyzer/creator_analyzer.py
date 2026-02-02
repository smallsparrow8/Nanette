"""
Creator Wallet Analyzer
Traces contract deployers and analyzes their history to detect
serial rug pullers, suspicious funding, and trustworthiness.
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from shared.blockchain.evm_client import EVMClient


# Known mixer / privacy protocol addresses per chain
KNOWN_MIXER_ADDRESSES = {
    "ethereum": {
        "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": "Tornado Cash 0.1 ETH",
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": "Tornado Cash 1 ETH",
        "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": "Tornado Cash 10 ETH",
        "0xa160cdab225685da1d56aa342ad8841c3b53f291": "Tornado Cash 100 ETH",
        "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": "Tornado Cash Router",
        "0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3": "Tornado Cash 100 ETH (old)",
    },
    "bsc": {
        "0x84443cfd09a48af6ef360c6976c5392ac5023a1f": "Tornado Cash BSC",
    },
}

# Uniswap V2 removeLiquidity function signatures
REMOVE_LIQUIDITY_SIGS = {
    "0xbaa2abde",  # removeLiquidity
    "0x02751cec",  # removeLiquidityETH
    "0xaf2979eb",  # removeLiquidityETHSupportingFeeOnTransferTokens
    "0x5b0d5984",  # removeLiquidityETHWithPermit
    "0xded9382a",  # removeLiquidityETHWithPermitSupportingFeeOnTransferTokens
    "0x2195995c",  # removeLiquidityWithPermit
}

# Max siblings to deep-analyze (rate limit budget)
MAX_SIBLING_DEEP_CHECK = 10


class CreatorAnalyzer:
    """Traces contract deployer wallet and analyzes creator history"""

    def __init__(self, blockchain: str = "ethereum"):
        self.client = EVMClient(blockchain)
        self.blockchain = blockchain.lower()

    async def analyze_creator(self, contract_address: str) -> Dict[str, Any]:
        """
        Full creator trace: find deployer, enumerate sibling contracts,
        assess deployer behavior, calculate Creator Trust Score.
        """
        result = {
            'success': False,
            'contract_address': contract_address,
            'blockchain': self.blockchain,
        }

        # Step 1: Find the deployer
        print(f"  [trace] Looking up deployer for {contract_address[:10]}...")
        creator_info = await self._get_contract_creator(contract_address)
        if not creator_info:
            result['error'] = 'Could not find contract creator. The contract may predate explorer tracking.'
            return result

        deployer_address = creator_info['deployer']
        print(f"  [trace] Deployer: {deployer_address[:10]}...")
        await asyncio.sleep(0.3)

        # Step 2: Check if deployer is a contract (factory pattern)
        deployer_code = await self.client.get_contract_code(deployer_address)
        is_factory = len(deployer_code) > 2  # "0x" means no code

        if is_factory:
            # Try to trace one level up
            print(f"  [trace] Deployer is a contract (factory). Tracing factory creator...")
            factory_creator = await self._get_contract_creator(deployer_address)
            await asyncio.sleep(0.3)
            if factory_creator and factory_creator['deployer']:
                factory_deployer = factory_creator['deployer']
                factory_code = await self.client.get_contract_code(factory_deployer)
                if len(factory_code) <= 2:
                    # Factory was deployed by an EOA — use that instead
                    deployer_address = factory_deployer
                    is_factory = False
                    print(f"  [trace] Factory deployed by EOA: {deployer_address[:10]}...")

        # Step 3: Profile the deployer
        print(f"  [trace] Building deployer profile...")
        deployer_profile = await self._get_deployer_profile(deployer_address)
        deployer_profile['is_factory'] = is_factory
        deployer_profile['address'] = deployer_address
        deployer_profile['creation_tx_hash'] = creator_info['creation_tx_hash']
        await asyncio.sleep(0.3)

        # Step 4: Find sibling contracts
        print(f"  [trace] Searching for other contracts by this deployer...")
        siblings = await self._find_sibling_contracts(
            deployer_address, exclude_address=contract_address
        )
        print(f"  [trace] Found {len(siblings)} sibling contracts")

        # Step 5: Deep-check siblings (capped)
        checked_siblings = []
        for i, sibling in enumerate(siblings[:MAX_SIBLING_DEEP_CHECK]):
            print(f"  [trace] Checking sibling {i+1}/{min(len(siblings), MAX_SIBLING_DEEP_CHECK)}...")
            health = await self._check_sibling_health(sibling['address'])
            sibling.update(health)
            checked_siblings.append(sibling)
            await asyncio.sleep(0.3)

        # Step 6: Detect funding red flags
        print(f"  [trace] Checking funding sources...")
        red_flags = await self._detect_funding_source_red_flags(deployer_address)

        # Step 7: Calculate Creator Trust Score
        print(f"  [trace] Calculating Creator Trust Score...")
        trust_score = self._calculate_creator_trust_score(
            deployer_profile, checked_siblings, red_flags
        )

        # Build summary
        alive_count = sum(1 for s in checked_siblings if s.get('is_alive', False))
        active_count = sum(1 for s in checked_siblings if s.get('is_active', False))
        lifespans = [s.get('lifespan_days', 0) for s in checked_siblings if s.get('lifespan_days')]
        avg_lifespan = sum(lifespans) / len(lifespans) if lifespans else 0

        result.update({
            'success': True,
            'deployer': deployer_profile,
            'sibling_contracts': checked_siblings,
            'red_flags': red_flags,
            'creator_trust_score': trust_score,
            'summary': {
                'total_siblings': len(siblings),
                'checked_siblings': len(checked_siblings),
                'alive_siblings': alive_count,
                'active_siblings': active_count,
                'dead_siblings': len(checked_siblings) - alive_count,
                'avg_sibling_lifespan_days': round(avg_lifespan, 1),
                'deployer_is_serial': len(siblings) > 5,
                'deployer_is_factory': is_factory,
            },
        })

        return result

    async def get_contract_creator_quick(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Lightweight creator check for /analyze integration.
        Only fetches deployer address and wallet age.
        """
        creator_info = await self._get_contract_creator(contract_address)
        if not creator_info:
            return None

        deployer = creator_info['deployer']
        await asyncio.sleep(0.3)

        # Get wallet age from first transaction
        first_txs = await self.client.get_first_transactions(deployer, limit=1)
        wallet_age_days = 0
        if first_txs:
            first_ts = int(first_txs[0].get('timeStamp', 0))
            if first_ts:
                age_seconds = time.time() - first_ts
                wallet_age_days = int(age_seconds / 86400)

        await asyncio.sleep(0.3)

        # Get tx count to estimate contract count
        tx_count = await self.client.get_transaction_count(deployer)

        return {
            'deployer_address': deployer,
            'wallet_age_days': wallet_age_days,
            'transaction_count': tx_count,
            'is_new_wallet': wallet_age_days < 7,
        }

    async def _get_contract_creator(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Call Etherscan getcontractcreation API to find deployer."""
        return await self.client.get_contract_creator(contract_address)

    async def _get_deployer_profile(self, deployer_address: str) -> Dict[str, Any]:
        """Build a profile of the deployer wallet."""
        profile: Dict[str, Any] = {
            'address': deployer_address,
            'wallet_age_days': 0,
            'first_tx_timestamp': None,
            'balance_eth': 0.0,
            'total_transactions': 0,
        }

        # Get first transactions (ascending) for age
        first_txs = await self.client.get_first_transactions(deployer_address, limit=3)
        if first_txs:
            first_ts = int(first_txs[0].get('timeStamp', 0))
            if first_ts:
                profile['first_tx_timestamp'] = datetime.fromtimestamp(
                    first_ts, tz=timezone.utc
                ).isoformat()
                age_seconds = time.time() - first_ts
                profile['wallet_age_days'] = int(age_seconds / 86400)

            # Funding source: who sent the first incoming transaction?
            for tx in first_txs:
                if tx.get('to', '').lower() == deployer_address.lower() and int(tx.get('value', 0)) > 0:
                    funding_addr = tx.get('from', '')
                    mixers = KNOWN_MIXER_ADDRESSES.get(self.blockchain, {})
                    label = mixers.get(funding_addr.lower(), 'Unknown')
                    is_mixer = funding_addr.lower() in mixers
                    profile['funding_source'] = {
                        'address': funding_addr,
                        'label': label,
                        'is_mixer': is_mixer,
                    }
                    break

        if 'funding_source' not in profile:
            profile['funding_source'] = {
                'address': 'Unknown',
                'label': 'Unknown',
                'is_mixer': False,
            }

        await asyncio.sleep(0.3)

        # Balance (via web3 RPC — free, no rate limit)
        balance_wei = await self.client.get_balance(deployer_address)
        profile['balance_eth'] = round(balance_wei / 1e18, 6)

        # Transaction count (via web3 RPC)
        profile['total_transactions'] = await self.client.get_transaction_count(deployer_address)

        return profile

    async def _find_sibling_contracts(self, deployer_address: str,
                                      exclude_address: str = "") -> List[Dict[str, Any]]:
        """
        Find all contracts deployed by the same wallet.
        Contract creation transactions have an empty 'to' field.
        """
        siblings = []
        exclude_lower = exclude_address.lower()

        # Fetch transaction history (descending — most recent first)
        txs = await self.client.get_transaction_history(
            deployer_address, action='txlist', page=1, offset=10000
        )

        for tx in txs:
            # Contract creation: 'to' is empty and contractAddress is present
            if tx.get('to', '') == '' and tx.get('contractAddress', ''):
                contract_addr = tx['contractAddress']
                if contract_addr.lower() == exclude_lower:
                    continue

                creation_ts = int(tx.get('timeStamp', 0))
                creation_date = None
                if creation_ts:
                    creation_date = datetime.fromtimestamp(
                        creation_ts, tz=timezone.utc
                    ).isoformat()

                siblings.append({
                    'address': contract_addr,
                    'creation_timestamp': creation_date,
                    'creation_ts': creation_ts,
                    'tx_hash': tx.get('hash', ''),
                })

        return siblings

    async def _check_sibling_health(self, sibling_address: str) -> Dict[str, Any]:
        """
        Check if a sibling contract is alive, active, and whether
        liquidity was removed.
        """
        health: Dict[str, Any] = {
            'is_alive': False,
            'is_active': False,
            'lifespan_days': 0,
            'token_name': None,
            'token_symbol': None,
            'had_liquidity_removal': False,
        }

        # Check bytecode (via web3 RPC — free)
        code = await self.client.get_contract_code(sibling_address)
        health['is_alive'] = len(code) > 2

        # Try to get token info (via web3 RPC — free)
        token_info = await self.client.get_token_info(sibling_address)
        if token_info:
            health['token_name'] = token_info.get('name')
            health['token_symbol'] = token_info.get('symbol')

        # Check last transaction (1 Etherscan call)
        recent_txs = await self.client.get_transaction_history(
            sibling_address, action='txlist', page=1, offset=5
        )

        if recent_txs:
            last_ts = int(recent_txs[0].get('timeStamp', 0))
            if last_ts:
                age_seconds = time.time() - last_ts
                health['is_active'] = age_seconds < (30 * 86400)  # active in last 30 days
                health['last_tx_timestamp'] = datetime.fromtimestamp(
                    last_ts, tz=timezone.utc
                ).isoformat()

            # Check for liquidity removal in recent transactions
            for tx in recent_txs:
                input_data = tx.get('input', '')
                if len(input_data) >= 10:
                    sig = input_data[:10].lower()
                    if sig in REMOVE_LIQUIDITY_SIGS:
                        health['had_liquidity_removal'] = True
                        break

        # Calculate lifespan from creation to last tx (or now)
        # We don't have creation_ts here, so lifespan will be set by caller
        # based on sibling's creation_timestamp

        return health

    async def _detect_funding_source_red_flags(self, deployer_address: str) -> List[Dict[str, Any]]:
        """Check funding sources for red flags."""
        red_flags = []
        mixers = KNOWN_MIXER_ADDRESSES.get(self.blockchain, {})

        # Get earliest transactions
        first_txs = await self.client.get_first_transactions(deployer_address, limit=10)

        if not first_txs:
            red_flags.append({
                'type': 'no_history',
                'severity': 'high',
                'description': 'Deployer wallet has no transaction history',
            })
            return red_flags

        # Check wallet age
        first_ts = int(first_txs[0].get('timeStamp', 0))
        if first_ts:
            age_days = (time.time() - first_ts) / 86400
            if age_days < 1:
                red_flags.append({
                    'type': 'brand_new_wallet',
                    'severity': 'critical',
                    'description': 'Deployer wallet was created less than 24 hours before deployment',
                })
            elif age_days < 7:
                red_flags.append({
                    'type': 'very_new_wallet',
                    'severity': 'high',
                    'description': f'Deployer wallet is only {int(age_days)} days old',
                })

        # Check funding sources for mixer involvement
        for tx in first_txs:
            sender = tx.get('from', '').lower()
            if sender in mixers:
                red_flags.append({
                    'type': 'mixer_funding',
                    'severity': 'critical',
                    'description': f'Deployer funded by {mixers[sender]}',
                })
                break

        return red_flags

    def _calculate_creator_trust_score(self, deployer: Dict[str, Any],
                                       siblings: List[Dict[str, Any]],
                                       red_flags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Creator Trust Score (0-100).

        Components:
        - Wallet Maturity:       /20
        - Deployment History:    /30
        - Sibling Survival Rate: /25
        - Funding Transparency:  /15
        - Behavioral Patterns:   /10
        """

        # --- Wallet Maturity (0-20) ---
        age_days = deployer.get('wallet_age_days', 0)
        if age_days > 365:
            maturity = 20
        elif age_days > 180:
            maturity = 15
        elif age_days > 30:
            maturity = 10
        elif age_days > 7:
            maturity = 5
        else:
            maturity = 0

        # --- Deployment History (0-30) ---
        history = 30
        dead_count = sum(1 for s in siblings if not s.get('is_alive', False))
        history -= min(15, dead_count * 3)  # -3 per dead sibling, max -15

        if len(siblings) > 5:
            # Check if many were deployed recently (serial deployer)
            recent_siblings = sum(
                1 for s in siblings
                if s.get('creation_ts', 0) > time.time() - (30 * 86400)
            )
            if recent_siblings > 5:
                history -= 5

        # Short average lifespan
        lifespans = [s.get('lifespan_days', 0) for s in siblings if s.get('lifespan_days')]
        if lifespans and sum(lifespans) / len(lifespans) < 7:
            history -= 5

        # Bonus for long-lived siblings
        long_lived = sum(1 for s in siblings if s.get('is_alive') and s.get('lifespan_days', 0) > 180)
        if long_lived > 0:
            history = min(30, history + 5)

        history = max(0, history)

        # --- Sibling Survival Rate (0-25) ---
        if len(siblings) == 0:
            survival = 15  # Neutral — no siblings to judge
        else:
            alive_count = sum(1 for s in siblings if s.get('is_alive', False))
            survival = round((alive_count / len(siblings)) * 25)

            # Deduct for liquidity removals
            lp_removals = sum(1 for s in siblings if s.get('had_liquidity_removal', False))
            survival -= min(15, lp_removals * 5)
            survival = max(0, survival)

        # --- Funding Transparency (0-15) ---
        transparency = 15
        for flag in red_flags:
            if flag['type'] == 'mixer_funding':
                transparency -= 15
            elif flag['type'] == 'brand_new_wallet':
                transparency -= 10
            elif flag['type'] == 'very_new_wallet':
                transparency -= 5
            elif flag['type'] == 'no_history':
                transparency -= 10
        transparency = max(0, transparency)

        # --- Behavioral Patterns (0-10) ---
        behavior = 10
        # Deploy-drain pattern: siblings with LP removal AND short lifespan
        drain_count = sum(
            1 for s in siblings
            if s.get('had_liquidity_removal') and s.get('lifespan_days', 999) < 14
        )
        if drain_count > 0:
            behavior -= min(5, drain_count * 2)

        # Rapid deployment pattern
        if len(siblings) >= 3:
            timestamps = sorted([s.get('creation_ts', 0) for s in siblings if s.get('creation_ts')])
            rapid_deploys = 0
            for i in range(1, len(timestamps)):
                if timestamps[i] - timestamps[i-1] < 86400:  # < 24h apart
                    rapid_deploys += 1
            if rapid_deploys >= 3:
                behavior -= 5

        behavior = max(0, behavior)

        # Total
        total = maturity + history + survival + transparency + behavior
        total = max(0, min(100, total))

        # Risk level
        if total >= 85:
            risk_level = 'very_low'
        elif total >= 70:
            risk_level = 'low'
        elif total >= 50:
            risk_level = 'medium'
        elif total >= 30:
            risk_level = 'high'
        else:
            risk_level = 'critical'

        # Generate recommendation
        if risk_level in ('very_low', 'low'):
            recommendation = (
                'Creator wallet has a reasonable track record. '
                'Always verify the contract code independently.'
            )
        elif risk_level == 'medium':
            recommendation = (
                'Creator history shows some mixed signals. '
                'Proceed with caution and do thorough research.'
            )
        elif risk_level == 'high':
            recommendation = (
                'Multiple warning signs in the creator\'s history. '
                'High risk of rug pull. Exercise extreme caution.'
            )
        else:
            recommendation = (
                'Creator wallet has serious red flags. '
                'This has the hallmarks of a scam. Stay away.'
            )

        return {
            'overall_score': total,
            'risk_level': risk_level,
            'wallet_maturity_score': maturity,
            'deployment_history_score': history,
            'sibling_survival_score': survival,
            'funding_transparency_score': transparency,
            'behavioral_patterns_score': behavior,
            'recommendation': recommendation,
        }
