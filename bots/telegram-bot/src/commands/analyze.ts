import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function analyzeCommand(ctx: Context) {
  // Get the contract address from the command
  const text = ctx.message && 'text' in ctx.message ? ctx.message.text : '';
  const args = text.split(' ').slice(1);

  if (args.length === 0) {
    return ctx.reply(
      'Give me an address and I\'ll tell you what\'s in it.\n\n' +
      'Usage: /analyze <contract_address> [blockchain]\n\n' +
      'Example: /analyze 0x6B175474E89094C44Da98b954EedeAC495271d0F ethereum\n\n' +
      'Chains I watch: ethereum, bsc, polygon, arbitrum, base, optimism'
    );
  }

  const address = args[0];
  const blockchain = args[1] || 'ethereum';

  // Validate address format (basic check)
  if (!address.match(/^0x[a-fA-F0-9]{40}$/)) {
    return ctx.reply(
      "That doesn't look like a valid contract address. I need a proper Ethereum address — starts with 0x, 42 characters."
    );
  }

  // Send "analyzing" message
  const statusMessage = await ctx.reply(
    'Reading the contract... Give me a moment to see what\'s inside.'
  );

  try {
    // Call Python analysis API
    const response = await axios.post(
      `${API_URL}/analyze`,
      {
        contract_address: address,
        blockchain: blockchain,
      },
      {
        timeout: 120000, // 2 minute timeout
      }
    );

    const analysis = response.data;

    if (!analysis.success) {
      await ctx.telegram.editMessageText(
        ctx.chat?.id,
        statusMessage.message_id,
        undefined,
        `Something's wrong with this contract — I couldn't complete the analysis.\n${analysis.error}`
      );
      return;
    }

    // Build response message
    const scores = analysis.scores || {};
    const overallScore = scores.overall_score || 0;
    const riskLevel = scores.risk_level || 'unknown';

    // Determine emoji based on risk
    let riskEmoji = '⚠️';
    if (overallScore >= 70) riskEmoji = '✅';
    else if (overallScore >= 50) riskEmoji = '⚠️';
    else if (overallScore >= 30) riskEmoji = '🔶';
    else riskEmoji = '🔴';

    let message = `*Nanette's Contract Analysis*\n\n`;
    message += `📍 Contract: \`${address.substring(0, 10)}...${address.substring(address.length - 8)}\`\n`;
    message += `⛓️ Blockchain: ${blockchain}\n\n`;

    message += `📊 *Overall Safety Score*\n`;
    message += `${riskEmoji} *${overallScore}/100* (${riskLevel.toUpperCase()} RISK)\n\n`;

    message += `📝 *Score Breakdown*\n`;
    message += `• Code Quality: ${scores.code_quality_score || 0}/25\n`;
    message += `• Security: ${scores.security_score || 0}/40\n`;
    message += `• Tokenomics: ${scores.tokenomics_score || 0}/20\n`;
    message += `• Liquidity: ${scores.liquidity_score || 0}/15\n\n`;

    // Add vulnerabilities if found
    const vulnerabilities = analysis.vulnerabilities || [];
    if (vulnerabilities.length > 0) {
      const criticalCount = vulnerabilities.filter((v: any) => v.severity === 'critical').length;
      const highCount = vulnerabilities.filter((v: any) => v.severity === 'high').length;

      message += `⚠️ *Vulnerabilities Detected*\n`;
      message += `🔴 Critical: ${criticalCount} | 🟠 High: ${highCount} | Total: ${vulnerabilities.length}\n\n`;

      // Show top 3 critical/high issues
      const topIssues = vulnerabilities
        .filter((v: any) => v.severity === 'critical' || v.severity === 'high')
        .slice(0, 3);

      if (topIssues.length > 0) {
        message += `🔴 *Top Issues*\n`;
        topIssues.forEach((v: any) => {
          message += `• [${v.severity.toUpperCase()}] ${v.description}\n`;
        });
        message += '\n';
      }
    }

    // Add token info if available
    const tokenInfo = analysis.token_info;
    if (tokenInfo && tokenInfo.name) {
      message += `💰 *Token Information*\n`;
      message += `• Name: ${tokenInfo.name}\n`;
      message += `• Symbol: ${tokenInfo.symbol}\n`;
      if (tokenInfo.total_supply) {
        const supply = tokenInfo.total_supply / Math.pow(10, tokenInfo.decimals || 18);
        message += `• Supply: ${supply.toLocaleString()}\n`;
      }
      message += '\n';
    }

    // Add Nanette's recommendation
    if (scores.recommendation) {
      message += `💡 *Nanette's Recommendation*\n`;
      message += `${scores.recommendation}\n\n`;
    }

    message += `_Always DYOR (Do Your Own Research) • Not Financial Advice_`;

    // Delete status message and send analysis
    await ctx.telegram.deleteMessage(ctx.chat!.id, statusMessage.message_id);

    // Send Nanette's personalized response if available
    if (analysis.nanette_response) {
      await ctx.reply(analysis.nanette_response.substring(0, 4000), { parse_mode: 'Markdown' });
    }

    // Send structured analysis
    await ctx.reply(message, { parse_mode: 'Markdown' });

  } catch (error: any) {
    console.error('Error calling analysis API:', error);

    let errorMessage = 'I couldn\'t read that contract. ';

    if (error.code === 'ECONNREFUSED') {
      errorMessage += 'I\'ve lost connection to the analysis service. Try again shortly.';
    } else if (error.response) {
      errorMessage += `${error.response.data?.error || error.message}`;
    } else {
      errorMessage += 'Verify the address and try again.';
    }

    await ctx.telegram.editMessageText(
      ctx.chat?.id,
      statusMessage.message_id,
      undefined,
      errorMessage
    );
  }
}
