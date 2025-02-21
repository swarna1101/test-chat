import asyncio
import contextlib
import threading

import google.generativeai as genai
import structlog
from google.api_core.exceptions import InvalidArgument, NotFound

from flare_ai_social.ai import BaseAIProvider, GeminiProvider
from flare_ai_social.prompts import FEW_SHOT_PROMPT
from flare_ai_social.settings import settings
from flare_ai_social.telegram import TelegramBot
from flare_ai_social.twitter import TwitterBot

logger = structlog.get_logger(__name__)


class BotManager:
    """Manager class for handling multiple social media bots."""

    def __init__(self) -> None:
        """Initialize the BotManager."""
        self.ai_provider: BaseAIProvider | None = None
        self.telegram_bot: TelegramBot | None = None
        self.twitter_thread: threading.Thread | None = None
        self.active_bots: list[str] = []
        self.running = False

    def initialize_ai_provider(self) -> None:
        """Initialize the AI provider with either tuned model or default model."""
        genai.configure(api_key=settings.gemini_api_key)
        tuned_model_id = settings.tuned_model_name

        try:
            # Check available tuned models
            tuned_models = [m.name for m in genai.list_tuned_models()]
            logger.info("Available tuned models", tuned_models=tuned_models)

            # Try to get tuned model if it exists
            if tuned_models and any(tuned_model_id in model for model in tuned_models):
                try:
                    model_info = genai.get_tuned_model(
                        name=f"tunedModels/{tuned_model_id}"
                    )
                    logger.info("Tuned model info", model_info=model_info)

                    # Initialize AI provider with tuned model
                    self.ai_provider = GeminiProvider(
                        settings.gemini_api_key,
                        model_name=f"tunedModels/{tuned_model_id}",
                        system_instruction=FEW_SHOT_PROMPT,
                    )
                    logger.info(f"Using tuned model: tunedModels/{tuned_model_id}")
                    return
                except (InvalidArgument, NotFound) as e:
                    logger.warning(f"Failed to load tuned model: {e}")
            else:
                logger.warning(
                    f"Tuned model '{tuned_model_id}' not found in available models. Using default model."
                )
        except Exception as e:
            logger.exception(f"Error accessing tuned models: {e}")

        # Fall back to default model
        logger.info("Using default Gemini Flash model with few-shot prompting")
        self.ai_provider = GeminiProvider(
            settings.gemini_api_key,
            model_name="gemini-1.5-flash",
            system_instruction=FEW_SHOT_PROMPT,
        )

    def start_twitter_bot(self) -> bool:
        """Initialize and start the Twitter bot in a separate thread."""
        # Check if Twitter is enabled in settings
        if not settings.enable_twitter:
            logger.info("Twitter bot disabled in settings")
            return False

        # Check if required Twitter credentials are configured
        if not all(
            [
                settings.x_api_key,
                settings.x_api_key_secret,
                settings.x_access_token,
                settings.x_access_token_secret,
            ]
        ):
            logger.error(
                "Twitter bot not started: Missing required credentials. "
                "Please configure Twitter API credentials in settings."
            )
            return False

        try:
            # Ensure AI provider is initialized
            assert self.ai_provider is not None, "AI provider must be initialized"
            twitter_bot = TwitterBot(
                ai_provider=self.ai_provider,
                bearer_token=settings.x_bearer_token,
                api_key=settings.x_api_key,
                api_secret=settings.x_api_key_secret,
                access_token=settings.x_access_token,
                access_secret=settings.x_access_token_secret,
                rapidapi_key=settings.rapidapi_key or "",
                rapidapi_host=settings.rapidapi_host,
                accounts_to_monitor=settings.accounts_to_monitor,
                polling_interval=settings.twitter_polling_interval,
            )

            # Start the Twitter bot in a separate thread
            self.twitter_thread = threading.Thread(
                target=twitter_bot.start, daemon=True, name="TwitterBotThread"
            )
            self.twitter_thread.start()
            logger.info("Twitter bot started in background thread")
            self.active_bots.append("Twitter")
            return True

        except ValueError as e:
            logger.exception(f"Failed to start Twitter bot: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error starting Twitter bot: {e}", exc_info=True)
            return False

    async def start_telegram_bot(self) -> bool:
        """Initialize and start the Telegram bot."""
        # Check if Telegram is enabled in settings
        if not settings.enable_telegram:
            logger.info("Telegram bot disabled in settings")
            return False

        if not settings.telegram_api_token:
            logger.warning("Telegram bot not started: Missing API token")
            return False

        try:
            # Parse allowed users if provided
            allowed_users: list[int] = []
            if settings.telegram_allowed_users:
                try:
                    # Convert comma-separated string to list of integers
                    allowed_users = [
                        int(user_id.strip())
                        for user_id in settings.telegram_allowed_users.split(",")
                        if user_id.strip().isdigit()
                    ]
                except Exception as e:
                    logger.warning(f"Error parsing telegram_allowed_users: {e}")

            # Ensure AI provider is initialized
            assert self.ai_provider is not None, "AI provider must be initialized"

            # Create and start Telegram bot
            self.telegram_bot = TelegramBot(
                ai_provider=self.ai_provider,
                api_token=settings.telegram_api_token,
                allowed_user_ids=allowed_users,
                polling_interval=settings.telegram_polling_interval,
            )

            # Properly initialize and start polling
            await self.telegram_bot.initialize()
            await self.telegram_bot.start_polling()
            self.active_bots.append("Telegram")
            return True

        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}", exc_info=True)
            return False

    async def monitor_bots(self) -> None:
        """Monitor active bots and handle unexpected terminations."""
        self.running = True
        try:
            while self.running and self.active_bots:
                # Check Twitter bot status
                if "Twitter" in self.active_bots and self.twitter_thread:
                    if not self.twitter_thread.is_alive():
                        logger.error("Twitter bot thread terminated unexpectedly")
                        self.active_bots.remove("Twitter")
                        # Attempt to restart Twitter if auto-restart is enabled
                        if getattr(settings, "auto_restart_bots", False):
                            logger.info("Attempting to restart Twitter bot")
                            if self.start_twitter_bot():
                                logger.info("Twitter bot restarted successfully")

                # Exit if no bots are active anymore
                if not self.active_bots:
                    logger.error("No active bots remaining")
                    break

                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error in bot monitoring loop: {e}", exc_info=True)
        finally:
            self.running = False

    async def shutdown(self) -> None:
        """Gracefully shutdown all active bots."""
        self.running = False

        # Shutdown Telegram bot if active
        if self.telegram_bot:
            try:
                logger.info("Shutting down Telegram bot")
                await self.telegram_bot.shutdown()
            except Exception as e:
                logger.exception(f"Error shutting down Telegram bot: {e}")

        if "Twitter" in self.active_bots:
            logger.info("Twitter bot daemon thread will terminate with main process")

        logger.info("All bots shutdown completed")


