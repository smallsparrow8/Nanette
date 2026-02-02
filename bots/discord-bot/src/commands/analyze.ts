import { ChatInputCommandInteraction, EmbedBuilder } from 'discord.js';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function analyzeCommand(interaction: ChatInputCommandInteraction) {
  const address = interaction.options.getString('address', true);
  const blockchain = interaction.options.getString('blockchain') || 'ethereum';

  // Validate address format (basic check)
  if (!address.match(/^0x[a-fA-F0-9]{40}$/)) {
    await interaction.reply({
      content: 'That doesn\'t look like a valid contract address. I need a proper Ethereum address — starts with 0x, 42 characters.',
      ephemeral: true,
    });
    return;
  }

  // Defer reply as analysis takes time
  await interaction.deferReply();

  try {
    // Call Python analysis API
    const response = await axios.post(`${API_URL}/analyze`, {
      contract_address: address,
      blockchain: blockchain,
    }, {
      timeout: 120000, // 2 minute timeout
    });

    const analysis = response.data;

    if (!analysis.success) {
      await interaction.editReply({
        content: `Something's wrong with this contract — I couldn't complete the analysis.\n${analysis.error}`,
      });
      return;
    }

    // Build response embed
    const scores = analysis.scores || {};
    const overallScore = scores.overall_score || 0;
    const riskLevel = scores.risk_level || 'unknown';

    // Determine embed color based on risk
    let color: number;
    if (overallScore >= 70) color = 0x00ff00; // Green
    else if (overallScore >= 50) color = 0xffff00; // Yellow
    else if (overallScore >= 30) color = 0xff8800; // Orange
    else color = 0xff0000; // Red

    const embed = new EmbedBuilder()
      .setTitle(`Nanette's Contract Analysis`)
      .setDescription(`Analysis for \`${address.substring(0, 10)}...${address.substring(address.length - 8)}\` on ${blockchain}`)
      .setColor(color)
      .addFields(
        {
          name: '📊 Overall Safety Score',
          value: `**${overallScore}/100** (${riskLevel.toUpperCase()} RISK)`,
          inline: false,
        },
        {
          name: '📝 Score Breakdown',
          value: [
            `Code Quality: ${scores.code_quality_score || 0}/25`,
            `Security: ${scores.security_score || 0}/40`,
            `Tokenomics: ${scores.tokenomics_score || 0}/20`,
            `Liquidity: ${scores.liquidity_score || 0}/15`,
          ].join('\n'),
          inline: true,
        }
      );

    // Add vulnerabilities if found
    const vulnerabilities = analysis.vulnerabilities || [];
    if (vulnerabilities.length > 0) {
      const criticalCount = vulnerabilities.filter((v: any) => v.severity === 'critical').length;
      const highCount = vulnerabilities.filter((v: any) => v.severity === 'high').length;

      embed.addFields({
        name: '⚠️ Vulnerabilities Detected',
        value: `Critical: ${criticalCount} | High: ${highCount} | Total: ${vulnerabilities.length}`,
        inline: false,
      });

      // Show top 3 critical/high issues
      const topIssues = vulnerabilities
        .filter((v: any) => v.severity === 'critical' || v.severity === 'high')
        .slice(0, 3);

      if (topIssues.length > 0) {
        embed.addFields({
          name: '🔴 Top Issues',
          value: topIssues
            .map((v: any) => `**[${v.severity.toUpperCase()}]** ${v.description}`)
            .join('\n')
            .substring(0, 1024), // Discord field limit
          inline: false,
        });
      }
    }

    // Add token info if available
    const tokenInfo = analysis.token_info;
    if (tokenInfo && tokenInfo.name) {
      embed.addFields({
        name: '💰 Token Information',
        value: [
          `Name: ${tokenInfo.name}`,
          `Symbol: ${tokenInfo.symbol}`,
          tokenInfo.total_supply ? `Supply: ${(tokenInfo.total_supply / Math.pow(10, tokenInfo.decimals || 18)).toLocaleString()}` : '',
        ].filter(Boolean).join('\n'),
        inline: true,
      });
    }

    // Add Nanette's recommendation
    if (scores.recommendation) {
      embed.addFields({
        name: '💡 Nanette\'s Recommendation',
        value: scores.recommendation,
        inline: false,
      });
    }

    embed.setFooter({
      text: 'Always DYOR (Do Your Own Research) • Not Financial Advice',
    })
      .setTimestamp();

    // Send Nanette's personalized response if available
    let messageContent = '';
    if (analysis.nanette_response) {
      // Truncate if too long (Discord message limit is 2000 chars)
      messageContent = analysis.nanette_response.substring(0, 1900);
    }

    await interaction.editReply({
      content: messageContent || undefined,
      embeds: [embed],
    });

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

    await interaction.editReply({
      content: errorMessage,
    });
  }
}
