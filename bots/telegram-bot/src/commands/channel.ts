import { Context } from 'telegraf';
import axios from 'axios';
import { isUserAdmin } from '../utils/adminCache';

const API_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Check if a message warrants Nanette's engagement
 * Returns engagement level: 'direct' (always respond), 'natural' (contextual), or null
 */
function detectEngagement(ctx: Context, text: string): 'direct' | 'natural' | null {
  const lowerText = text.toLowerCase();

  // DIRECT ENGAGEMENT — always respond
  // Name mentions
  if (lowerText.includes('nanette')) return 'direct';

  // @mention of the bot
  const botUsername = ctx.botInfo?.username?.toLowerCase();
  if (botUsername && lowerText.includes(`@${botUsername}`)) return 'direct';

  // Reply to Nanette's message
  const msg = ctx.message as any;
  if (msg?.reply_to_message?.from?.is_bot) {
    const replyToBotId = msg.reply_to_message.from.id;
    if (replyToBotId === ctx.botInfo?.id) return 'direct';
  }

  // NATURAL ENGAGEMENT — join conversation naturally
  const isQuestion = text.includes('?') ||
    /^(who|what|where|when|why|how|is|are|can|should|does|do|will|would)\b/i.test(text.trim());

  // Questions about crypto/blockchain topics
  const cryptoTerms = [
    'crypto', 'blockchain', 'defi', 'nft', 'web3',
    'contract', 'token', 'wallet', 'address', 'scam', 'rug',
    'honeypot', 'liquidity', 'dex', 'swap', 'eth', 'sol', 'btc',
    'safe', 'legit', 'trust', 'audit', 'verify', 'check',
    '0x', 'ca ', 'mint', 'airdrop', 'presale', 'launch',
    'price', 'pump', 'dump', 'moon', 'bear', 'bull',
    'rin', '$rin', 'rintintin',
  ];

  if (isQuestion && cryptoTerms.some(term => lowerText.includes(term))) {
    return 'natural';
  }

  // Any question directed at the conversation (general engagement)
  if (isQuestion) {
    return 'natural';
  }

  // Contract addresses posted (likely wanting analysis)
  if (/0x[a-fA-F0-9]{40}/.test(text)) {
    return 'natural';
  }

  // Social engagement / greetings directed at conversation
  if (/\b(welcome|hello|hi|hey|gm|gn|good morning|good night|thanks|thank you)\b/i.test(text)) {
    return 'natural';
  }

  return null;
}

/**
 * Handle a text message from a group/supergroup chat.
 * Routes messages directed at Nanette to the chat API for response.
 * Other messages go to channel analysis for logging/monitoring.
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

  // Detect engagement level
  const engagement = detectEngagement(ctx, text);

  if (engagement) {
    // Engage with the conversation
    try {
      // For natural engagement, add context hint so Nanette responds conversationally
      const messageToSend = engagement === 'natural'
        ? `[Group conversation - join naturally if you can help]\n${text}`
        : text;

      const response = await axios.post(
        `${API_URL}/chat`,
        {
          message: messageToSend,
          conversation_history: [],
          user_id: userId ? String(userId) : null,
          channel_id: String(chatId),
        },
        { timeout: 60000 }
      );

      const result = response.data;

      if (result.response) {
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
          `Channel direct message error (chat ${chatId}):`,
          error.message
        );
      }
    }
    return;
  }

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
 * Only responds when directly engaged (name in caption, reply to bot, @mention).
 */
export async function handleGroupMediaMessage(ctx: Context) {
  const fileInfo = getFileInfo(ctx);
  if (!fileInfo) return;
  if (!ctx.chat || ctx.chat.type === 'private') return;

  const caption = ('caption' in ctx.message! ? (ctx.message as any).caption : '') || '';
  const chatId = ctx.chat.id;
  const messageId = ctx.message!.message_id;
  const userId = ctx.from?.id;

  // Only respond if there's engagement (direct or natural)
  const engagement = detectEngagement(ctx, caption);
  if (!engagement) {
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

    // Send to chat API with media
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: caption || '',
        conversation_history: [],
        user_id: userId ? String(userId) : null,
        channel_id: String(chatId),
        image_base64: fileBase64,
        image_media_type: fileInfo.mimeType,
        file_name: fileInfo.fileName,
        file_size: fileInfo.fileSize,
        analysis_mode: analysisMode,
      },
      { timeout: 120000 }
    );

    const result = response.data;

    if (result.response) {
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
