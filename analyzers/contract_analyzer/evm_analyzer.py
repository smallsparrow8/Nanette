"""
EVM Smart Contract Analyzer
Performs comprehensive security and safety analysis of EVM smart contracts
"""
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from shared.blockchain.evm_client import EVMClient


class EVMAnalyzer:
    """Main analyzer for EVM smart contracts"""

    def __init__(self, blockchain: str = "ethereum"):
        """
        Initialize EVM analyzer

        Args:
            blockchain: Blockchain network (ethereum, bsc, polygon, etc.)
        """
        self.blockchain = blockchain
        self.client = EVMClient(blockchain)

    async def analyze_contract(self, contract_address: str) -> Dict[str, Any]:
        """
        Perform comprehensive contract analysis

        Args:
            contract_address: Contract address to analyze

        Returns:
            Dict containing full analysis results
        """
        start_time = datetime.utcnow()

        # Validate address
        if not self.client.is_valid_address(contract_address):
            return {
                'error': 'Invalid contract address',
                'contract_address': contract_address
            }

        # Initialize result structure
        result = {
            'contract_address': contract_address.lower(),
            'blockchain': self.blockchain,
            'analyzed_at': start_time.isoformat(),
            'is_verified': False,
            'source_code': None,
            'token_info': None,
            'code_quality': {},
            'vulnerabilities': [],
            'warnings': [],
            'info': []
        }

        # Fetch contract source code
        print(f"Fetching contract source code for {contract_address}...")
        source_data = await self.client.get_contract_source_code(contract_address)

        if source_data:
            result['is_verified'] = True
            result['source_code'] = source_data['source_code']
            result['contract_name'] = source_data['contract_name']
            result['compiler_version'] = source_data['compiler_version']
            result['optimization_enabled'] = source_data['optimization_used']
            result['license'] = source_data['license_type']

            # Analyze code quality
            result['code_quality'] = self._analyze_code_quality(source_data)

            # Analyze source code for vulnerabilities
            vulnerabilities = self._analyze_source_code(source_data['source_code'])
            result['vulnerabilities'].extend(vulnerabilities)
        else:
            result['warnings'].append({
                'type': 'unverified_contract',
                'severity': 'high',
                'message': 'Contract source code is not verified on the block explorer'
            })

        # Fetch contract bytecode
        bytecode = await self.client.get_contract_code(contract_address)
        if bytecode and bytecode != "0x":
            result['has_code'] = True
            # Analyze bytecode patterns
            bytecode_issues = self._analyze_bytecode(bytecode)
            result['vulnerabilities'].extend(bytecode_issues)
        else:
            result['has_code'] = False
            result['error'] = 'No contract code found at this address'
            return result

        # Get token information
        print("Fetching token information...")
        token_info = await self.client.get_token_info(contract_address)
        if token_info:
            result['token_info'] = token_info

        # Calculate analysis duration
        end_time = datetime.utcnow()
        result['analysis_duration_seconds'] = (end_time - start_time).total_seconds()

        return result

    def _analyze_code_quality(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code quality metrics

        Args:
            source_data: Contract source data from explorer

        Returns:
            Dict with code quality metrics
        """
        quality = {
            'compiler_version': source_data['compiler_version'],
            'optimization_enabled': source_data['optimization_used'],
            'license': source_data['license_type'],
            'score': 0  # Out of 25
        }

        # Score compiler version (5 points)
        compiler_version = source_data['compiler_version']
        if compiler_version:
            # Extract version number (e.g., "v0.8.19+commit..." -> "0.8.19")
            version_match = re.search(r'v?(\d+\.\d+\.\d+)', compiler_version)
            if version_match:
                version = version_match.group(1)
                major, minor, patch = map(int, version.split('.'))

                # Solidity 0.8+ has built-in overflow checks
                if major == 0 and minor >= 8:
                    quality['score'] += 5
                    quality['modern_compiler'] = True
                elif major == 0 and minor >= 6:
                    quality['score'] += 3
                    quality['modern_compiler'] = False
                else:
                    quality['modern_compiler'] = False

        # Score optimization (5 points)
        if source_data['optimization_used']:
            quality['score'] += 5

        # Score license (5 points)
        if source_data['license_type'] and source_data['license_type'] != 'None':
            quality['score'] += 5

        # Score for having verified source (10 points)
        quality['score'] += 10

        return quality

    def _analyze_source_code(self, source_code: str) -> List[Dict[str, Any]]:
        """
        Analyze source code for common vulnerabilities

        Args:
            source_code: Contract source code

        Returns:
            List of detected vulnerabilities
        """
        vulnerabilities = []

        # Pattern-based vulnerability detection
        patterns = {
            'reentrancy': {
                'pattern': r'\.call\{value:.*?\}\(',
                'severity': 'high',
                'description': 'Potential reentrancy vulnerability: External call before state change'
            },
            'unchecked_send': {
                'pattern': r'\.send\(',
                'severity': 'medium',
                'description': 'Unchecked send: Return value not checked'
            },
            'delegatecall': {
                'pattern': r'\.delegatecall\(',
                'severity': 'high',
                'description': 'Delegatecall to untrusted contract can be dangerous'
            },
            'selfdestruct': {
                'pattern': r'selfdestruct\(',
                'severity': 'medium',
                'description': 'Contract contains selfdestruct function'
            },
            'tx_origin': {
                'pattern': r'tx\.origin',
                'severity': 'medium',
                'description': 'Use of tx.origin for authorization is dangerous'
            }
        }

        for vuln_type, config in patterns.items():
            matches = re.finditer(config['pattern'], source_code, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append({
                    'type': vuln_type,
                    'severity': config['severity'],
                    'description': config['description'],
                    'location': match.start()
                })

        # Check for missing access control
        if 'onlyOwner' not in source_code and 'Ownable' not in source_code:
            if 'function mint' in source_code or 'function burn' in source_code:
                vulnerabilities.append({
                    'type': 'missing_access_control',
                    'severity': 'high',
                    'description': 'Critical functions may lack proper access control'
                })

        # Check for pausable without proper controls
        if 'function pause' in source_code:
            if 'onlyOwner' not in source_code:
                vulnerabilities.append({
                    'type': 'unrestricted_pause',
                    'severity': 'high',
                    'description': 'Pause function may be callable by anyone'
                })

        return vulnerabilities

    def _analyze_bytecode(self, bytecode: str) -> List[Dict[str, Any]]:
        """
        Analyze bytecode for suspicious patterns

        Args:
            bytecode: Contract bytecode

        Returns:
            List of detected issues
        """
        issues = []

        # Check for suspicious opcodes
        # SELFDESTRUCT opcode (0xff)
        if 'ff' in bytecode.lower():
            issues.append({
                'type': 'selfdestruct_opcode',
                'severity': 'medium',
                'description': 'Contract contains SELFDESTRUCT opcode'
            })

        # Check bytecode size
        bytecode_size = len(bytecode) // 2  # Each byte is 2 hex chars
        if bytecode_size > 24576:  # 24KB limit
            issues.append({
                'type': 'large_bytecode',
                'severity': 'low',
                'description': f'Contract bytecode is very large ({bytecode_size} bytes)'
            })

        return issues

    async def quick_scan(self, contract_address: str) -> Dict[str, Any]:
        """
        Perform a quick scan without detailed source code analysis

        Args:
            contract_address: Contract address

        Returns:
            Quick scan results
        """
        result = {
            'contract_address': contract_address.lower(),
            'blockchain': self.blockchain,
            'scan_type': 'quick'
        }

        # Check if address has code
        bytecode = await self.client.get_contract_code(contract_address)
        result['is_contract'] = bytecode and bytecode != "0x"

        # Get token info if it's a token contract
        token_info = await self.client.get_token_info(contract_address)
        if token_info:
            result['is_token'] = True
            result['token_info'] = token_info
        else:
            result['is_token'] = False

        return result
