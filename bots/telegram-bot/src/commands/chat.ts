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

/**
 * Get file info from various Telegram media types
 */
function getFileInfo(ctx: Context): {
  fileId: string;
  fileName?: string;
  fileSize?: number;
  mimeType?: string;
  mediaType: string;
} | null {
  if (!ctx.message) return null;

  // Photo
  if ('photo' in ctx.message && ctx.message.photo) {
    const largest = ctx.message.photo[ctx.message.photo.length - 1];
    return {
      fileId: largest.file_id,
      fileSize: largest.file_size,
      mimeType: 'image/jpeg',
      mediaType: 'photo',
    };
  }

  // Document (files, images sent as documents, PDFs, etc.)
  if ('document' in ctx.message && ctx.message.document) {
    return {
      fileId: ctx.message.document.file_id,
      fileName: ctx.message.document.file_name,
      fileSize: ctx.message.document.file_size,
      mimeType: ctx.message.document.mime_type,
      mediaType: 'document',
    };
  }

  // Sticker
  if ('sticker' in ctx.message && ctx.message.sticker) {
    return {
      fileId: ctx.message.sticker.file_id,
      fileSize: ctx.message.sticker.file_size,
      mimeType: ctx.message.sticker.is_animated ? 'application/x-tgsticker' :
                ctx.message.sticker.is_video ? 'video/webm' : 'image/webp',
      mediaType: 'sticker',
    };
  }

  // Video
  if ('video' in ctx.message && ctx.message.video) {
    return {
      fileId: ctx.message.video.file_id,
      fileName: ctx.message.video.file_name,
      fileSize: ctx.message.video.file_size,
      mimeType: ctx.message.video.mime_type || 'video/mp4',
      mediaType: 'video',
    };
  }

  // Video note (round videos)
  if ('video_note' in ctx.message && ctx.message.video_note) {
    return {
      fileId: ctx.message.video_note.file_id,
      fileSize: ctx.message.video_note.file_size,
      mimeType: 'video/mp4',
      mediaType: 'video_note',
    };
  }

  // Voice message
  if ('voice' in ctx.message && ctx.message.voice) {
    return {
      fileId: ctx.message.voice.file_id,
      fileSize: ctx.message.voice.file_size,
      mimeType: ctx.message.voice.mime_type || 'audio/ogg',
      mediaType: 'voice',
    };
  }

  // Audio file
  if ('audio' in ctx.message && ctx.message.audio) {
    return {
      fileId: ctx.message.audio.file_id,
      fileName: ctx.message.audio.file_name,
      fileSize: ctx.message.audio.file_size,
      mimeType: ctx.message.audio.mime_type || 'audio/mpeg',
      mediaType: 'audio',
    };
  }

  // Animation (GIF)
  if ('animation' in ctx.message && ctx.message.animation) {
    return {
      fileId: ctx.message.animation.file_id,
      fileName: ctx.message.animation.file_name,
      fileSize: ctx.message.animation.file_size,
      mimeType: ctx.message.animation.mime_type || 'video/mp4',
      mediaType: 'animation',
    };
  }

  return null;
}

/**
 * Determine analysis mode from caption text
 */
function detectAnalysisMode(text: string): string | undefined {
  const lower = text.toLowerCase();
  const esotericKeywords = [
    'clue', 'clues', 'hidden', 'esoteric', 'symbolic', 'symbol',
    'mystery', 'secret', 'occult', 'mystical', 'decode', 'cipher',
    'meaning', 'deeper', 'anomaly', 'anomalies', 'strange', 'odd',
    'unusual', 'pattern', 'message', 'sign', 'omen', 'riddle',
  ];
  const forensicKeywords = [
    'metadata', 'exif', 'forensic', 'analyze data', 'underlying',
    'steganography', 'stego', 'hidden data', 'embedded', 'tampered',
    'modified', 'original', 'authentic', 'manipulated', 'edited',
  ];

  if (esotericKeywords.some((kw) => lower.includes(kw))) {
    return 'esoteric';
  }
  if (forensicKeywords.some((kw) => lower.includes(kw))) {
    return 'forensic';
  }
  return undefined;
}

export async function handleChatMediaMessage(ctx: Context) {
  const fileInfo = getFileInfo(ctx);
  if (!fileInfo) return;

  const chatId = ctx.chat!.id;
  const userId = ctx.from!.id;
  const caption = ('caption' in ctx.message! ? (ctx.message as any).caption : '') || '';

  // Show typing action
  await ctx.sendChatAction('typing');

  try {
    // Download the file
    const fileLink = await ctx.telegram.getFileLink(fileInfo.fileId);
    const fileResponse = await axios.get(fileLink.href, {
      responseType: 'arraybuffer',
    });
    const fileBase64 = Buffer.from(fileResponse.data).toString('base64');

    // Get conversation history for this chat
    let history = conversationHistory.get(chatId) || [];
    if (history.length > 20) {
      history = history.slice(-20);
    }

    // Detect analysis mode from caption
    const analysisMode = detectAnalysisMode(caption);

    // Call chat API with media
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: caption || '',
        conversation_history: history,
        user_id: userId.toString(),
        channel_id: chatId.toString(),
        image_base64: fileBase64,
        image_media_type: fileInfo.mimeType,
        file_name: fileInfo.fileName,
        file_size: fileInfo.fileSize,
        analysis_mode: analysisMode,
      },
      {
        timeout: 120000, // 2 minutes — media analysis takes longer
      }
    );

    const nanetteResponse = response.data.response;

    // Update conversation history (store text summary, not base64)
    const mediaDesc = fileInfo.fileName
      ? `[sent ${fileInfo.mediaType}: ${fileInfo.fileName}]`
      : `[sent ${fileInfo.mediaType}]`;
    history.push(
      { role: 'user', content: caption || mediaDesc },
      { role: 'assistant', content: nanetteResponse }
    );
    conversationHistory.set(chatId, history);

    // Split long messages if needed (Telegram limit: 4096 chars)
    if (nanetteResponse.length > 4000) {
      const chunks = splitMessage(nanetteResponse, 4000);
      for (const chunk of chunks) {
        await ctx.reply(chunk, { parse_mode: 'Markdown' });
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
    } else {
      await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });
    }
  } catch (error: any) {
    console.error(`Error in chat ${fileInfo.mediaType}:`, error);

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

// Keep old function name as alias for backwards compatibility
export const handleChatImageMessage = handleChatMediaMessage;

// Clear old conversations (call periodically)
export function clearOldConversations(maxAgeMs: number = 3600000) {
  // In production, implement proper cleanup with timestamps
  // For now, just clear if too many conversations stored
  if (conversationHistory.size > 100) {
    conversationHistory.clear();
  }
}
