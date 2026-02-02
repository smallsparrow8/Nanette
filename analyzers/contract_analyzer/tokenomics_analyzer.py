"""
Tokenomics Analyzer
Analyzes token economics, distribution, and fee structures
"""
import re
from typing import Dict, Any, List, Optional


class TokenomicsAnalyzer:
    """Analyzer for token economics and distribution"""

    def __init__(self):
        self.warnings = []
        self.red_flags = []

    def analyze(self, source_code: str, token_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze token economics

        Args:
            source_code: Contract source code
            token_info: Token information (name, symbol, supply, etc.)

        Returns:
            Dict with tokenomics analysis
        """
        result = {
            'total_supply': None,
            'decimals': None,
            'owner_allocation': None,
            'fees': {
                'buy_fee': None,
                'sell_fee': None,
                'transfer_fee': None,
                'is_modifiable': False
            },
            'burn_mechanism': False,
            'mint_mechanism': False,
            'pausable': False,
            'blacklist_mechanism': False,
            'warnings': [],
            'red_flags': [],
            'score': 0  # Out of 20
        }

        self.warnings = []
        self.red_flags = []

        # Extract token info
        if token_info:
            result['total_supply'] = token_info.get('total_supply')
            result['decimals'] = token_info.get('decimals')
            result['owner'] = token_info.get('owner')

        # Analyze fee structure
        result['fees'] = self._analyze_fees(source_code)

        # Check for burn mechanism
        result['burn_mechanism'] = self._check_burn_mechanism(source_code)

        # Check for mint mechanism
        result['mint_mechanism'] = self._check_mint_mechanism(source_code)

        # Check if pausable
        result['pausable'] = self._check_pausable(source_code)

        # Check for blacklist mechanism
        result['blacklist_mechanism'] = self._check_blacklist(source_code)

        # Check for max transaction limits
        result['max_transaction_limit'] = self._check_max_tx_limit(source_code)

        # Check for cooldown mechanisms
        result['cooldown_mechanism'] = self._check_cooldown(source_code)

        # Calculate score
        result['score'] = self._calculate_tokenomics_score(result)

        result['warnings'] = self.warnings
        result['red_flags'] = self.red_flags

        return result

    def _analyze_fees(self, source_code: str) -> Dict[str, Any]:
        """Analyze fee structure"""
        fees = {
            'buy_fee': None,
            'sell_fee': None,
            'transfer_fee': None,
            'is_modifiable': False
        }

        # Look for fee variables
        fee_patterns = [
            r'(\w*[Bb]uy[Ff]ee\w*)\s*=\s*(\d+)',
            r'(\w*[Ss]ell[Ff]ee\w*)\s*=\s*(\d+)',
            r'(\w*[Tt]ransfer[Ff]ee\w*)\s*=\s*(\d+)',
            r'(\w*[Tt]ax\w*)\s*=\s*(\d+)'
        ]

        for pattern in fee_patterns:
            matches = re.finditer(pattern, source_code)
            for match in matches:
                fee_name = match.group(1).lower()
                fee_value = int(match.group(2))

                if 'buy' in fee_name:
                    fees['buy_fee'] = fee_value
                elif 'sell' in fee_name:
                    fees['sell_fee'] = fee_value
                elif 'transfer' in fee_name:
                    fees['transfer_fee'] = fee_value

                # Check if fee is too high (> 10%)
                if fee_value > 1000:  # Assuming basis points (10000 = 100%)
                    self.red_flags.append(f'Excessive {fee_name}: {fee_value/100}%')

        # Check if fees are modifiable
        if re.search(r'function\s+set\w*[Ff]ee', source_code) or \
           re.search(r'function\s+update\w*[Ff]ee', source_code):
            fees['is_modifiable'] = True
            self.warnings.append('Fees can be modified by owner')

        return fees

    def _check_burn_mechanism(self, source_code: str) -> bool:
        """Check if contract has burn mechanism"""
        burn_patterns = [
            r'function\s+burn\s*\(',
            r'_burn\s*\(',
            r'\.burn\s*\(',
        ]

        for pattern in burn_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                return True

        return False

    def _check_mint_mechanism(self, source_code: str) -> bool:
        """Check if contract has mint mechanism"""
        # Look for mint functions
        mint_patterns = [
            r'function\s+mint\s*\(',
            r'_mint\s*\(',
            r'\.mint\s*\(',
        ]

        has_mint = False
        for pattern in mint_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                has_mint = True
                break

        if has_mint:
            # Check if mint has access control
            if not re.search(r'onlyOwner|onlyMinter|onlyRole', source_code):
                self.red_flags.append('Mint function may lack proper access control')
            else:
                self.warnings.append('Contract has mint function (can increase supply)')

        return has_mint

    def _check_pausable(self, source_code: str) -> bool:
        """Check if contract is pausable"""
        pausable_patterns = [
            r'function\s+pause\s*\(',
            r'whenNotPaused',
            r'Pausable'
        ]

        for pattern in pausable_patterns:
            if re.search(pattern, source_code):
                self.warnings.append('Contract can be paused, halting all transfers')
                return True

        return False

    def _check_blacklist(self, source_code: str) -> bool:
        """Check for blacklist mechanism"""
        blacklist_patterns = [
            r'blacklist',
            r'isBlacklisted',
            r'_blacklist',
            r'blocked',
            r'isBlocked'
        ]

        for pattern in blacklist_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                self.red_flags.append('Contract has blacklist mechanism - users can be blocked from trading')
                return True

        return False

    def _check_max_tx_limit(self, source_code: str) -> Optional[bool]:
        """Check for maximum transaction limits"""
        max_tx_patterns = [
            r'maxTx',
            r'maxTransaction',
            r'_maxTxAmount',
            r'maxBuy',
            r'maxSell'
        ]

        has_max_tx = False
        for pattern in max_tx_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                has_max_tx = True
                break

        if has_max_tx:
            # Check if it's modifiable
            if re.search(r'function\s+setMax', source_code, re.IGNORECASE):
                self.warnings.append('Maximum transaction limit can be modified by owner')

            return True

        return False

    def _check_cooldown(self, source_code: str) -> bool:
        """Check for cooldown mechanisms"""
        cooldown_patterns = [
            r'cooldown',
            r'buyCooldown',
            r'sellCooldown',
            r'lastBuy',
            r'lastSell'
        ]

        for pattern in cooldown_patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                self.warnings.append('Contract has cooldown mechanism between trades')
                return True

        return False

    def _calculate_tokenomics_score(self, analysis: Dict[str, Any]) -> int:
        """
        Calculate tokenomics score (out of 20 points)

        Scoring:
        - No excessive fees: 5 points
        - Fees not modifiable: 3 points
        - No blacklist: 4 points
        - No hidden mint: 4 points
        - Reasonable max tx: 2 points
        - No pause mechanism or properly controlled: 2 points
        """
        score = 0

        # Check fees
        fees = analysis.get('fees', {})
        buy_fee = fees.get('buy_fee', 0) or 0
        sell_fee = fees.get('sell_fee', 0) or 0

        # Assuming basis points (10000 = 100%)
        if buy_fee <= 500 and sell_fee <= 500:  # <= 5%
            score += 5
        elif buy_fee <= 1000 and sell_fee <= 1000:  # <= 10%
            score += 3
        elif buy_fee <= 1500 and sell_fee <= 1500:  # <= 15%
            score += 1

        # Fees not modifiable
        if not fees.get('is_modifiable'):
            score += 3
        else:
            score += 1  # Partial credit if modifiable but reasonable

        # No blacklist
        if not analysis.get('blacklist_mechanism'):
            score += 4

        # Mint mechanism check
        if not analysis.get('mint_mechanism'):
            score += 4
        elif 'Mint function may lack proper access control' not in self.red_flags:
            score += 2  # Partial credit if controlled

        # Max transaction limit
        if not analysis.get('max_transaction_limit'):
            score += 2
        elif 'Maximum transaction limit can be modified' not in self.warnings:
            score += 1

        # Pausable
        if not analysis.get('pausable'):
            score += 2

        return min(score, 20)  # Max 20 points
