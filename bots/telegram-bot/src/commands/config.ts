import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Check if user is a Telegram chat admin or the chat owner.
 * In private chats, the user is always considered admin.
 */
async function isUserAdmin(ctx: Context): Promise<boolean> {
  const chatType = ctx.chat?.type;

  // Private chats — user has full control
  if (chatType === 'private') {
    return true;
  }

  // Group/supergroup — check Telegram admin status
  try {
    const userId = ctx.from?.id;
    if (!userId) return false;

    const member = await ctx.telegram.getChatMember(ctx.chat!.id, userId);
    return member.status === 'creator' || member.status === 'administrator';
  } catch {
    return false;
  }
}

/**
 * /nanette_config command — admin-only server configuration
 *
 * Usage:
 *   /nanette_config                — Show current settings
 *   /nanette_config enable <cat>   — Enable a feature category
 *   /nanette_config disable <cat>  — Disable a feature category
 *   /nanette_config cooldown <sec> — Set response cooldown
 *   /nanette_config admin add <id> — Add a Nanette admin
 *   /nanette_config admin remove <id> — Remove a Nanette admin
 *
 * Categories: analysis, interactions, chat, fun, crypto,
 *             auto_respond, channel_analysis, clues
 */
export async function configCommand(ctx: Context) {
  // Admin check
  const isAdmin = await isUserAdmin(ctx);
  if (!isAdmin) {
    return ctx.reply(
      'Only chat owners and admins can configure my settings.'
    );
  }

  const text = ctx.message && 'text' in ctx.message ? ctx.message.text : '';
  const args = text.split(/\s+/).slice(1);
  const chatId = String(ctx.chat?.id || '');
  const userId = String(ctx.from?.id || '');
  const chatTitle = ctx.chat && 'title' in ctx.chat ? ctx.chat.title : 'Private';

  // Determine owner — for groups, try to get creator
  let ownerId = userId;
  if (ctx.chat?.type !== 'private') {
    try {
      const admins = await ctx.telegram.getChatAdministrators(ctx.chat!.id);
      const creator = admins.find(a => a.status === 'creator');
      if (creator) {
        ownerId = String(creator.user.id);
      }
    } catch {
      // Fall back to current user
    }
  }

  // No args — show current config
  if (args.length === 0) {
    return showConfig(ctx, chatId, userId, chatTitle, ownerId);
  }

  const action = args[0].toLowerCase();

  // Enable / disable
  if (action === 'enable' || action === 'disable') {
    const target = args[1];
    if (!target) {
      return ctx.reply(
        `Usage: /nanette_config ${action} <category>\n\n` +
        'Categories: analysis, interactions, chat, fun, crypto, ' +
        'auto_respond, channel_analysis, clues'
      );
    }

    try {
      // Ensure config exists first
      await axios.post(`${API_URL}/config/get`, {
        server_id: chatId,
        platform: 'telegram',
        user_id: userId,
        server_name: chatTitle,
        owner_id: ownerId,
      });

      const response = await axios.post(`${API_URL}/config/update`, {
        server_id: chatId,
        platform: 'telegram',
        user_id: userId,
        action: action,
        target: target.toLowerCase(),
      });

      if (response.data.success) {
        const state = action === 'enable' ? 'enabled' : 'disabled';
        return ctx.reply(`${target} has been ${state}.`);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        return ctx.reply('Only server owners and admins can change settings.');
      }
      console.error('Config update error:', error);
      return ctx.reply('Something went wrong updating the config.');
    }
  }

  // Cooldown
  if (action === 'cooldown') {
    const seconds = parseInt(args[1]);
    if (isNaN(seconds) || seconds < 0) {
      return ctx.reply(
        'Usage: /nanette_config cooldown <seconds>\n' +
        'Example: /nanette_config cooldown 300'
      );
    }

    try {
      await axios.post(`${API_URL}/config/get`, {
        server_id: chatId,
        platform: 'telegram',
        user_id: userId,
        server_name: chatTitle,
        owner_id: ownerId,
      });

      await axios.post(`${API_URL}/config/update`, {
        server_id: chatId,
        platform: 'telegram',
        user_id: userId,
        action: 'cooldown',
        target: String(seconds),
        value: String(seconds),
      });

      return ctx.reply(`Response cooldown set to ${seconds} seconds.`);
    } catch (error: any) {
      if (error.response?.status === 403) {
        return ctx.reply('Only server owners and admins can change settings.');
      }
      return ctx.reply('Something went wrong updating the cooldown.');
    }
  }

  // Admin management
  if (action === 'admin') {
    const subAction = args[1]?.toLowerCase();
    const targetId = args[2];

    if (!subAction || !targetId || !['add', 'remove'].includes(subAction)) {
      return ctx.reply(
        'Usage:\n' +
        '/nanette_config admin add <user_id>\n' +
        '/nanette_config admin remove <user_id>'
      );
    }

    try {
      await axios.post(`${API_URL}/config/get`, {
        server_id: chatId,
        platform: 'telegram',
        user_id: userId,
        server_name: chatTitle,
        owner_id: ownerId,
      });

      await axios.post(`${API_URL}/config/update`, {
        server_id: chatId,
        platform: 'telegram',
        user_id: userId,
        action: subAction === 'add' ? 'add_admin' : 'remove_admin',
        target: targetId,
      });

      const verb = subAction === 'add' ? 'added as' : 'removed from';
      return ctx.reply(`User ${targetId} ${verb} Nanette admin.`);
    } catch (error: any) {
      if (error.response?.status === 403) {
        return ctx.reply('Only server owners and admins can manage admins.');
      }
      return ctx.reply('Something went wrong updating admins.');
    }
  }

  // Unknown action
  return ctx.reply(
    'Usage:\n' +
    '/nanette_config — Show settings\n' +
    '/nanette_config enable <category>\n' +
    '/nanette_config disable <category>\n' +
    '/nanette_config cooldown <seconds>\n' +
    '/nanette_config admin add <user_id>\n' +
    '/nanette_config admin remove <user_id>\n\n' +
    'Categories: analysis, interactions, chat, fun, crypto, ' +
    'auto_respond, channel_analysis, clues'
  );
}


