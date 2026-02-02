"""
Contract Address Interaction Analyzer
Traces transaction flows and builds interaction graphs using NetworkX
"""
import asyncio
from typing import Dict, Any, List, Set, Optional, Tuple
from collections import defaultdict
import networkx as nx
from shared.blockchain.evm_client import EVMClient


# Well-known addresses per chain (partial list — expand as needed)
KNOWN_ADDRESSES = {
    "ethereum": {
        "0x0000000000000000000000000000000000000000": "Null Address",
        "0x000000000000000000000000000000000000dead": "Burn Address",
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
        "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router",
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap Universal Router",
        "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "SushiSwap Router",
        "0xdef1c0ded9bec7f1a1670819833240f027b25eff": "0x Exchange Proxy",
        "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap Universal Router V2",
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
        "0x6b175474e89094c44da98b954eedeac495271d0f": "DAI",
    },
    "bsc": {
        "0x0000000000000000000000000000000000000000": "Null Address",
        "0x000000000000000000000000000000000000dead": "Burn Address",
        "0x10ed43c718714eb63d5aa57b78b54704e256024e": "PancakeSwap Router",
        "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": "WBNB",
    },
    "polygon": {
        "0x0000000000000000000000000000000000000000": "Null Address",
        "0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff": "QuickSwap Router",
        "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270": "WMATIC",
    },
}


