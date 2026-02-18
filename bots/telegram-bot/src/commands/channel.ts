import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

// Store conversation history per group chat (keyed by chat ID)
const groupConversationHistory = new Map<number, any[]>();

// Periodically clean up stale group histories to avoid memory leaks
setInterval(() => {
  if (groupConversationHistory.size > 200) {
    groupConversationHistory.clear();
  }
}, 30 * 60 * 1000); // every 30 minutes

/**
 * Check if Nanette is directly addressed (must always respond)
 */
function isDirectlyAddressed(ctx: Context, text: string): boolean {
  const lowerText = text.toLowerCase();

  // Name mentions (full name or nickname)
  if (lowerText.includes('nanette')) return true;
  // Check for "nan" as a standalone word (not part of another word)
  if (/\bnan\b/.test(lowerText)) return true;

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
  const messageId = ctx.message.message_id;
  const userId = ctx.from?.id;
  const username =
    ctx.from?.username || ctx.from?.first_name || 'Unknown';
  const chatTitle = 'title' in ctx.chat ? ctx.chat.title : 'Unknown Group';

  // Skip bot commands — those are handled by command handlers
  if (text.startsWith('/')) return;

  // Check if directly addressed (must respond)
  const directlyAddressed = isDirectlyAddressed(ctx, text);

  // Get conversation history for this group
  let history = groupConversationHistory.get(chatId) || [];
  if (history.length > 20) {
    history = history.slice(-20);
  }

  // Send to API — Nanette decides whether to engage
  try {
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: text,
        conversation_history: history,
        user_id: userId ? String(userId) : null,
        channel_id: String(chatId),
        channel_title: chatTitle,
        username: username,
        message_id: String(messageId),
        is_group: true,
        directly_addressed: directlyAddressed,
      },
      { timeout: 60000 }
    );

    const result = response.data;

    // Track all messages in history (with username for group context)
    history.push({ role: 'user', content: `${username}: ${text}` });

    // Only reply if Nanette decided to respond
    if (result.response && result.should_respond !== false) {
      history.push({ role: 'assistant', content: result.response });
      await ctx.reply(result.response, {
        parse_mode: 'Markdown',
        reply_parameters: {
          message_id: messageId,
        },
      });
    }

    groupConversationHistory.set(chatId, history);
  } catch (error: any) {
    if (error.code !== 'ECONNREFUSED') {
      console.error(
        `Channel message error (chat ${chatId}):`,
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
  const chatTitle = 'title' in ctx.chat ? ctx.chat.title : 'Unknown Group';

  // Check if directly addressed
  const directlyAddressed = isDirectlyAddressed(ctx, caption);

  // Get conversation history for this group
  let history = groupConversationHistory.get(chatId) || [];
  if (history.length > 20) {
    history = history.slice(-20);
  }

  // Telegram bots can only download files up to 20MB
  const MAX_FILE_SIZE = 20 * 1024 * 1024;
  if (fileInfo.fileSize && fileInfo.fileSize > MAX_FILE_SIZE) {
    // Only respond if directly addressed — skip silently for large files in groups
    if (directlyAddressed) {
      try {
        const mediaDesc = fileInfo.fileName
          ? `[sent a ${fileInfo.mediaType} file: ${fileInfo.fileName} (${(fileInfo.fileSize / 1024 / 1024).toFixed(1)}MB - too large to view)]`
          : `[sent a large ${fileInfo.mediaType} (${(fileInfo.fileSize / 1024 / 1024).toFixed(1)}MB - too large to view)]`;
        const response = await axios.post(
          `${API_URL}/chat`,
          {
            message: caption ? `${caption}\n\n${mediaDesc}` : mediaDesc,
            conversation_history: history,
            channel_id: String(chatId),
            channel_title: chatTitle,
            username: username,
            is_group: true,
            directly_addressed: true,
          },
          { timeout: 60000 }
        );
        history.push({ role: 'user', content: `${username}: [${fileInfo.mediaType}] ${caption}` });
        if (response.data.response && response.data.should_respond !== false) {
          history.push({ role: 'assistant', content: response.data.response });
          await ctx.reply(response.data.response, {
            parse_mode: 'Markdown',
            reply_parameters: { message_id: messageId },
          });
        }
        groupConversationHistory.set(chatId, history);
      } catch (err: any) {
        console.error('Error handling large file in group:', err.message);
      }
    }
    return;
  }

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
        conversation_history: history,
        user_id: userId ? String(userId) : null,
        channel_id: String(chatId),
        channel_title: chatTitle,
        username: username,
        message_id: String(messageId),
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

    // Track in history
    history.push({ role: 'user', content: `${username}: [${fileInfo.mediaType}] ${caption || ''}` });

    // Only reply if Nanette decided to respond
    if (result.response && result.should_respond !== false) {
      history.push({ role: 'assistant', content: result.response });
      await ctx.reply(result.response, {
        parse_mode: 'Markdown',
        reply_parameters: {
          message_id: messageId,
        },
      });
    }

    groupConversationHistory.set(chatId, history);
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
