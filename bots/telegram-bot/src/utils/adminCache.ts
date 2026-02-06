import { Telegram } from 'telegraf';

interface CacheEntry {
  adminIds: Set<string>;
  fetchedAt: number;
}

const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes

const cache = new Map<string, CacheEntry>();

/**
 * Get the set of admin user IDs for a chat.
 * Results are cached for 10 minutes to avoid rate limits.
 */
export async function getChatAdminIds(
  telegram: Telegram,
  chatId: number | string
): Promise<Set<string>> {
  const key = String(chatId);
  const now = Date.now();

  const cached = cache.get(key);
  if (cached && now - cached.fetchedAt < CACHE_TTL_MS) {
    return cached.adminIds;
  }

  try {
    const admins = await telegram.getChatAdministrators(chatId);
    const adminIds = new Set(
      admins.map((a) => String(a.user.id))
    );

    cache.set(key, { adminIds, fetchedAt: now });
    return adminIds;
  } catch (error: any) {
    // Handle group -> supergroup migration
    // Telegram returns migrate_to_chat_id when a group is upgraded
    const migrateId = error?.parameters?.migrate_to_chat_id;
    if (migrateId) {
      try {
        const admins = await telegram.getChatAdministrators(migrateId);
        const adminIds = new Set(
          admins.map((a) => String(a.user.id))
        );
        // Cache under both old and new IDs
        cache.set(key, { adminIds, fetchedAt: now });
        cache.set(String(migrateId), { adminIds, fetchedAt: now });
        return adminIds;
      } catch (retryError) {
        // Migration retry failed, fall through to default handling
      }
    }

    // Only log non-migration errors (migration is expected during upgrades)
    if (!migrateId) {
      console.error(`Failed to fetch admins for chat ${key}:`, error);
    }

    // Return cached data if available, even if stale
    if (cached) {
      return cached.adminIds;
    }
    return new Set();
  }
}

/**
 * Check if a user is an admin in a specific chat.
 */
export async function isUserAdmin(
  telegram: Telegram,
  chatId: number | string,
  userId: number | string
): Promise<boolean> {
  const adminIds = await getChatAdminIds(telegram, chatId);
  return adminIds.has(String(userId));
}

/**
 * Clear the admin cache for a specific chat or all chats.
 */
export function clearAdminCache(chatId?: string): void {
  if (chatId) {
    cache.delete(chatId);
  } else {
    cache.clear();
  }
}