class InteractionAnalyzer:
    """Analyzes address interactions and fund flows for a contract"""

    def __init__(self, blockchain: str = "ethereum"):
        self.client = EVMClient(blockchain)
        self.blockchain = blockchain.lower()

    async def analyze_interactions(self, address: str,
                                    max_transactions: int = 200) -> Dict[str, Any]:
        """
        Full interaction analysis: fetch transactions, build graph, detect patterns.

        Args:
            address: Contract or wallet address to analyze
            max_transactions: Maximum transactions to fetch per type

        Returns:
            Complete analysis dict with graph, stats, and insights
        """
        address = address.lower()

        # Fetch all three types of transactions with rate limiting
        normal_txns = await self.client.get_transaction_history(
            address, action="txlist", offset=max_transactions
        )
        await asyncio.sleep(0.3)  # Etherscan rate limit

        internal_txns = await self.client.get_transaction_history(
            address, action="txlistinternal", offset=max_transactions
        )
        await asyncio.sleep(0.3)

        token_txns = await self.client.get_transaction_history(
            address, action="tokentx", offset=max_transactions
        )

        # Combine and build graph
        graph, stats = self._build_graph(address, normal_txns, internal_txns, token_txns)

        # Detect patterns
        patterns = self._detect_patterns(graph, address)

        # Compute top senders and receivers
        top_senders = self._get_top_counterparties(graph, address, direction="in")
        top_receivers = self._get_top_counterparties(graph, address, direction="out")

        # Build risk indicators
        risk_indicators = self._assess_risk(graph, address, patterns, stats)

        # Educational insights
        educational = self._generate_educational_insights(patterns, stats)

        return {
            "address": address,
            "blockchain": self.blockchain,
            "total_transactions": stats["total_transactions"],
            "unique_addresses": stats["unique_addresses"],
            "total_eth_in": stats["total_value_in"],
            "total_eth_out": stats["total_value_out"],
            "top_senders": top_senders,
            "top_receivers": top_receivers,
            "fund_flow_summary": self._build_flow_summary(stats, top_senders, top_receivers),
            "graph_data": graph,
            "notable_patterns": patterns,
            "risk_indicators": risk_indicators,
            "educational_insights": educational,
            "token_transfers": stats.get("token_transfers", 0),
            "internal_transactions": stats.get("internal_count", 0),
        }

    def _build_graph(self, center_address: str,
                     normal_txns: List[Dict],
                     internal_txns: List[Dict],
                     token_txns: List[Dict]) -> Tuple[nx.DiGraph, Dict]:
        """Build a NetworkX directed graph from transaction data"""
        graph = nx.DiGraph()
        center = center_address.lower()

        # Track stats
        total_value_in = 0.0
        total_value_out = 0.0
        edge_data = defaultdict(lambda: {"count": 0, "total_value": 0.0, "types": set()})

        # Process normal transactions
        for tx in normal_txns:
            from_addr = tx.get("from", "").lower()
            to_addr = tx.get("to", "").lower()
            if not from_addr or not to_addr:
                continue

            value_eth = int(tx.get("value", "0")) / 1e18
            edge_key = (from_addr, to_addr)
            edge_data[edge_key]["count"] += 1
            edge_data[edge_key]["total_value"] += value_eth
            edge_data[edge_key]["types"].add("normal")

            if to_addr == center:
                total_value_in += value_eth
            if from_addr == center:
                total_value_out += value_eth

        # Process internal transactions
        internal_count = 0
        for tx in internal_txns:
            from_addr = tx.get("from", "").lower()
            to_addr = tx.get("to", "").lower()
            if not from_addr or not to_addr:
                continue

            value_eth = int(tx.get("value", "0")) / 1e18
            edge_key = (from_addr, to_addr)
            edge_data[edge_key]["count"] += 1
            edge_data[edge_key]["total_value"] += value_eth
            edge_data[edge_key]["types"].add("internal")
            internal_count += 1

        # Process token transfers
        token_transfer_count = 0
        for tx in token_txns:
            from_addr = tx.get("from", "").lower()
            to_addr = tx.get("to", "").lower()
            if not from_addr or not to_addr:
                continue

            edge_key = (from_addr, to_addr)
            edge_data[edge_key]["count"] += 1
            edge_data[edge_key]["types"].add("token")
            token_transfer_count += 1

        # Build graph nodes and edges
        known = KNOWN_ADDRESSES.get(self.blockchain, {})
        all_addresses = set()

        for (from_addr, to_addr), data in edge_data.items():
            all_addresses.add(from_addr)
            all_addresses.add(to_addr)

            graph.add_edge(
                from_addr, to_addr,
                weight=data["count"],
                value=data["total_value"],
                types=list(data["types"]),
            )

        # Label nodes
        for addr in all_addresses:
            label = known.get(addr, known.get(to_checksum_safe(addr), ""))
            is_center = addr == center
            graph.add_node(
                addr,
                label=label or shorten_address(addr),
                full_label=label,
                is_center=is_center,
                is_known=bool(label),
                interaction_count=graph.degree(addr) if addr in graph else 0,
            )

        stats = {
            "total_transactions": len(normal_txns) + len(internal_txns) + len(token_txns),
            "normal_count": len(normal_txns),
            "internal_count": internal_count,
            "token_transfers": token_transfer_count,
            "unique_addresses": len(all_addresses),
            "total_value_in": round(total_value_in, 6),
            "total_value_out": round(total_value_out, 6),
            "edge_count": graph.number_of_edges(),
        }

        return graph, stats

    def _get_top_counterparties(self, graph: nx.DiGraph, center: str,
                                 direction: str = "in", limit: int = 5) -> List[Dict]:
        """Get top addresses by interaction count"""
        counterparties = []
        known = KNOWN_ADDRESSES.get(self.blockchain, {})

        if direction == "in":
            edges = graph.in_edges(center, data=True) if center in graph else []
        else:
            edges = graph.out_edges(center, data=True) if center in graph else []

        for edge in edges:
            if direction == "in":
                addr = edge[0]
            else:
                addr = edge[1]

            data = edge[2]
            label = known.get(addr, known.get(to_checksum_safe(addr), ""))

            counterparties.append({
                "address": addr,
                "label": label or shorten_address(addr),
                "is_known": bool(label),
                "transaction_count": data.get("weight", 0),
                "total_value_eth": round(data.get("value", 0), 6),
                "types": data.get("types", []),
            })

        counterparties.sort(key=lambda x: x["transaction_count"], reverse=True)
        return counterparties[:limit]

    def _detect_patterns(self, graph: nx.DiGraph, center: str) -> List[Dict]:
        """Detect notable patterns in the interaction graph"""
        patterns = []

        if len(graph.nodes) < 2:
            return patterns

        # 1. Circular flows (cycles)
        try:
            cycles = list(nx.simple_cycles(graph))
            short_cycles = [c for c in cycles if 2 <= len(c) <= 5]
            if short_cycles:
                patterns.append({
                    "type": "circular_flow",
                    "severity": "warning",
                    "description": f"Detected {len(short_cycles)} circular fund flow(s). "
                                   f"Funds move in loops between addresses.",
                    "detail": f"Shortest cycle involves {len(min(short_cycles, key=len))} addresses.",
                    "educational": "Circular flows can indicate wash trading — artificially "
                                   "inflating volume by sending funds between controlled wallets. "
                                   "Not always malicious, but worth investigating.",
                })
        except Exception:
            pass  # Cycle detection can be expensive on large graphs

        # 2. High concentration (one address dominates)
        if center in graph:
            in_edges = list(graph.in_edges(center, data=True))
            if in_edges:
                total_in = sum(e[2].get("weight", 0) for e in in_edges)
                max_sender = max(in_edges, key=lambda e: e[2].get("weight", 0))
                max_ratio = max_sender[2].get("weight", 0) / total_in if total_in > 0 else 0

                if max_ratio > 0.5 and total_in > 5:
                    patterns.append({
                        "type": "high_concentration",
                        "severity": "info",
                        "description": f"One address accounts for {max_ratio:.0%} of all "
                                       f"incoming transactions.",
                        "detail": f"Top sender: {shorten_address(max_sender[0])}",
                        "educational": "When a single address dominates the transaction flow, "
                                       "it could be the deployer, a major investor, or a "
                                       "coordinated actor. Check if this aligns with the "
                                       "project's known team wallets.",
                    })

        # 3. DEX interactions
        known = KNOWN_ADDRESSES.get(self.blockchain, {})
        dex_interactions = []
        for node in graph.nodes:
            label = known.get(node, known.get(to_checksum_safe(node), ""))
            if any(dex in label.lower() for dex in ["uniswap", "sushiswap", "pancakeswap",
                                                      "quickswap", "router", "exchange"]):
                dex_interactions.append(label)

        if dex_interactions:
            unique_dexes = list(set(dex_interactions))
            patterns.append({
                "type": "dex_activity",
                "severity": "info",
                "description": f"Interacts with {len(unique_dexes)} DEX(es): "
                               f"{', '.join(unique_dexes[:3])}",
                "detail": "Active trading detected on decentralized exchanges.",
                "educational": "DEX interactions show this contract/address is actively "
                               "traded. Check if the trading volume looks organic or if "
                               "there are suspiciously regular patterns.",
            })

        # 4. Rapid in/out (potential pass-through)
        if center in graph:
            in_count = graph.in_degree(center)
            out_count = graph.out_degree(center)
            if in_count > 3 and out_count > 3:
                ratio = min(in_count, out_count) / max(in_count, out_count)
                if ratio > 0.7:
                    patterns.append({
                        "type": "pass_through",
                        "severity": "warning",
                        "description": "Address shows balanced in/out flow — funds enter "
                                       "and leave at similar rates.",
                        "detail": f"In: {in_count} connections, Out: {out_count} connections",
                        "educational": "A balanced in/out pattern can indicate a mixer, "
                                       "a distribution contract, or a middleman wallet. "
                                       "If it's a token contract, this is often normal "
                                       "(buy/sell activity). For a wallet, look deeper.",
                    })

        # 5. Burn address interactions
        null_addr = "0x0000000000000000000000000000000000000000"
        dead_addr = "0x000000000000000000000000000000000000dead"
        if null_addr in graph.nodes or dead_addr in graph.nodes:
            patterns.append({
                "type": "burn_activity",
                "severity": "info",
                "description": "Tokens have been sent to burn addresses.",
                "detail": "Interactions with null (0x000...0) or dead address detected.",
                "educational": "Burn activity reduces circulating supply. This can be "
                               "bullish for token value if done consistently, but verify "
                               "the burn is real and not just a display trick.",
            })

        return patterns

    def _assess_risk(self, graph: nx.DiGraph, center: str,
                     patterns: List[Dict], stats: Dict) -> List[Dict]:
        """Generate risk indicators from the analysis"""
        risks = []

        # Check for circular flows
        circular = [p for p in patterns if p["type"] == "circular_flow"]
        if circular:
            risks.append({
                "level": "medium",
                "indicator": "Circular fund flows detected",
                "explanation": "Could indicate wash trading or artificial volume inflation.",
            })

        # Check for very few unique addresses
        if stats["unique_addresses"] < 5 and stats["total_transactions"] > 20:
            risks.append({
                "level": "high",
                "indicator": "Low address diversity",
                "explanation": f"Only {stats['unique_addresses']} unique addresses in "
                               f"{stats['total_transactions']} transactions. Activity may "
                               f"be concentrated among insiders.",
            })

        # Check for asymmetric flows
        if stats["total_value_out"] > 0 and stats["total_value_in"] > 0:
            ratio = stats["total_value_out"] / stats["total_value_in"]
            if ratio > 5:
                risks.append({
                    "level": "high",
                    "indicator": "Outflow greatly exceeds inflow",
                    "explanation": "Significantly more value leaving than entering. "
                                   "Could indicate fund extraction.",
                })

        return risks

    def _generate_educational_insights(self, patterns: List[Dict],
                                        stats: Dict) -> List[str]:
        """Generate educational takeaways for beginners"""
        insights = []

        insights.append(
            f"This address has interacted with {stats['unique_addresses']} unique "
            f"addresses across {stats['total_transactions']} transactions."
        )

        if stats.get("token_transfers", 0) > 0:
            insights.append(
                f"There are {stats['token_transfers']} token transfers — this means "
                f"ERC20 tokens are moving through this address, not just ETH."
            )

        if stats.get("internal_count", 0) > 0:
            insights.append(
                f"Internal transactions ({stats['internal_count']}) indicate this "
                f"contract calls other contracts. Smart contracts talking to each "
                f"other is the backbone of DeFi."
            )

        for pattern in patterns:
            if pattern.get("educational"):
                insights.append(pattern["educational"])

        return insights

    def _build_flow_summary(self, stats: Dict,
                             top_senders: List[Dict],
                             top_receivers: List[Dict]) -> str:
        """Build a human-readable fund flow summary"""
        parts = []

        parts.append(f"{stats['total_transactions']} total transactions with "
                     f"{stats['unique_addresses']} unique addresses.")

        if stats["total_value_in"] > 0:
            parts.append(f"Total inflow: {stats['total_value_in']:.4f} ETH")
        if stats["total_value_out"] > 0:
            parts.append(f"Total outflow: {stats['total_value_out']:.4f} ETH")

        if top_senders:
            top = top_senders[0]
            parts.append(f"Top sender: {top['label']} ({top['transaction_count']} txns)")

        if top_receivers:
            top = top_receivers[0]
            parts.append(f"Top receiver: {top['label']} ({top['transaction_count']} txns)")

        return " | ".join(parts)


def shorten_address(address: str) -> str:
    """Shorten an address for display"""
    if len(address) > 10:
        return f"{address[:6]}...{address[-4:]}"
    return address


def to_checksum_safe(address: str) -> str:
    """Try to convert to checksum, return original if fails"""
    try:
        from eth_utils import to_checksum_address
        return to_checksum_address(address)
    except Exception:
        return address