async function showConfig(
  ctx: Context,
  chatId: string,
  userId: string,
  chatTitle: string,
  ownerId: string
) {
  try {
    const response = await axios.post(`${API_URL}/config/get`, {
      server_id: chatId,
      platform: 'telegram',
      user_id: userId,
      server_name: chatTitle,
      owner_id: ownerId,
    });

    const c = response.data;
    const on = '✅';
    const off = '❌';

    const msg = `*Nanette Configuration*\n` +
      `Chat: ${chatTitle}\n\n` +
      `*Feature Controls*\n` +
      `${c.allow_analysis ? on : off} Analysis (/analyze)\n` +
      `${c.allow_interactions ? on : off} Interactions (/interactions)\n` +
      `${c.allow_chat ? on : off} Chat (conversation)\n` +
      `${c.allow_fun ? on : off} Fun commands\n` +
      `${c.allow_crypto_data ? on : off} Crypto data (price, gas, etc.)\n` +
      `${c.auto_respond ? on : off} Auto-respond in groups\n` +
      `${c.channel_analysis_enabled ? on : off} Channel analysis\n` +
      `${c.rin_clue_detection ? on : off} RIN clue detection\n\n` +
      `*Settings*\n` +
      `Response cooldown: ${c.response_cooldown}s\n` +
      `Admins: ${c.admin_ids?.length || 0}\n\n` +
      `_Use /nanette\\_config enable|disable <category> to change._`;

    return ctx.reply(msg, { parse_mode: 'Markdown' });

  } catch (error: any) {
    console.error('Error fetching config:', error);
    return ctx.reply('Could not load configuration.');
  }
}