async def async_start() -> None:
    """Initialize and start all components of the application asynchronously."""
    bot_manager = BotManager()

    try:
        # Initialize AI provider
        bot_manager.initialize_ai_provider()
        if not bot_manager.ai_provider:
            logger.error("Failed to initialize AI provider")
            return

        # Start Twitter bot (if enabled and configured)
        bot_manager.start_twitter_bot()

        # Start Telegram bot (if enabled and configured)
        await bot_manager.start_telegram_bot()

        if bot_manager.active_bots:
            logger.info(f"Active bots: {', '.join(bot_manager.active_bots)}")
            monitor_task = asyncio.create_task(bot_manager.monitor_bots())

            try:
                while bot_manager.active_bots:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Main task cancelled")
            finally:
                monitor_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await monitor_task

                await bot_manager.shutdown()
        else:
            logger.info(
                "No bots active. Configure Twitter and/or Telegram credentials "
                "and enable them in settings to activate social monitoring."
            )
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        await bot_manager.shutdown()
    except Exception as e:
        logger.error(f"Fatal error in async_start: {e}", exc_info=True)
        await bot_manager.shutdown()


def start_bot_manager() -> None:
    """Initialize and start all components of the application."""
    try:
        asyncio.run(async_start())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in start: {e}", exc_info=True)
