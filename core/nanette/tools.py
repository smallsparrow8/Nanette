"""
Nanette's Tools
Tools for accessing web information and blockchain data
"""
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class NanetteTools:
    """Tools that Nanette can use to access information"""

    def __init__(self):
        """Initialize tools"""
        self.session = None

    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web for information

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, snippet, and URL
        """
        try:
            session = await self._get_session()

            # Using DuckDuckGo Instant Answer API (free, no API key needed)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }

            async with session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    return [{"error": f"Search failed with status {response.status}"}]

                data = await response.json()

                results = []

                # Add abstract/definition if available
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading", "Summary"),
                        "snippet": data.get("AbstractText"),
                        "url": data.get("AbstractURL", ""),
                        "source": data.get("AbstractSource", "DuckDuckGo")
                    })

                # Add related topics
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else "Related",
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo"
                        })

                return results[:max_results] if results else [{"info": "No results found"}]

        except asyncio.TimeoutError:
            return [{"error": "Search request timed out"}]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    async def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current cryptocurrency price

        Args:
            symbol: Crypto symbol (e.g., BTC, ETH, RIN)

        Returns:
            Price information
        """
        try:
            session = await self._get_session()

            # Using CoinGecko API (free, no API key needed)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": symbol.lower(),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_market_cap": "true",
                "include_24hr_vol": "true"
            }

            async with session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    return {"error": f"Price lookup failed with status {response.status}"}

                data = await response.json()

                if not data:
                    return {"error": f"Symbol '{symbol}' not found"}

                # Extract data
                symbol_lower = symbol.lower()
                if symbol_lower in data:
                    coin_data = data[symbol_lower]
                    return {
                        "symbol": symbol.upper(),
                        "price_usd": coin_data.get("usd"),
                        "change_24h": coin_data.get("usd_24h_change"),
                        "market_cap": coin_data.get("usd_market_cap"),
                        "volume_24h": coin_data.get("usd_24h_vol"),
                        "timestamp": datetime.now().isoformat()
                    }

                return {"error": f"No data found for '{symbol}'"}

        except asyncio.TimeoutError:
            return {"error": "Price request timed out"}
        except Exception as e:
            return {"error": f"Price lookup failed: {str(e)}"}

    async def get_crypto_info(self, symbol_or_id: str) -> Dict[str, Any]:
        """
        Get detailed cryptocurrency information

        Args:
            symbol_or_id: Crypto symbol or CoinGecko ID

        Returns:
            Detailed crypto information
        """
        try:
            session = await self._get_session()

            # Using CoinGecko API
            coin_id = symbol_or_id.lower()
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "community_data": "true",
                "developer_data": "true"
            }

            async with session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    return {"error": f"Crypto info lookup failed with status {response.status}"}

                data = await response.json()

                return {
                    "name": data.get("name"),
                    "symbol": data.get("symbol", "").upper(),
                    "description": data.get("description", {}).get("en", "")[:500],  # Limit length
                    "market_cap_rank": data.get("market_cap_rank"),
                    "current_price": data.get("market_data", {}).get("current_price", {}).get("usd"),
                    "market_cap": data.get("market_data", {}).get("market_cap", {}).get("usd"),
                    "total_volume": data.get("market_data", {}).get("total_volume", {}).get("usd"),
                    "price_change_24h": data.get("market_data", {}).get("price_change_percentage_24h"),
                    "homepage": data.get("links", {}).get("homepage", [None])[0],
                    "blockchain_site": data.get("links", {}).get("blockchain_site", []),
                    "twitter": data.get("links", {}).get("twitter_screen_name"),
                    "telegram": data.get("links", {}).get("telegram_channel_identifier"),
                    "community_score": data.get("community_score"),
                    "developer_score": data.get("developer_score"),
                }

        except asyncio.TimeoutError:
            return {"error": "Request timed out"}
        except Exception as e:
            return {"error": f"Lookup failed: {str(e)}"}

    async def get_gas_prices(self, blockchain: str = "ethereum") -> Dict[str, Any]:
        """
        Get current gas prices for a blockchain

        Args:
            blockchain: Blockchain name (ethereum, bsc, polygon, etc.)

        Returns:
            Gas price information
        """
        try:
            session = await self._get_session()

            if blockchain.lower() == "ethereum":
                # Using Etherscan gas tracker (no API key needed for this endpoint)
                url = "https://api.etherscan.io/api"
                params = {
                    "module": "gastracker",
                    "action": "gasoracle"
                }

                async with session.get(url, params=params, timeout=10) as response:
                    if response.status != 200:
                        return {"error": f"Gas price lookup failed"}

                    data = await response.json()

                    if data.get("status") == "1" and data.get("result"):
                        result = data["result"]
                        return {
                            "blockchain": "Ethereum",
                            "safe_gas_price": result.get("SafeGasPrice"),
                            "propose_gas_price": result.get("ProposeGasPrice"),
                            "fast_gas_price": result.get("FastGasPrice"),
                            "unit": "Gwei",
                            "timestamp": datetime.now().isoformat()
                        }

            return {"info": f"Gas prices not available for {blockchain}"}

        except Exception as e:
            return {"error": f"Gas price lookup failed: {str(e)}"}

    async def search_crypto_news(self, query: str = "cryptocurrency", max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for cryptocurrency news

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of news articles
        """
        # For now, use web search focused on crypto news
        # In production, use a dedicated crypto news API like CryptoPanic
        news_query = f"{query} cryptocurrency news latest"
        return await self.search_web(news_query, max_results)

    def format_tools_for_claude(self) -> str:
        """
        Format available tools as context for Claude

        Returns:
            String describing available tools
        """
        return """
You have access to the following tools to help answer questions:

1. **search_web(query)**: Search the web for current information
   - Use for: General information, news, current events
   - Example: "search_web('Ethereum 2.0 latest updates')"

2. **get_crypto_price(symbol)**: Get current cryptocurrency price
   - Use for: Price queries, market data
   - Example: "get_crypto_price('ethereum')"

3. **get_crypto_info(symbol)**: Get detailed crypto information
   - Use for: Project details, descriptions, links
   - Example: "get_crypto_info('bitcoin')"

4. **get_gas_prices(blockchain)**: Get current gas prices
   - Use for: Transaction cost information
   - Example: "get_gas_prices('ethereum')"

5. **search_crypto_news(query)**: Search for crypto news
   - Use for: Latest news and updates
   - Example: "search_crypto_news('DeFi')"

When you need to use a tool, describe what you want to search for or look up, and I'll fetch that information for you.
"""

    async def execute_tool_request(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool request

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments

        Returns:
            Tool execution result
        """
        tools_map = {
            "search_web": self.search_web,
            "get_crypto_price": self.get_crypto_price,
            "get_crypto_info": self.get_crypto_info,
            "get_gas_prices": self.get_gas_prices,
            "search_crypto_news": self.search_crypto_news,
        }

        if tool_name not in tools_map:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return await tools_map[tool_name](**kwargs)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
