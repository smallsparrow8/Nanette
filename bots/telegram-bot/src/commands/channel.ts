import { Context } from 'telegraf';
import axios from 'axios';
import { isUserAdmin } from '../utils/adminCache';

const API_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Handle a text message from a group/supergroup chat.
 * Sends the message to the Python backend for analysis.
 * If the backend decides Nanette should respond, sends her response.
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

  // Only respond when directly engaged:
  // - Someone says "Nanette" (natural conversation)
  // - Someone replies to one of Nanette's messages
  // - Someone @mentions the bot
  const botUsername = ctx.botInfo?.username?.toLowerCase();
  const textLower = text.toLowerCase();
  const isNameMentioned = textLower.includes('nanette');
  const isBotMentioned = botUsername && textLower.includes(`@${botUsername}`);
  const isReplyToBot = ctx.message.reply_to_message?.from?.id === ctx.botInfo?.id;

  if (!isNameMentioned && !isBotMentioned && !isReplyToBot) return;

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

    // If Nanette should respond, send her message
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
    // with error messages
    if (error.code !== 'ECONNREFUSED') {
      console.error(
        `Channel message processing error (chat ${chatId}):`,
        error.message
      );
    }
  }
}

/**
 * Handle a photo message from a group/supergroup chat.
 * Downloads the image, converts to base64, and sends to the Python backend.
 * Only responds when directly engaged (name in caption, reply to bot, @mention).
 */
export async function handleGroupImageMessage(ctx: Context) {
  if (!ctx.message || !('photo' in ctx.message)) return;
  if (!ctx.chat || ctx.chat.type === 'private') return;

  const caption = ('caption' in ctx.message ? ctx.message.caption : '') || '';
  const chatId = ctx.chat.id;
  const chatTitle = 'title' in ctx.chat ? ctx.chat.title : undefined;
  const chatType = ctx.chat.type;
  const messageId = ctx.message.message_id;
  const userId = ctx.from?.id;
  const username =
    ctx.from?.username || ctx.from?.first_name || 'Unknown';

  // Only respond when directly engaged:
  // - Caption contains "Nanette" (natural conversation)
  // - Someone replies to one of Nanette's messages with a photo
  // - Caption @mentions the bot
  const botUsername = ctx.botInfo?.username?.toLowerCase();
  const captionLower = caption.toLowerCase();
  const isNameMentioned = captionLower.includes('nanette');
  const isBotMentioned = botUsername && captionLower.includes(`@${botUsername}`);
  const isReplyToBot = ctx.message.reply_to_message?.from?.id === ctx.botInfo?.id;

  if (!isNameMentioned && !isBotMentioned && !isReplyToBot) return;

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

    // Send to chat API with image (reuse /chat endpoint for vision)
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: caption || '',
        conversation_history: [],
        user_id: userId ? String(userId) : null,
        channel_id: String(chatId),
        image_base64: imageBase64,
        image_media_type: 'image/jpeg',
      },
      { timeout: 90000 }
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
        `Channel image processing error (chat ${chatId}):`,
        error.message
      );
    }
  }
}
