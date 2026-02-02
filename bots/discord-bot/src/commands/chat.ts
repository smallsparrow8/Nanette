import { Message } from 'discord.js';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

// Store conversation history per channel (in production, use Redis or database)
const conversationHistory = new Map<string, any[]>();

export async function handleChatMessage(message: Message) {
  // Ignore messages from bots
  if (message.author.bot) return;

  // Only respond if mentioned or in DM
  const isMentioned = message.mentions.has(message.client.user!);
  const isDM = message.channel.isDMBased();

  if (!isMentioned && !isDM) return;

  // Remove mention from message content
  let userMessage = message.content
    .replace(/<@!?\d+>/g, '') // Remove mentions
    .trim();

  if (!userMessage) {
    await message.reply('I\'m here. What do you need?');
    return;
  }

  // Show typing indicator
  await message.channel.sendTyping();

  try {
    // Get conversation history for this channel
    const channelId = message.channel.id;
    let history = conversationHistory.get(channelId) || [];

    // Limit history to last 10 messages to avoid token limits
    if (history.length > 20) {
      history = history.slice(-20);
    }

    // Call chat API
    const response = await axios.post(`${API_URL}/chat`, {
      message: userMessage,
      conversation_history: history,
      user_id: message.author.id,
      channel_id: channelId,
    }, {
      timeout: 60000, // 1 minute timeout
    });

    const nanetteResponse = response.data.response;

    // Update conversation history
    history.push(
      { role: 'user', content: userMessage },
      { role: 'assistant', content: nanetteResponse }
    );
    conversationHistory.set(channelId, history);

    // Split long messages if needed (Discord limit: 2000 chars)
    if (nanetteResponse.length > 1900) {
      const chunks = splitMessage(nanetteResponse, 1900);
      for (const chunk of chunks) {
        await message.reply(chunk);
      }
    } else {
      await message.reply(nanetteResponse);
    }

  } catch (error: any) {
    console.error('Error in chat:', error);

    let errorMessage = 'Something\'s interfering with my senses. ';

    if (error.code === 'ECONNREFUSED') {
      errorMessage += 'I\'ve lost connection. Try again shortly.';
    } else if (error.response) {
      errorMessage += `${error.response.data?.error || error.message}`;
    } else {
      errorMessage += 'Give me a moment and try again.';
    }

    await message.reply(errorMessage);
  }
}

function splitMessage(text: string, maxLength: number): string[] {
  const chunks: string[] = [];
  let currentChunk = '';

  const lines = text.split('\n');

  for (const line of lines) {
    if (currentChunk.length + line.length + 1 > maxLength) {
      if (currentChunk) {
        chunks.push(currentChunk);
        currentChunk = '';
      }

      // If a single line is too long, split it by sentences
      if (line.length > maxLength) {
        const sentences = line.match(/[^.!?]+[.!?]+/g) || [line];
        for (const sentence of sentences) {
          if (currentChunk.length + sentence.length > maxLength) {
            if (currentChunk) chunks.push(currentChunk);
            currentChunk = sentence;
          } else {
            currentChunk += sentence;
          }
        }
      } else {
        currentChunk = line;
      }
    } else {
      currentChunk += (currentChunk ? '\n' : '') + line;
    }
  }

  if (currentChunk) {
    chunks.push(currentChunk);
  }

  return chunks;
}

// Clear old conversations (call periodically)
export function clearOldConversations(maxAgeMs: number = 3600000) {
  // In production, implement proper cleanup with timestamps
  // For now, just clear if too many conversations stored
  if (conversationHistory.size > 100) {
    conversationHistory.clear();
  }
}
