import { Context } from 'telegraf';
import axios from 'axios';
import { isUserAdmin } from '../utils/adminCache';

const API_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Check if Nanette is directly addressed (must always respond)
 */
function isDirectlyAddressed(ctx: Context, text: string): boolean {
  const lowerText = text.toLowerCase();

  // Name mentions
  if (lowerText.includes('nanette')) return true;

  // @mention of the bot
  const botUsername = ctx.botInfo?.username?.toLowerCase();
  if (botUsername && lowerText.includes(`@${botUsername}`)) return true;

  // Reply to Nanette's message
  const msg = ctx.message as any;
  if (msg?.reply_to_message?.from?.is_bot) {
    const replyToBotId = msg.reply_to_message.from.id;
    if (replyToBotId === ctx.botInfo?.id) return true;
  }

  return false;
}

/**
 * Handle a text message from a group/supergroup chat.
 * Nanette reads all messages and decides naturally when to engage.
 */
export async function handleGroupMessage(ctx: Context) {
  if (!ctx.message || !('text' in ctx.message)) return;
  if (!ctx.chat || ctx.chat.type === 'private') return;

  const text = ctx.message.text;
  const chatId = ctx.chat.id;
  const chatTitle = 'title' in ctx.chat ? ctx.chat.title : undefined;
  const chatType = ctx.chat.type;
  const messageId = ctx.message.message_id;
  const userId = ctx.from?.id;
  const username =
    ctx.from?.username || ctx.from?.first_name || 'Unknown';

  // Skip bot commands — those are handled by command handlers
  if (text.startsWith('/')) return;

  // Check if directly addressed (must respond)
  const directlyAddressed = isDirectlyAddressed(ctx, text);

  // Send to API — Nanette decides whether to engage
  try {
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: text,
        conversation_history: [],
        user_id: userId ? String(userId) : null,
        channel_id: String(chatId),
        username: username,
        is_group: true,
        directly_addressed: directlyAddressed,
      },
      { timeout: 60000 }
    );

    const result = response.data;

    // Only reply if Nanette decided to respond
    if (result.response && result.should_respond !== false) {
      await ctx.reply(result.response, {
        parse_mode: 'Markdown',
        reply_parameters: {
          message_id: messageId,
        },
      });
    }
  } catch (error: any) {
    if (error.code !== 'ECONNREFUSED') {
      console.error(
        `Channel message error (chat ${chatId}):`,
        error.message
      );
    }
  }
  return;

  // Background channel analysis for non-directed messages
  // Check if user is admin
  let isAdmin = false;
  if (userId) {
    try {
      isAdmin = await isUserAdmin(
        ctx.telegram,
        chatId,
        userId
      );
    } catch {
      // Non-critical — default to false
    }
  }

  // Get reply-to message ID if this is a reply
  const replyToId =
    ctx.message.reply_to_message?.message_id || null;

  try {
    const response = await axios.post(
      `${API_URL}/channel/message`,
      {
        chat_id: String(chatId),
        chat_title: chatTitle,
        chat_type: chatType,
        message_id: String(messageId),
        user_id: userId ? String(userId) : null,
        username: username,
        is_admin: isAdmin,
        text: text,
        reply_to_message_id: replyToId
          ? String(replyToId)
          : null,
        timestamp: new Date().toISOString(),
        platform: 'telegram',
      },
      { timeout: 30000 }
    );

    const result = response.data;

    // If channel analyzer says respond, send her message
    if (result.should_respond && result.nanette_response) {
      await ctx.reply(result.nanette_response, {
        parse_mode: 'Markdown',
        reply_parameters: {
          message_id: messageId,
        },
      });
    }
  } catch (error: any) {
    // Silently fail for group messages — don't spam the chat
    if (error.code !== 'ECONNREFUSED') {
      console.error(
        `Channel message processing error (chat ${chatId}):`,
        error.message
      );
    }
  }
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

  // Document
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

  // Video note
  if ('video_note' in ctx.message && ctx.message.video_note) {
    return {
      fileId: ctx.message.video_note.file_id,
      fileSize: ctx.message.video_note.file_size,
      mimeType: 'video/mp4',
      mediaType: 'video_note',
    };
  }

  // Voice
  if ('voice' in ctx.message && ctx.message.voice) {
    return {
      fileId: ctx.message.voice.file_id,
      fileSize: ctx.message.voice.file_size,
      mimeType: ctx.message.voice.mime_type || 'audio/ogg',
      mediaType: 'voice',
    };
  }

  // Audio
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

/**
 * Handle any media message from a group/supergroup chat.
 * Downloads the media, converts to base64, and sends to the Python backend.
 * Nanette decides naturally when to engage with media.
 */
export async function handleGroupMediaMessage(ctx: Context) {
  const fileInfo = getFileInfo(ctx);
  if (!fileInfo) return;
  if (!ctx.chat || ctx.chat.type === 'private') return;

  const caption = ('caption' in ctx.message! ? (ctx.message as any).caption : '') || '';
  const chatId = ctx.chat.id;
  const messageId = ctx.message!.message_id;
  const userId = ctx.from?.id;
  const username = ctx.from?.username || ctx.from?.first_name || 'Unknown';

  // Check if directly addressed
  const directlyAddressed = isDirectlyAddressed(ctx, caption);

  try {
    // Download the file
    const fileLink = await ctx.telegram.getFileLink(fileInfo.fileId);
    const fileResponse = await axios.get(fileLink.href, {
      responseType: 'arraybuffer',
    });
    const fileBase64 = Buffer.from(fileResponse.data).toString('base64');

    // Detect analysis mode from caption
    const analysisMode = detectAnalysisMode(caption);

    // Send to chat API with media — Nanette decides whether to engage
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: caption || '',
        conversation_history: [],
        user_id: userId ? String(userId) : null,
        channel_id: String(chatId),
        username: username,
        is_group: true,
        directly_addressed: directlyAddressed,
        image_base64: fileBase64,
        image_media_type: fileInfo.mimeType,
        file_name: fileInfo.fileName,
        file_size: fileInfo.fileSize,
        analysis_mode: analysisMode,
      },
      { timeout: 120000 }
    );

    const result = response.data;

    // Only reply if Nanette decided to respond
    if (result.response && result.should_respond !== false) {
      await ctx.reply(result.response, {
        parse_mode: 'Markdown',
        reply_parameters: {
          message_id: messageId,
        },
      });
    }
  } catch (error: any) {
    // Silently fail for group messages
    if (error.code !== 'ECONNREFUSED') {
      console.error(
        `Channel ${fileInfo.mediaType} processing error (chat ${chatId}):`,
        error.message
      );
    }
  }
}

// Keep old function name as alias for backwards compatibility
export const handleGroupImageMessage = handleGroupMediaMessage;
