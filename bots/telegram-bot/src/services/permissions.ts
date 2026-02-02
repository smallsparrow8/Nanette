import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Check if a feature is enabled for the current chat.
 * Returns true if no config exists (default: all enabled).
 * Returns true for private chats (no restrictions in DMs).
 */
export async function isFeatureEnabled(
  ctx: Context,
  feature: string
): Promise<boolean> {
  // Private chats — all features enabled
  if (ctx.chat?.type === 'private') {
    return true;
  }

  const chatId = String(ctx.chat?.id || '');
  if (!chatId) return true;

  try {
    const response = await axios.post(
      `${API_URL}/config/check-feature`,
      {
        server_id: chatId,
        platform: 'telegram',
        feature: feature,
      },
      { timeout: 5000 }
    );

    return response.data.enabled !== false;
  } catch {
    // If API is down or errors, allow feature (fail open)
    return true;
  }
}

/**
 * Middleware wrapper that checks feature permissions before
 * executing a command handler.
 *
 * Usage:
 *   bot.command('analyze', withPermission('analyze', analyzeCommand));
 */
export function withPermission(
  feature: string,
  handler: (ctx: Context) => Promise<any>
) {
  return async (ctx: Context) => {
    const enabled = await isFeatureEnabled(ctx, feature);

    if (!enabled) {
      return ctx.reply(
        `That command has been disabled by the admins of this chat.`
      );
    }

    return handler(ctx);
  };
}
