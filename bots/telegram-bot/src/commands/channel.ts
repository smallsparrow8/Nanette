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
