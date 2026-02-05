import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

// Store conversation history per chat (in production, use Redis or database)
const conversationHistory = new Map<number, any[]>();

export async function handleChatMessage(ctx: Context) {
  if (!ctx.message || !('text' in ctx.message)) return;

  const userMessage = ctx.message.text;
  const chatId = ctx.chat!.id;
  const userId = ctx.from!.id;

  if (!userMessage) {
    return ctx.reply('I\'m here. What do you need?');
  }

  // Show typing action
  await ctx.sendChatAction('typing');

  try {
    // Get conversation history for this chat
    let history = conversationHistory.get(chatId) || [];

    // Limit history to last 20 messages to avoid token limits
    if (history.length > 20) {
      history = history.slice(-20);
    }

    // Call chat API
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: userMessage,
        conversation_history: history,
        user_id: userId.toString(),
        channel_id: chatId.toString(),
      },
      {
        timeout: 60000, // 1 minute timeout
      }
    );

    const nanetteResponse = response.data.response;

    // Update conversation history
    history.push(
      { role: 'user', content: userMessage },
      { role: 'assistant', content: nanetteResponse }
    );
    conversationHistory.set(chatId, history);

    // Split long messages if needed (Telegram limit: 4096 chars)
    if (nanetteResponse.length > 4000) {
      const chunks = splitMessage(nanetteResponse, 4000);
      for (const chunk of chunks) {
        await ctx.reply(chunk, { parse_mode: 'Markdown' });
        // Small delay between chunks
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    } else {
      await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });
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

    await ctx.reply(errorMessage);
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

export async function handleChatImageMessage(ctx: Context) {
  if (!ctx.message || !('photo' in ctx.message)) return;

  const chatId = ctx.chat!.id;
  const userId = ctx.from!.id;
  const caption = ('caption' in ctx.message ? ctx.message.caption : '') || '';

  // Show typing action
  await ctx.sendChatAction('typing');

  try {
    // Get the largest photo size (last in array)
    const photos = ctx.message.photo;
    const largest = photos[photos.length - 1];

    // Download the photo
    const fileLink = await ctx.telegram.getFileLink(largest.file_id);
    const imageResponse = await axios.get(fileLink.href, {
      responseType: 'arraybuffer',
    });
    const imageBase64 = Buffer.from(imageResponse.data).toString('base64');

    // Get conversation history for this chat
    let history = conversationHistory.get(chatId) || [];
    if (history.length > 20) {
      history = history.slice(-20);
    }

    // Call chat API with image
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: caption || '',
        conversation_history: history,
        user_id: userId.toString(),
        channel_id: chatId.toString(),
        image_base64: imageBase64,
        image_media_type: 'image/jpeg',
      },
      {
        timeout: 90000, // 90 seconds — vision takes longer
      }
    );

    const nanetteResponse = response.data.response;

    // Update conversation history (store text summary, not base64)
    history.push(
      { role: 'user', content: caption || '[sent an image]' },
      { role: 'assistant', content: nanetteResponse }
    );
    conversationHistory.set(chatId, history);

    // Split long messages if needed (Telegram limit: 4096 chars)
    if (nanetteResponse.length > 4000) {
      const chunks = splitMessage(nanetteResponse, 4000);
      for (const chunk of chunks) {
        await ctx.reply(chunk, { parse_mode: 'Markdown' });
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    } else {
      await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });
    }
  } catch (error: any) {
    console.error('Error in chat image:', error);

    let errorMessage = "Something's interfering with my senses. ";

    if (error.code === 'ECONNREFUSED') {
      errorMessage += "I've lost connection. Try again shortly.";
    } else if (error.response) {
      errorMessage += `${error.response.data?.error || error.message}`;
    } else {
      errorMessage += 'Give me a moment and try again.';
    }

    await ctx.reply(errorMessage);
  }
}

// Clear old conversations (call periodically)
export function clearOldConversations(maxAgeMs: number = 3600000) {
  // In production, implement proper cleanup with timestamps
  // For now, just clear if too many conversations stored
  if (conversationHistory.size > 100) {
    conversationHistory.clear();
  }
}
