import asyncio
import sys
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from app.config import Settings, load_yaml
from app.ai.generator import AIGenerator
from app.bot.handlers import MessageHandler
from app.services.storage import LeadStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("trading_setter")

def main():
    settings = Settings()

    # Validate required settings
    if not settings.API_ID or not settings.API_HASH:
        logger.error("API_ID and API_HASH are required in .env")
        sys.exit(1)
    if not settings.SESSION_STRING and not settings.SESSION_NAME:
        logger.error("SESSION_STRING or SESSION_NAME is required in .env")
        sys.exit(1)

    # Load all YAML configs
    configs = {
        "app": load_yaml("app.yaml"),
        "roles": load_yaml("roles.yaml"),
        "scripts": load_yaml("scripts.yaml").get("scripts", {}),
        "scoring": load_yaml("scoring.yaml").get("scoring", {}),
        "routing": load_yaml("routing.yaml").get("routing", {}),
        "prompts": load_yaml("prompts.yaml"),
    }

    logger.info("Config loaded: %s", list(configs.keys()))

    # Initialize storage
    store = LeadStore(settings.DATABASE_URL)
    logger.info("Storage initialized: %s", settings.DATABASE_URL)

    # Initialize AI generator if API key is provided
    ai = None
    if settings.LLM_API_KEY:
        ai = AIGenerator(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            system_prompt=configs["prompts"].get("system_prompt", ""),
            max_output_tokens=configs["app"].get("ai", {}).get("max_output_tokens", 400),
            temperature=configs["app"].get("ai", {}).get("temperature", 0.4),
        )
        logger.info("AI generator initialized: %s via %s", settings.LLM_MODEL, settings.LLM_BASE_URL)
    else:
        logger.warning("No LLM_API_KEY - running in fallback mode (no AI)")

    # Create Telegram client
    if settings.SESSION_STRING:
        client = TelegramClient(
            StringSession(settings.SESSION_STRING),
            int(settings.API_ID),
            settings.API_HASH,
        )
    else:
        client = TelegramClient(
            settings.SESSION_NAME,
            int(settings.API_ID),
            settings.API_HASH,
        )

    # Initialize message handler
    msg_handler = MessageHandler(client, configs, ai, store)

    @client.on(events.NewMessage(incoming=True))
    async def event_handler(event):
        try:
            await msg_handler.handle_new_message(event)
        except Exception as e:
            logger.exception("Error handling message")

    async def run():
        await client.start()
        me = await client.get_me()
        logger.info(
            "🤖 Bot started as %s (@%s, ID: %s)",
            me.first_name,
            me.username,
            me.id,
        )
        logger.info(
            "📢 Forwarding hot leads to channel: %s",
            configs.get("app", {}).get("bot", {}).get("forward_channel_link", "NOT SET"),
        )

        # Send startup notification to channel
        try:
            channel_link = configs.get("app", {}).get("bot", {}).get("forward_channel_link")
            if channel_link:
                channel_entity = await client.get_entity(channel_link)
                await client.send_message(
                    channel_entity,
                    "🟢 **Bot Trading Setter démarré**\n"
                    f"Compte : {me.first_name} (@{me.username})\n"
                    f"IA : {'✅ Active' if ai else '❌ Fallback'}\n"
                    f"⏰ {__import__('datetime').datetime.now().strftime('%H:%M %d/%m/%Y')}",
                    parse_mode="md",
                )
                logger.info("Startup notification sent to channel: %s", channel_link)
        except Exception as e:
            logger.warning("Could not send startup notification: %s", e)

        await client.run_until_disconnected()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)

if __name__ == "__main__":
    main()