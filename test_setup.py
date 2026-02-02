"""
Nanette Setup Test Script
Run this to verify your installation is working correctly
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        from shared.config import settings
        print("✓ Config module loaded")

        from shared.database import Database
        print("✓ Database module loaded")

        from shared.blockchain.evm_client import EVMClient
        print("✓ EVM client module loaded")

        from analyzers.contract_analyzer.evm_analyzer import EVMAnalyzer
        print("✓ EVM analyzer module loaded")

        from analyzers.contract_analyzer.vulnerability_scanner import VulnerabilityScanner
        print("✓ Vulnerability scanner module loaded")

        from analyzers.contract_analyzer.tokenomics_analyzer import TokenomicsAnalyzer
        print("✓ Tokenomics analyzer module loaded")

        from analyzers.contract_analyzer.safety_scorer import SafetyScorer
        print("✓ Safety scorer module loaded")

        from core.nanette.personality import Nanette
        print("✓ Nanette personality module loaded")

        from core.nanette.orchestrator import AnalysisOrchestrator
        print("✓ Analysis orchestrator module loaded")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from shared.config import settings

        # Check essential keys
        if not settings.anthropic_api_key or settings.anthropic_api_key == "your_claude_api_key":
            print("⚠ ANTHROPIC_API_KEY not set or using placeholder")
            print("  Get your key from: https://console.anthropic.com/")
        else:
            print("✓ ANTHROPIC_API_KEY is set")

        if settings.discord_bot_token:
            print("✓ DISCORD_BOT_TOKEN is set")
        else:
            print("⚠ DISCORD_BOT_TOKEN not set (optional for API-only usage)")

        print(f"✓ Environment: {settings.environment}")
        print(f"✓ Database: {settings.database_url}")

        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_database():
    """Test database connection"""
    print("\nTesting database...")
    try:
        from shared.database import Database

        db = Database()
        db.create_tables()
        print("✓ Database tables created/verified")

        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_api_dependencies():
    """Test API dependencies"""
    print("\nTesting API dependencies...")
    try:
        import anthropic
        print("✓ anthropic package installed")

        import web3
        print("✓ web3 package installed")

        import fastapi
        print("✓ fastapi package installed")

        import aiohttp
        print("✓ aiohttp package installed")

        import pydantic
        print("✓ pydantic package installed")

        import sqlalchemy
        print("✓ sqlalchemy package installed")

        return True
    except Exception as e:
        print(f"✗ Dependency test failed: {e}")
        print("\nRun: pip install -r requirements.txt")
        return False


async def test_blockchain_connection():
    """Test blockchain connection"""
    print("\nTesting blockchain connection...")
    try:
        from shared.blockchain.evm_client import EVMClient

        client = EVMClient("ethereum")

        if client.is_connected():
            print("✓ Connected to Ethereum RPC")
        else:
            print("⚠ Could not connect to Ethereum RPC")
            print("  This is OK if you're using free public RPCs (they can be slow)")

        # Test address validation
        test_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
        if client.is_valid_address(test_address):
            print("✓ Address validation working")

        return True
    except Exception as e:
        print(f"✗ Blockchain connection test failed: {e}")
        return False


async def test_claude_api():
    """Test Claude API connection"""
    print("\nTesting Claude API...")
    try:
        from core.nanette.personality import Nanette
        from shared.config import settings

        if not settings.anthropic_api_key or settings.anthropic_api_key == "your_claude_api_key":
            print("⚠ Skipping Claude API test - API key not configured")
            return True

        nanette = Nanette()
        greeting = nanette.get_greeting()

        if greeting and "Nanette" in greeting:
            print("✓ Nanette personality initialized")
            print(f"✓ Using model: {nanette.model}")

            # Try a simple chat
            print("  Testing Claude API call...")
            response = await nanette.chat("Hello!")
            if response:
                print("✓ Claude API is working!")
                print(f"  Response preview: {response[:100]}...")
            else:
                print("⚠ Claude API returned empty response")

        return True
    except Exception as e:
        print(f"✗ Claude API test failed: {e}")
        print("  Check your ANTHROPIC_API_KEY in .env")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Nanette Setup Verification")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Configuration": test_config(),
        "Database": test_database(),
        "Dependencies": test_api_dependencies(),
    }

    # Async tests
    import asyncio

    async def run_async_tests():
        results["Blockchain"] = await test_blockchain_connection()
        results["Claude API"] = await test_claude_api()

    asyncio.run(run_async_tests())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! Nanette is ready to go!")
        print("\nNext steps:")
        print("1. Start the API: python api/main.py")
        print("2. Start Discord bot: cd bots/discord-bot && npm run dev")
        print("3. Try /analyze command in Discord!")
    else:
        print("\n⚠ Some tests failed. Please review the errors above.")
        print("\nCommon fixes:")
        print("- Make sure .env file exists and has your API keys")
        print("- Run: pip install -r requirements.txt")
        print("- Check Python version: python --version (should be 3.11+)")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
