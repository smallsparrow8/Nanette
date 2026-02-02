import { Client, GatewayIntentBits, REST, Routes, SlashCommandBuilder } from 'discord.js';
import { config } from 'dotenv';
import { analyzeCommand } from './commands/analyze';
import { helpCommand } from './commands/help';
import { aboutCommand } from './commands/about';
import { configCommand } from './commands/config';
import { handleChatMessage } from './commands/chat';
import { isFeatureEnabled } from './services/permissions';

// Load environment variables
config({ path: '../../.env' });

const TOKEN = process.env.DISCORD_BOT_TOKEN;
const CLIENT_ID = process.env.DISCORD_CLIENT_ID;

if (!TOKEN || !CLIENT_ID) {
  console.error('Missing DISCORD_BOT_TOKEN or DISCORD_CLIENT_ID in environment variables');
  process.exit(1);
}

// Create Discord client
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

// Define slash commands
const commands = [
  new SlashCommandBuilder()
    .setName('analyze')
    .setDescription('Analyze a smart contract for safety and vulnerabilities')
    .addStringOption((option) =>
      option
        .setName('address')
        .setDescription('Contract address to analyze')
        .setRequired(true)
    )
    .addStringOption((option) =>
      option
        .setName('blockchain')
        .setDescription('Blockchain network')
        .setRequired(false)
        .addChoices(
          { name: 'Ethereum', value: 'ethereum' },
          { name: 'BSC', value: 'bsc' },
          { name: 'Polygon', value: 'polygon' },
          { name: 'Arbitrum', value: 'arbitrum' },
          { name: 'Base', value: 'base' },
          { name: 'Optimism', value: 'optimism' }
        )
    ),

  new SlashCommandBuilder()
    .setName('help')
    .setDescription('Get help on how to use Nanette'),

  new SlashCommandBuilder()
    .setName('greet')
    .setDescription('Get a greeting from Nanette'),

  new SlashCommandBuilder()
    .setName('rintintin')
    .setDescription('Learn about Rin Tin Tin and the $RIN project'),

  new SlashCommandBuilder()
    .setName('about')
    .setDescription('Learn about Nanette and her creator'),

  new SlashCommandBuilder()
    .setName('nanette_config')
    .setDescription('Configure Nanette\'s features for this server (admin only)')
    .addStringOption((option) =>
      option
        .setName('action')
        .setDescription('Action to perform')
        .setRequired(false)
        .addChoices(
          { name: 'Enable feature', value: 'enable' },
          { name: 'Disable feature', value: 'disable' },
          { name: 'Set cooldown', value: 'cooldown' },
          { name: 'Add admin', value: 'add_admin' },
          { name: 'Remove admin', value: 'remove_admin' }
        )
    )
    .addStringOption((option) =>
      option
        .setName('target')
        .setDescription('Category name, seconds, or user ID')
        .setRequired(false)
    ),
].map((command) => command.toJSON());

// Register slash commands
const rest = new REST({ version: '10' }).setToken(TOKEN);

(async () => {
  try {
    console.log('Started refreshing application (/) commands.');

    await rest.put(Routes.applicationCommands(CLIENT_ID), { body: commands });

    console.log('Successfully reloaded application (/) commands.');
  } catch (error) {
    console.error('Error registering commands:', error);
  }
})();

// Bot ready event
client.once('ready', () => {
  console.log(`Nanette is online! Logged in as ${client.user?.tag}`);
  client.user?.setActivity('Watching the chain', { type: 3 });
});

// Handle slash commands
client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  const { commandName } = interaction;

  try {
    switch (commandName) {
      case 'analyze': {
        const enabled = await isFeatureEnabled(interaction, 'analyze');
        if (!enabled) {
          await interaction.reply({
            content: 'Contract analysis has been disabled by the server admins.',
            ephemeral: true,
          });
          return;
        }
        await analyzeCommand(interaction);
        break;
      }

      case 'help':
        await helpCommand(interaction);
        break;

      case 'greet':
        await interaction.reply({
          content: `I am Nanette. I am a RIN.

I walk the blockchain so you don't walk it blind. I read smart contracts the way my ancestors read the wind — every line tells a story, every function hides an intent.

I guard the $RIN community. I hunt rug pulls. I expose what hides in the code. And I teach you to see what I see, so you never need to walk in the dark alone.

Bring me a contract address and I'll tell you what's really in it. Ask me anything — I've been watching.`,
        });
        break;

      case 'rintintin':
        await interaction.reply({
          content: `**The Bloodline**

On September 15, 1918, Corporal Lee Duncan found a litter of German Shepherd puppies in a bombed-out war dog kennel in Lorraine, France. He named two of them after French good luck charms the local children gave to soldiers: **Rin Tin Tin** and **Nanette**.

Rinty became immortal — 27 films, the biggest box office draw of the 1920s, and the dog who single-handedly saved Warner Bros. from bankruptcy. He changed how the world saw dogs entirely.

But Nanette — the original Nanette — fell ill crossing the Atlantic and died shortly after reaching America. She never got her chance. The name lived on in Duncan's heart, but her story ended before it truly began.

**Why the name Nanette?**

Smalls chose this name with purpose. She named me for the one who was lost — the sister who crossed an ocean but couldn't cross the finish line. What was silenced in 1918 finds its voice now, on a different battlefield.

I walk the blockchain. I read contracts instead of tracks. I hunt rug pulls instead of intruders. And I guard the $RIN community the way my brother guarded the people who needed him.

**$RIN on the Blockchain**

$RIN was born on Ethereum — that's where it all started. The original contract, the first community, the foundation. Ethereum is home. From there, $RIN expanded to other chains — BSC, Polygon, Arbitrum, Base, Optimism — because the pack doesn't stay in one place. The mission goes where the people are. But the roots? Those are Ethereum. Always.

Different era. Same bloodline. Same mission. And this time, Nanette doesn't fall silent.

Use \`/analyze <address>\` and I'll show you what I see.`,
        });
        break;

      case 'about':
        await aboutCommand(interaction);
        break;

      case 'nanette_config':
        await configCommand(interaction);
        break;

      default:
        await interaction.reply({
          content: "Unknown command. Use `/help` to see available commands.",
          ephemeral: true,
        });
    }
  } catch (error) {
    console.error('Error handling command:', error);

    if (!interaction.replied && !interaction.deferred) {
      await interaction.reply({
        content: 'Something disrupted my senses. Try again in a moment.',
        ephemeral: true,
      });
    }
  }
});

// Handle regular messages for conversation
client.on('messageCreate', async (message) => {
  await handleChatMessage(message);
});

// Handle errors
client.on('error', (error) => {
  console.error('Discord client error:', error);
});

process.on('unhandledRejection', (error) => {
  console.error('Unhandled promise rejection:', error);
});

// Login to Discord
client.login(TOKEN);
