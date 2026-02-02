import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function traceCommand(ctx: Context) {
  const text = ctx.message && 'text' in ctx.message ? ctx.message.text : '';
  const args = text.split(' ').slice(1);

  if (args.length === 0) {
    return ctx.reply(
      'Give me a contract address and I\'ll trace who deployed it.\n\n' +
      'Usage: /trace <address> [blockchain]\n\n' +
      'Example: /trace 0x6B175474E89094C44Da98b954EedeAC495271d0F ethereum\n\n' +
      'I\'ll find the deployer, check their history, and calculate a Creator Trust Score.\n\n' +
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
    'Tracing the creator... I\'m following the deployment trail, checking their other contracts, and building a trust profile. This takes a moment.'
  );

  try {
    const response = await axios.post(
      `${API_URL}/trace-creator`,
      {
        contract_address: address,
        blockchain: blockchain,
      },
      {
        timeout: 180000, // 3 minute timeout
      }
    );

    const result = response.data;

    if (!result.success) {
      await ctx.telegram.editMessageText(
        ctx.chat?.id,
        statusMessage.message_id,
        undefined,
        `The trail went cold. ${result.error || 'Could not trace the creator.'}`
      );
      return;
    }

    // Delete the status message
    await ctx.telegram.deleteMessage(ctx.chat!.id, statusMessage.message_id);

    const data = result.data || {};
    const shortAddr = `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    const deployerAddr = data.deployer_address || 'Unknown';
    const shortDeployer = deployerAddr.length > 10
      ? `${deployerAddr.substring(0, 6)}...${deployerAddr.substring(deployerAddr.length - 4)}`
      : deployerAddr;

    // Trust score display
    const score = data.creator_trust_score ?? 0;
    const riskLevel = data.risk_level || 'unknown';
    const scoreBar = getScoreBar(score);
    const riskIcon = getRiskIcon(riskLevel);

    let summary = `*Creator Trace* — ${shortAddr}\n`;
    summary += `Chain: ${blockchain}\n\n`;

    // Deployer info
    summary += `*Deployer*\n`;
    summary += `Address: \`${deployerAddr}\`\n`;
    if (data.deployer_wallet_age_days !== undefined) {
      summary += `Wallet age: ${formatAge(data.deployer_wallet_age_days)}\n`;
    }
    if (data.deployer_total_transactions !== undefined) {
      summary += `Total transactions: ${data.deployer_total_transactions.toLocaleString()}\n`;
    }
    if (data.deployer_balance_eth !== undefined) {
      summary += `Balance: ${data.deployer_balance_eth.toFixed(4)} ETH\n`;
    }
    if (data.is_factory_deployed) {
      summary += `Deployed via factory contract\n`;
    }
    summary += '\n';

    // Trust score
    summary += `*Creator Trust Score*\n`;
    summary += `${riskIcon} ${score}/100 — ${riskLevel.replace('_', ' ').toUpperCase()}\n`;
    summary += `${scoreBar}\n\n`;

    // Score breakdown
    const breakdown = data.score_breakdown || {};
    if (Object.keys(breakdown).length > 0) {
      summary += `*Score Breakdown*\n`;
      if (breakdown.wallet_maturity !== undefined) {
        summary += `Wallet Maturity: ${breakdown.wallet_maturity}/20\n`;
      }
      if (breakdown.deployment_history !== undefined) {
        summary += `Deploy History: ${breakdown.deployment_history}/30\n`;
      }
      if (breakdown.sibling_survival !== undefined) {
        summary += `Sibling Survival: ${breakdown.sibling_survival}/25\n`;
      }
      if (breakdown.funding_transparency !== undefined) {
        summary += `Funding Transparency: ${breakdown.funding_transparency}/15\n`;
      }
      if (breakdown.behavioral_patterns !== undefined) {
        summary += `Behavioral Patterns: ${breakdown.behavioral_patterns}/10\n`;
      }
      summary += '\n';
    }

    // Sibling contracts
    const siblings = data.sibling_contracts || [];
    const totalSiblings = data.total_siblings || 0;
    const aliveSiblings = data.alive_siblings || 0;

    if (totalSiblings > 0) {
      summary += `*Other Contracts by Creator* (${aliveSiblings}/${totalSiblings} alive)\n`;
      siblings.slice(0, 5).forEach((s: any) => {
        const sAddr = s.address
          ? `${s.address.substring(0, 6)}...${s.address.substring(s.address.length - 4)}`
          : '???';
        const status = s.is_alive ? 'alive' : 'dead';
        const statusIcon = s.is_alive ? '🟢' : '🔴';
        let line = `${statusIcon} \`${sAddr}\` — ${status}`;
        if (s.name) line += ` (${s.name})`;
        if (s.lp_removed) line += ' ⚠️ LP removed';
        summary += `${line}\n`;
      });
      if (totalSiblings > 5) {
        summary += `...and ${totalSiblings - 5} more\n`;
      }
      summary += '\n';
    }

    // Red flags
    const redFlags = data.red_flags || [];
    if (redFlags.length > 0) {
      summary += `*Red Flags*\n`;
      redFlags.forEach((flag: string) => {
        summary += `🚩 ${flag}\n`;
      });
      summary += '\n';
    }

    // Funding source
    const funding = data.funding_source || {};
    if (funding.source_type) {
      summary += `*Funding Source*\n`;
      summary += `Type: ${funding.source_type}\n`;
      if (funding.source_address) {
        const fAddr = funding.source_address;
        summary += `From: \`${fAddr.substring(0, 6)}...${fAddr.substring(fAddr.length - 4)}\`\n`;
      }
      if (funding.source_label) {
        summary += `Label: ${funding.source_label}\n`;
      }
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
    console.error('Error calling trace-creator API:', error);

    let errorMessage = 'The trail went cold. ';

    if (error.code === 'ECONNREFUSED') {
      errorMessage += 'I\'ve lost connection to the analysis service. Try again shortly.';
    } else if (error.code === 'ECONNABORTED') {
      errorMessage += 'The trace is taking longer than expected. The deployer may have a very long history.';
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

function getScoreBar(score: number): string {
  const filled = Math.round(score / 10);
  const empty = 10 - filled;
  return '█'.repeat(filled) + '░'.repeat(empty) + ` ${score}%`;
}

function getRiskIcon(level: string): string {
  switch (level) {
    case 'very_low': return '🟢';
    case 'low': return '🟢';
    case 'medium': return '🟡';
    case 'high': return '🟠';
    case 'critical': return '🔴';
    default: return '⚪';
  }
}

function formatAge(days: number): string {
  if (days < 1) return 'Less than a day';
  if (days < 7) return `${Math.round(days)} days`;
  if (days < 30) return `${Math.round(days / 7)} weeks`;
  if (days < 365) return `${Math.round(days / 30)} months`;
  const years = Math.floor(days / 365);
  const remainingMonths = Math.round((days % 365) / 30);
  if (remainingMonths === 0) return `${years} year${years > 1 ? 's' : ''}`;
  return `${years}y ${remainingMonths}mo`;
}
