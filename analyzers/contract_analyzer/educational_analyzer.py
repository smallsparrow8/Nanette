"""
Educational Analyzer
Helps users learn about smart contracts and discover hidden connections
Explains concepts in beginner-friendly language
"""
import re
from typing import Dict, Any, List, Optional


class EducationalAnalyzer:
    """Analyzes contracts for educational insights and learning opportunities"""

    def __init__(self):
        self.learning_points = []
        self.connections = []
        self.beginner_explanations = []

    def analyze_for_learning(self, source_code: str, contract_address: str,
                            token_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze contract for educational value and hidden connections

        Args:
            source_code: Contract source code
            contract_address: Contract address
            token_info: Token information

        Returns:
            Educational insights and connections
        """
        result = {
            'learning_opportunities': [],
            'hidden_connections': [],
            'beginner_explanations': [],
            'implementation_patterns': [],
            'real_world_utility_examples': []
        }

        if not source_code:
            return result

        # Detect learning patterns
        result['learning_opportunities'] = self._find_learning_patterns(source_code)

        # Find connections to other projects/standards
        result['hidden_connections'] = self._discover_connections(source_code)

        # Generate beginner explanations
        result['beginner_explanations'] = self._create_beginner_explanations(source_code)

        # Identify implementation patterns
        result['implementation_patterns'] = self._identify_patterns(source_code)

        # Find real-world utility examples
        result['real_world_utility_examples'] = self._find_utility_examples(source_code)

        return result

    def _find_learning_patterns(self, source_code: str) -> List[Dict[str, Any]]:
        """Find patterns that teach coding concepts"""
        patterns = []

        # OpenZeppelin imports (learning standard patterns)
        if '@openzeppelin/contracts' in source_code or 'OpenZeppelin' in source_code:
            patterns.append({
                'concept': 'Using Industry Standards',
                'explanation': 'This contract uses OpenZeppelin - the gold standard for secure smart contracts. OpenZeppelin provides pre-audited, battle-tested code that you can build upon.',
                'learning_point': 'When building your own contracts, start with OpenZeppelin libraries instead of writing everything from scratch. It\'s safer and teaches you best practices.',
                'beginner_tip': 'Think of OpenZeppelin like using React or Vue.js for web development - it\'s a trusted framework that makes building secure contracts easier.',
                'link': 'https://docs.openzeppelin.com/contracts'
            })

        # Inheritance patterns
        inheritance_matches = re.findall(r'contract\s+\w+\s+is\s+([\w\s,]+)', source_code)
        if inheritance_matches:
            inherited = inheritance_matches[0].split(',')
            patterns.append({
                'concept': 'Contract Inheritance',
                'explanation': f'This contract inherits from {len(inherited)} other contract(s): {", ".join(c.strip() for c in inherited)}',
                'learning_point': 'Inheritance lets you reuse code. Like how a "Car" class might inherit from a "Vehicle" class, contracts can inherit features from other contracts.',
                'beginner_tip': 'Start simple: Create a basic ERC20 token by inheriting from OpenZeppelin\'s ERC20 contract. You get all the standard token functions for free!',
                'code_example': 'contract MyToken is ERC20 { ... }'
            })

        # Events (teaching observability)
        event_count = len(re.findall(r'event\s+\w+', source_code))
        if event_count > 0:
            patterns.append({
                'concept': 'Events for Transparency',
                'explanation': f'Found {event_count} event(s). Events are like console.log() but for blockchain - they let users track what happened.',
                'learning_point': 'Always emit events when important things happen (transfers, approvals, ownership changes). This makes your contract transparent and trackable.',
                'beginner_tip': 'Events are cheap (gas-wise) and essential. Apps like Etherscan use events to show transaction history.',
                'code_example': 'emit Transfer(from, to, amount);'
            })

        # Modifiers (teaching access control)
        modifier_matches = re.findall(r'modifier\s+(\w+)', source_code)
        if modifier_matches:
            patterns.append({
                'concept': 'Modifiers for Access Control',
                'explanation': f'Uses {len(modifier_matches)} modifier(s): {", ".join(modifier_matches[:3])}. Modifiers are like middleware - they run before functions.',
                'learning_point': 'Modifiers let you add checks to functions. onlyOwner is the most common - it prevents anyone except the owner from calling sensitive functions.',
                'beginner_tip': 'Think of modifiers like route guards in web frameworks. They check permissions before allowing code to run.',
                'code_example': 'modifier onlyOwner() { require(msg.sender == owner); _; }'
            })

        # Mapping usage (teaching data structures)
        mapping_count = len(re.findall(r'mapping\s*\(', source_code))
        if mapping_count > 0:
            patterns.append({
                'concept': 'Mappings (Blockchain HashMaps)',
                'explanation': f'Uses {mapping_count} mapping(s) to store data efficiently.',
                'learning_point': 'Mappings are like JavaScript objects or Python dictionaries. They let you look up values by key (like checking a balance by address).',
                'beginner_tip': 'mapping(address => uint256) balances; means "for each address, store a number". Perfect for tracking who owns what!',
                'code_example': 'mapping(address => uint256) public balances;'
            })

        return patterns

    def _discover_connections(self, source_code: str) -> List[Dict[str, Any]]:
        """Discover connections to other projects and standards"""
        connections = []

        # ERC Standards
        erc_patterns = {
            'ERC20': {
                'description': 'Standard token interface',
                'connection': 'All fungible tokens (like $RIN) follow this standard',
                'utility': 'Makes tokens work with all wallets and exchanges',
                'learn_more': 'Study ERC20 to understand how tokens work'
            },
            'ERC721': {
                'description': 'NFT standard',
                'connection': 'Each token is unique (like collectibles)',
                'utility': 'Powers NFT marketplaces like OpenSea',
                'learn_more': 'Learn this to build NFT projects'
            },
            'ERC1155': {
                'description': 'Multi-token standard',
                'connection': 'Mix of fungible and non-fungible tokens',
                'utility': 'Used in gaming (GameFi) for items',
                'learn_more': 'Advanced: combines ERC20 and ERC721'
            }
        }

        for erc, info in erc_patterns.items():
            if erc in source_code:
                connections.append({
                    'type': 'Standard Implementation',
                    'standard': erc,
                    'description': info['description'],
                    'connection': info['connection'],
                    'real_world_utility': info['utility'],
                    'learning_path': info['learn_more'],
                    'beginner_explanation': f'{erc} is a rulebook that all {info["description"]}s follow. Like how all cars have steering wheels and pedals in the same place, all {erc} tokens have the same functions.'
                })

        # Uniswap/DEX connections
        if any(word in source_code for word in ['IUniswapV2Router', 'pancakeswap', 'sushiswap', 'DEX']):
            connections.append({
                'type': 'DeFi Integration',
                'standard': 'Uniswap V2/V3 Router',
                'description': 'Connects to decentralized exchanges',
                'connection': 'This contract can interact with DEXs like Uniswap',
                'real_world_utility': 'Enables trading without centralized exchanges',
                'learning_path': 'Study how DEXs work with Automated Market Makers (AMMs)',
                'beginner_explanation': 'DEX = Decentralized Exchange. Instead of Coinbase (centralized), Uniswap lets people trade directly from their wallets using smart contracts.'
            })

        # Chainlink (oracles)
        if 'chainlink' in source_code.lower() or 'AggregatorV3Interface' in source_code:
            connections.append({
                'type': 'Oracle Integration',
                'standard': 'Chainlink Oracles',
                'description': 'Brings real-world data to blockchain',
                'connection': 'Uses Chainlink to get external data (prices, weather, etc.)',
                'real_world_utility': 'Makes smart contracts react to real-world events',
                'learning_path': 'Learn about oracles - the bridge between blockchain and reality',
                'beginner_explanation': 'Blockchain can\'t access the internet directly. Chainlink is like a messenger that brings real-world data (stock prices, weather) onto the blockchain.'
            })

        # Multisig patterns
        if 'multisig' in source_code.lower() or 'Gnosis' in source_code:
            connections.append({
                'type': 'Security Pattern',
                'standard': 'Multi-Signature Wallet',
                'description': 'Requires multiple approvals',
                'connection': 'Uses multisig for enhanced security',
                'real_world_utility': 'Like requiring 2+ signatures on a check - prevents single point of failure',
                'learning_path': 'Study Gnosis Safe - the standard for multisig',
                'beginner_explanation': 'Like needing 2-of-3 keys to open a safe. One person can\'t act alone, preventing theft or mistakes.'
            })

        return connections

    def _create_beginner_explanations(self, source_code: str) -> List[Dict[str, Any]]:
        """Create beginner-friendly explanations of what the contract does"""
        explanations = []

        # Explain common functions in simple terms
        function_explanations = {
            'transfer': {
                'what_it_does': 'Sends tokens from you to someone else',
                'real_world_analogy': 'Like Venmo or PayPal - "Send $10 to Alice"',
                'when_to_use': 'Moving tokens between wallets',
                'beginner_note': 'Most basic token function. You call this when sending tokens to a friend.'
            },
            'approve': {
                'what_it_does': 'Gives permission to another contract to spend your tokens',
                'real_world_analogy': 'Like giving your credit card to a restaurant - they can charge you',
                'when_to_use': 'Before using DEXs or DeFi apps',
                'beginner_note': 'IMPORTANT: Only approve trusted contracts! This is how many scams work.'
            },
            'mint': {
                'what_it_does': 'Creates new tokens',
                'real_world_analogy': 'Like a mint printing money',
                'when_to_use': 'Creating initial supply or rewards',
                'beginner_note': 'Check who can mint! Only owner? Anyone? This affects token value.'
            },
            'burn': {
                'what_it_does': 'Destroys tokens forever',
                'real_world_analogy': 'Like shredding dollar bills - reduces total supply',
                'when_to_use': 'Deflationary tokenomics',
                'beginner_note': 'Burning reduces supply, potentially increasing value of remaining tokens.'
            }
        }

        for func_name, info in function_explanations.items():
            if f'function {func_name}' in source_code or f'function _{func_name}' in source_code:
                explanations.append({
                    'function': func_name,
                    'simple_explanation': info['what_it_does'],
                    'real_world_analogy': info['real_world_analogy'],
                    'when_to_use': info['when_to_use'],
                    'beginner_note': info['beginner_note']
                })

        return explanations

    def _identify_patterns(self, source_code: str) -> List[Dict[str, Any]]:
        """Identify implementation patterns that can be reused"""
        patterns = []

        # SafeMath pattern
        if 'SafeMath' in source_code:
            patterns.append({
                'pattern': 'SafeMath Library',
                'purpose': 'Prevents overflow/underflow bugs',
                'implementation': 'Using library for safe arithmetic',
                'when_to_use': 'Pre-Solidity 0.8.0 contracts (newer versions have this built-in)',
                'how_to_implement': 'Import OpenZeppelin SafeMath and use .add(), .sub() instead of + and -',
                'beginner_tip': 'If using Solidity 0.8.0+, you don\'t need this - it\'s automatic!'
            })

        # Reentrancy guard
        if 'ReentrancyGuard' in source_code or 'nonReentrant' in source_code:
            patterns.append({
                'pattern': 'Reentrancy Guard',
                'purpose': 'Prevents reentrancy attacks',
                'implementation': 'Using OpenZeppelin ReentrancyGuard',
                'when_to_use': 'Any function that transfers ETH or tokens',
                'how_to_implement': 'Inherit ReentrancyGuard, add nonReentrant modifier to vulnerable functions',
                'beginner_tip': 'This is critical for security! Always use when transferring value.'
            })

        # Pausable pattern
        if 'Pausable' in source_code:
            patterns.append({
                'pattern': 'Pausable Contract',
                'purpose': 'Emergency stop switch',
                'implementation': 'Can pause all transfers if needed',
                'when_to_use': 'When you want ability to freeze contract in emergency',
                'how_to_implement': 'Inherit Pausable, add whenNotPaused modifier',
                'beginner_tip': 'Double-edged sword: Protects users but gives owner control. Use transparently!'
            })

        return patterns

    def _find_utility_examples(self, source_code: str) -> List[Dict[str, Any]]:
        """Find real-world utility examples in the code"""
        utilities = []

        # Auto-liquidity
        if any(word in source_code for word in ['addLiquidity', 'swapAndLiquify']):
            utilities.append({
                'utility': 'Automatic Liquidity Generation',
                'how_it_works': 'Takes a fee from transactions and automatically adds it to liquidity pool',
                'real_world_benefit': 'Makes trading smoother and reduces price impact',
                'implementation_idea': 'Use for any project that wants to improve trading',
                'beginner_explanation': 'Like a vending machine that automatically restocks itself from sales'
            })

        # Reflection/rewards
        if any(word in source_code for word in ['reflect', 'reward', 'dividend']):
            utilities.append({
                'utility': 'Holder Rewards',
                'how_it_works': 'Distributes a portion of each transaction to all holders',
                'real_world_benefit': 'Passive income for holding',
                'implementation_idea': 'Great for community-focused projects',
                'beginner_explanation': 'Like getting dividends from stocks - you earn just by holding'
            })

        # Staking
        if 'stake' in source_code.lower() or 'farming' in source_code.lower():
            utilities.append({
                'utility': 'Staking/Farming',
                'how_it_works': 'Lock tokens to earn rewards',
                'real_world_benefit': 'Earn passive income, reduces circulating supply',
                'implementation_idea': 'Common in DeFi - learn this pattern!',
                'beginner_explanation': 'Like putting money in a savings account - lock it up, earn interest'
            })

        return utilities

    def format_educational_report(self, analysis: Dict[str, Any],
                                 is_rin_contract: bool = False) -> str:
        """Format educational analysis into readable report"""
        report = []

        if is_rin_contract:
            report.append("🎓 **$RIN Educational Analysis - Hidden Learning Opportunities!**\n")
            report.append("Discover what makes $RIN special and learn how to build your own utility!\n")
        else:
            report.append("🎓 **Educational Insights**\n")

        # Learning opportunities
        if analysis.get('learning_opportunities'):
            report.append("\n📚 **What You Can Learn From This Contract:**\n")
            for i, pattern in enumerate(analysis['learning_opportunities'][:5], 1):
                report.append(f"{i}. **{pattern['concept']}**")
                report.append(f"   💡 {pattern['explanation']}")
                report.append(f"   📖 Learning Point: {pattern['learning_point']}")
                report.append(f"   🎯 Beginner Tip: {pattern['beginner_tip']}")
                if 'code_example' in pattern:
                    report.append(f"   ```{pattern['code_example']}```")
                report.append("")

        # Hidden connections
        if analysis.get('hidden_connections'):
            report.append("\n🔗 **Hidden Connections to Other Projects:**\n")
            for conn in analysis['hidden_connections']:
                report.append(f"**{conn['standard']}** - {conn['description']}")
                report.append(f"🔍 Connection: {conn['connection']}")
                report.append(f"🌟 Real-World Utility: {conn['real_world_utility']}")
                report.append(f"📚 Learning Path: {conn['learning_path']}")
                report.append(f"👶 Beginner: {conn['beginner_explanation']}")
                report.append("")

        # Implementation patterns
        if analysis.get('implementation_patterns'):
            report.append("\n🛠️ **Patterns You Can Reuse:**\n")
            for pattern in analysis['implementation_patterns']:
                report.append(f"**{pattern['pattern']}**")
                report.append(f"Purpose: {pattern['purpose']}")
                report.append(f"When to use: {pattern['when_to_use']}")
                report.append(f"How: {pattern['how_to_implement']}")
                report.append(f"💡 {pattern['beginner_tip']}")
                report.append("")

        # Real-world utilities
        if analysis.get('real_world_utility_examples'):
            report.append("\n⚙️ **Real-World Utility Examples:**\n")
            for util in analysis['real_world_utility_examples']:
                report.append(f"**{util['utility']}**")
                report.append(f"How it works: {util['how_it_works']}")
                report.append(f"Benefit: {util['real_world_benefit']}")
                report.append(f"💡 {util['beginner_explanation']}")
                report.append(f"🔧 Your idea: {util['implementation_idea']}")
                report.append("")

        if is_rin_contract:
            report.append("\n🐕 **Nanette's Teaching Note:**")
            report.append("$RIN isn't just a token - it's a learning platform! Each pattern and connection")
            report.append("teaches you how to build REAL UTILITY for your own projects.")
            report.append("\nLike Rin Tin Tin taught audiences through entertainment,")
            report.append("$RIN teaches developers through implementation!")

        return "\n".join(report)
