import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function interactionsCommand(ctx: Context) {
  const text = ctx.message && 'text' in ctx.message ? ctx.message.text : '';
  const args = text.split(' ').slice(1);

  if (args.length === 0) {
    return ctx.reply(
      'Give me an address and I\'ll trace where the money flows.\n\n' +
      'Usage: /interactions <address> [blockchain]\n\n' +
      'Example: /interactions 0x6B175474E89094C44Da98b954EedeAC495271d0F ethereum\n\n' +
      'Chains I watch: ethereum, bsc, polygon, arbitrum, base, optimism'
    );
  }

  const address = args[0];
  const blockchain = args[1] || 'ethereum';

  // Validate address format
  if (!address.match(/^0x[a-fA-F0-9]{40}$/)) {
    return ctx.reply(
      "That doesn't look like a valid address. I need a proper Ethereum address — starts with 0x, 42 characters."
    );
  }

  const statusMessage = await ctx.reply(
    'Tracing the money trail... I\'m mapping every address this contract has touched. Give me a moment.'
  );

  try {
    const response = await axios.post(
      `${API_URL}/analyze-interactions`,
      {
        contract_address: address,
        blockchain: blockchain,
      },
      {
        timeout: 180000, // 3 minute timeout — interaction analysis is heavier
      }
    );

    const result = response.data;

    if (!result.success) {
      await ctx.telegram.editMessageText(
        ctx.chat?.id,
        statusMessage.message_id,
        undefined,
        `The trail went cold. ${result.error || 'Could not complete the interaction analysis.'}`
      );
      return;
    }

    // Delete the status message
    await ctx.telegram.deleteMessage(ctx.chat!.id, statusMessage.message_id);

    // Send the graph image
    if (result.graph_image) {
      const imageBuffer = Buffer.from(result.graph_image, 'base64');
      const shortAddr = `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;

      await ctx.replyWithPhoto(
        { source: imageBuffer },
        {
          caption: `Interaction Map — ${shortAddr} on ${blockchain}`,
        }
      );
    }

    // Build stats summary
    const stats = result.stats || {};
    const patterns = result.patterns || [];
    const risks = result.risk_indicators || [];

    let summary = `*Interaction Analysis*\n`;
    summary += `Address: \`${address.substring(0, 10)}...${address.substring(address.length - 6)}\`\n`;
    summary += `Chain: ${blockchain}\n\n`;

    summary += `*Stats*\n`;
    summary += `• Transactions: ${stats.total_transactions || 0}\n`;
    summary += `• Unique addresses: ${stats.unique_addresses || 0}\n`;
    summary += `• Value in: ${(stats.total_value_in || 0).toFixed(4)} ETH\n`;
    summary += `• Value out: ${(stats.total_value_out || 0).toFixed(4)} ETH\n\n`;

    // Top counterparties
    const topSenders = result.top_senders || [];
    const topReceivers = result.top_receivers || [];

    if (topSenders.length > 0) {
      summary += `*Top Senders*\n`;
      topSenders.slice(0, 3).forEach((s: any) => {
        const label = s.label || `${s.address?.substring(0, 8)}...`;
        summary += `• ${label}: ${s.count} txs\n`;
      });
      summary += '\n';
    }

    if (topReceivers.length > 0) {
      summary += `*Top Receivers*\n`;
      topReceivers.slice(0, 3).forEach((r: any) => {
        const label = r.label || `${r.address?.substring(0, 8)}...`;
        summary += `• ${label}: ${r.count} txs\n`;
      });
      summary += '\n';
    }

    // Patterns
    if (patterns.length > 0) {
      summary += `*Patterns Detected*\n`;
      patterns.slice(0, 4).forEach((p: any) => {
        const icon = p.severity === 'warning' || p.severity === 'high' ? '⚠️' : 'ℹ️';
        summary += `${icon} ${p.description}\n`;
      });
      summary += '\n';
    }

    // Risk indicators
    if (risks.length > 0) {
      summary += `*Risk Indicators*\n`;
      risks.slice(0, 3).forEach((r: string) => {
        summary += `🔴 ${r}\n`;
      });
      summary += '\n';
    }

    // Send stats
    await ctx.reply(summary, { parse_mode: 'Markdown' });

    // Send Nanette's explanation
    if (result.nanette_explanation) {
      const explanation = result.nanette_explanation.substring(0, 4000);
      await ctx.reply(explanation);
    }

  } catch (error: any) {
    console.error('Error calling interactions API:', error);

    let errorMessage = 'The trail went cold. ';

    if (error.code === 'ECONNREFUSED') {
      errorMessage += 'I\'ve lost connection to the analysis service. Try again shortly.';
    } else if (error.code === 'ECONNABORTED') {
      errorMessage += 'The analysis is taking longer than expected. The address may have too many transactions to map quickly.';
    } else if (error.response) {
      errorMessage += `${error.response.data?.detail || error.message}`;
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
