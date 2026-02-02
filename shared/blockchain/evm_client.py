"""
EVM Blockchain client for interacting with Ethereum-compatible chains
"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from web3 import Web3
from eth_utils import to_checksum_address, is_address
from shared.config import settings


class EVMClient:
    """Client for interacting with EVM-compatible blockchains"""

    def __init__(self, blockchain: str = "ethereum"):
        """
        Initialize EVM client

        Args:
            blockchain: Name of the blockchain (ethereum, bsc, polygon, etc.)
        """
        self.blockchain = blockchain.lower()
        self.rpc_url = settings.get_rpc_url(self.blockchain)
        self.explorer_api_key = settings.get_explorer_api_key(self.blockchain)
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # Explorer API URLs
        self.explorer_urls = {
            'ethereum': 'https://api.etherscan.io/api',
            'eth': 'https://api.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api',
            'polygon': 'https://api.polygonscan.com/api',
            'matic': 'https://api.polygonscan.com/api',
            'arbitrum': 'https://api.arbiscan.io/api',
            'arb': 'https://api.arbiscan.io/api',
            'base': 'https://api.basescan.org/api',
            'optimism': 'https://api-optimistic.etherscan.io/api',
            'op': 'https://api-optimistic.etherscan.io/api',
        }

    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        try:
            return self.w3.is_connected()
        except:
            return False

    def is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address"""
        return is_address(address)

    def to_checksum(self, address: str) -> str:
        """Convert address to checksum format"""
        return to_checksum_address(address)

    async def get_contract_source_code(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetch contract source code from blockchain explorer

        Args:
            contract_address: Contract address

        Returns:
            Dict with source code and metadata, or None if not found
        """
        if not self.explorer_api_key:
            print(f"Warning: No explorer API key configured for {self.blockchain}")
            return None

        explorer_url = self.explorer_urls.get(self.blockchain)
        if not explorer_url:
            return None

        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': contract_address,
            'apikey': self.explorer_api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(explorer_url, params=params) as response:
                    data = await response.json()

                    if data['status'] == '1' and data['result']:
                        result = data['result'][0]

                        # Return None if contract is not verified
                        if result['SourceCode'] == '':
                            return None

                        return {
                            'source_code': result['SourceCode'],
                            'abi': result['ABI'],
                            'contract_name': result['ContractName'],
                            'compiler_version': result['CompilerVersion'],
                            'optimization_used': result['OptimizationUsed'] == '1',
                            'runs': result['Runs'],
                            'constructor_arguments': result['ConstructorArguments'],
                            'evm_version': result.get('EVMVersion', 'Default'),
                            'library': result.get('Library', ''),
                            'license_type': result.get('LicenseType', 'None'),
                            'proxy': result.get('Proxy', '0'),
                            'implementation': result.get('Implementation', ''),
                            'swarm_source': result.get('SwarmSource', '')
                        }
        except Exception as e:
            print(f"Error fetching contract source: {e}")
            return None

    async def get_contract_abi(self, contract_address: str) -> Optional[str]:
        """Get contract ABI"""
        source_data = await self.get_contract_source_code(contract_address)
        if source_data:
            return source_data.get('abi')
        return None

    async def get_contract_code(self, contract_address: str) -> str:
        """Get contract bytecode"""
        try:
            address = self.to_checksum(contract_address)
            code = self.w3.eth.get_code(address)
            return code.hex()
        except Exception as e:
            print(f"Error fetching contract code: {e}")
            return ""

    async def get_token_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token information (name, symbol, decimals, total supply)

        Args:
            contract_address: Token contract address

        Returns:
            Dict with token info or None
        """
        try:
            address = self.to_checksum(contract_address)

            # ERC20 ABI for basic functions
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "owner",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function"
                }
            ]

            contract = self.w3.eth.contract(address=address, abi=erc20_abi)

            token_info = {}

            # Try to get each field, some may not exist
            try:
                token_info['name'] = contract.functions.name().call()
            except:
                token_info['name'] = None

            try:
                token_info['symbol'] = contract.functions.symbol().call()
            except:
                token_info['symbol'] = None

            try:
                token_info['decimals'] = contract.functions.decimals().call()
            except:
                token_info['decimals'] = 18  # Default

            try:
                token_info['total_supply'] = contract.functions.totalSupply().call()
            except:
                token_info['total_supply'] = None

            try:
                token_info['owner'] = contract.functions.owner().call()
            except:
                token_info['owner'] = None

            return token_info

        except Exception as e:
            print(f"Error fetching token info: {e}")
            return None

    async def get_transaction_count(self, address: str) -> int:
        """Get number of transactions for an address"""
        try:
            checksum_address = self.to_checksum(address)
            return self.w3.eth.get_transaction_count(checksum_address)
        except:
            return 0

    async def get_balance(self, address: str) -> int:
        """Get ETH/native token balance"""
        try:
            checksum_address = self.to_checksum(address)
            return self.w3.eth.get_balance(checksum_address)
        except:
            return 0

    async def get_transaction_history(self, address: str, action: str = "txlist",
                                      page: int = 1, offset: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch transaction history from Etherscan-compatible explorer.

        Args:
            address: Contract or wallet address
            action: "txlist" (normal), "txlistinternal" (internal), "tokentx" (ERC20 transfers)
            page: Page number for pagination
            offset: Number of results per page (max 10000)

        Returns:
            List of transaction dicts
        """
        explorer_url = self.explorer_urls.get(self.blockchain)
        if not explorer_url:
            return []

        params = {
            'module': 'account',
            'action': action,
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': page,
            'offset': min(offset, 10000),
            'sort': 'desc',
        }

        if self.explorer_api_key:
            params['apikey'] = self.explorer_api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(explorer_url, params=params) as response:
                    data = await response.json()

                    if data.get('status') == '1' and data.get('result'):
                        return data['result']
                    return []
        except Exception as e:
            print(f"Error fetching transaction history ({action}): {e}")
            return []

    async def get_contract_creator(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Get the creator/deployer of a contract using Etherscan's
        getcontractcreation endpoint.

        Returns:
            Dict with 'deployer' and 'creation_tx_hash', or None
        """
        explorer_url = self.explorer_urls.get(self.blockchain)
        if not explorer_url or not self.explorer_api_key:
            return None

        params = {
            'module': 'contract',
            'action': 'getcontractcreation',
            'contractaddresses': contract_address,
            'apikey': self.explorer_api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(explorer_url, params=params) as response:
                    data = await response.json()
                    if data.get('status') == '1' and data.get('result'):
                        result = data['result'][0]
                        return {
                            'deployer': result.get('contractCreator', ''),
                            'creation_tx_hash': result.get('txHash', ''),
                        }
        except Exception as e:
            print(f"Error fetching contract creator: {e}")

        return None

    async def get_first_transactions(self, address: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch the earliest transactions for an address (ascending order).
        Useful for determining wallet age and initial funding source.
        """
        explorer_url = self.explorer_urls.get(self.blockchain)
        if not explorer_url:
            return []

        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': min(limit, 100),
            'sort': 'asc',
        }

        if self.explorer_api_key:
            params['apikey'] = self.explorer_api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(explorer_url, params=params) as response:
                    data = await response.json()
                    if data.get('status') == '1' and data.get('result'):
                        return data['result']
                    return []
        except Exception as e:
            print(f"Error fetching first transactions: {e}")
            return []

    async def call_contract_function(self, contract_address: str, abi: str,
                                    function_name: str, *args) -> Any:
        """
        Call a contract function

        Args:
            contract_address: Contract address
            abi: Contract ABI
            function_name: Function to call
            *args: Function arguments

        Returns:
            Function result
        """
        try:
            import json
            address = self.to_checksum(contract_address)
            contract = self.w3.eth.contract(address=address, abi=json.loads(abi))
            function = getattr(contract.functions, function_name)
            return function(*args).call()
        except Exception as e:
            print(f"Error calling contract function {function_name}: {e}")
            return None
