import asyncio
import time

import structlog
from telegram import Bot, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from flare_ai_social.ai import BaseAIProvider

logger = structlog.get_logger(__name__)


class TelegramBot:
    def __init__(
        self,
        ai_provider: BaseAIProvider,
        api_token: str,
        allowed_user_ids: list[int] | None = None,
        polling_interval: int = 5,
    ) -> None:
        """
        Initialize the Telegram bot.

        Args:
            ai_provider: The AI provider to use for generating responses
            api_token: Telegram Bot API token
            allowed_user_ids: Optional list of allowed Telegram user IDs (for access control).
                              If empty or None, all users are allowed.
            polling_interval: Time between update checks in seconds
        """
        self.ai_provider = ai_provider
        self.api_token = api_token
        self.allowed_user_ids = (
            allowed_user_ids or []
        )  # Empty list means no restrictions
        self.polling_interval = polling_interval
        self.application = None
        self.me = None  # Will store bot's own information

        # Track last processed update time for each chat
        self.last_processed_time: dict[int, float] = {}

        # Check required credentials
        if not self.api_token:
            msg = "Telegram API token not provided. Please check your settings."
            raise ValueError(msg)

        # Log initialization with appropriate message about access control
        if self.allowed_user_ids:
            logger.info(
                "TelegramBot initialized with access restrictions",
                allowed_users_count=len(self.allowed_user_ids),
                polling_interval=polling_interval,
            )
        else:
            logger.info(
                "TelegramBot initialized without access restrictions (public bot)",
                polling_interval=polling_interval,
            )

    def _is_user_allowed(self, user_id: int) -> bool:
        """
        Check if a user is allowed to use the bot.

        If no allowed_user_ids are specified, all users are allowed.

        Args:
            user_id: The Telegram user ID to check

        Returns:
            bool: True if the user is allowed, False otherwise
        """
        # If allowed_user_ids is empty, all users are allowed
        if not self.allowed_user_ids:
            return True

        # Otherwise, check if the user is in the allowed list
        return user_id in self.allowed_user_ids

    def _safe_dict(self, obj):
        """Convert an object to a dictionary, handling None values."""
        if obj is None:
            return None
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return str(obj)

    def _dump_update(self, update: Update) -> dict:
        """Convert update to a dictionary for debugging."""
        if not update:
            return {"error": "Update is None"}

        try:
            # Try to get the raw data
            result = {}
            if update.message:
                result["message"] = {
                    "message_id": update.message.message_id,
                    "from_user": self._safe_dict(update.message.from_user),
                    "chat": self._safe_dict(update.message.chat),
                    "date": str(update.message.date),
                    "text": update.message.text,
                    "has_entities": bool(update.message.entities),
                }

                if update.message.entities:
                    result["message"]["entities"] = [
                        {
                            "type": e.type,
                            "offset": e.offset,
                            "length": e.length,
                            "text": update.message.text[e.offset : e.offset + e.length]
                            if update.message.text
                            else None,
                        }
                        for e in update.message.entities
                    ]

                if update.message.reply_to_message:
                    result["message"]["reply_to_message"] = {
                        "message_id": update.message.reply_to_message.message_id,
                        "from_user": self._safe_dict(
                            update.message.reply_to_message.from_user
                        ),
                        "text": update.message.reply_to_message.text,
                    }

            return result
        except Exception as e:
            logger.exception(f"Error dumping update: {e}")
            return {"error": str(e)}

    async def catch_all(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Catch all handler to log any received updates."""
        try:
            logger.warning(
                "CATCH ALL RECEIVED UPDATES",
                update_type=str(type(update)),
                has_message=update.message is not None,
                chat_type=update.effective_chat.type if update.effective_chat else None,
                message_text=update.message.text if update.message else None,
            )
        except Exception as e:
            logger.exception(f"Error in catch_all handler: {e}")

    async def raw_update_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log raw update data for debugging."""
        try:
            self._dump_update(update)

            # Check if this is a message with text
            if update.message and update.message.text:
                # Check if the message might be mentioning the bot
                if self.me and self.me.username:
                    # Look for possible mentions of the bot
                    possible_mentions = [
                        f"@{self.me.username}",
                        self.me.username,
                        self.me.first_name,
                    ]

                    any(
                        mention.lower() in update.message.text.lower()
                        for mention in possible_mentions
                    )

        except Exception as e:
            logger.exception(f"Error in raw update handler: {e}")

    async def debug_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Debug command to verify bot is working."""
        if not update.effective_user:
            return

        # Get bot info if not already available
        if not self.me:
            try:
                self.me = await context.bot.get_me()
            except Exception as e:
                logger.exception(f"Failed to get bot info in debug command: {e}")

        logger.warning(
            "DEBUG COMMAND RECEIVED",
            chat_id=update.effective_chat.id,
            chat_type=update.effective_chat.type,
            user_id=update.effective_user.id,
            bot_info=self._safe_dict(self.me),
        )

        await update.message.reply_text(
            f"Debug info:\n"
            f"- Bot username: {self.me.username if self.me else 'unknown'}\n"
            f"- Bot ID: {self.me.id if self.me else 'unknown'}\n"
            f"- Chat type: {update.effective_chat.type}\n"
            f"- Chat ID: {update.effective_chat.id}\n"
            f"- Message received successfully!"
        )

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /start command."""
        if not update.effective_user:
            return

        user = update.effective_user
        user_id = user.id

        if not self._is_user_allowed(user_id):
            await update.message.reply_text(
                "Sorry, you're not authorized to use this bot."
            )
            logger.warning("Unauthorized access attempt", user_id=user_id)
            return

        await update.message.reply_text(
            f"👋 Hello {user.first_name}! I'm the Flare AI assistant. "
            f"Feel free to ask me anything about Flare Network, FTSO, XRP, or blockchain topics."
        )
        logger.info("Start command handled", user_id=user_id)

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /help command."""
        if not update.effective_user:
            return

        user_id = update.effective_user.id

        if not self._is_user_allowed(user_id):
            await update.message.reply_text(
                "Sorry, you're not authorized to use this bot."
            )
            logger.warning("Unauthorized help request", user_id=user_id)
            return

        help_text = (
            "🤖 *Flare AI Assistant Help*\n\n"
            "I can answer questions about Flare Network, FTSO, cryptocurrencies, and more.\n\n"
            "*Available commands:*\n"
            "/start - Start the conversation\n"
            "/help - Show this help message\n"
            "/debug - Show diagnostic information\n\n"
            "Simply send me a message, and I'll do my best to assist you!"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle incoming messages and generate AI responses.
        - In private chats: respond to every message
        - In group chats: respond only when the bot is mentioned
        """
        # First, log the raw update for debugging
        self._dump_update(update)

        if not update.message or not update.effective_user:
            logger.warning("Message or user missing, skipping")
            return

        user = update.effective_user
        user_id = user.id
        chat_id = update.effective_chat.id

        # Important - make sure we have bot info
        if not self.me:
            try:
                self.me = await context.bot.get_me()
                logger.info(
                    "Got bot information",
                    bot_id=self.me.id,
                    bot_username=self.me.username,
                    bot_first_name=self.me.first_name,
                )
            except Exception as e:
                logger.exception(f"Failed to get bot info: {e}")
                return

        # Skipping processing if message has no text
        if not update.message.text:
            logger.debug("Skipping message without text")
            return

        message_text = update.message.text

        # Determine chat type
        is_group_chat = update.effective_chat.type in ["group", "supergroup", "channel"]
        is_private_chat = update.effective_chat.type == "private"

        # Log message details for debugging
        log_data = {
            "user_id": user_id,
            "chat_id": chat_id,
            "chat_type": update.effective_chat.type,
            "message_id": update.message.message_id,
            "message_text": message_text,
            "has_entities": update.message.entities is not None,
            "entity_count": len(update.message.entities)
            if update.message.entities
            else 0,
            "bot_username": self.me.username if self.me else "unknown",
        }
        logger.info("Received message details", **log_data)

        # For ALL messages, do a simple text contains check first for debug purposes
        if self.me and self.me.username:
            mention_variations = [
                f"@{self.me.username}",
                f"@{self.me.username.lower()}",
                self.me.username,
                self.me.username.lower(),
            ]

        is_mentioned = False

        if is_group_chat:
            # Multiple ways to check for mentions:

            # 1. Check direct mentions using entities (most reliable)
            if update.message.entities:
                for entity in update.message.entities:
                    if entity.type == "mention":
                        mention_text = message_text[
                            entity.offset : entity.offset + entity.length
                        ]

                        # Compare with different variations of the bot username
                        bot_username = (
                            self.me.username.lower()
                            if self.me and self.me.username
                            else ""
                        )
                        mention_without_at = (
                            mention_text[1:].lower()
                            if mention_text.startswith("@")
                            else mention_text.lower()
                        )

                        if mention_without_at == bot_username:
                            is_mentioned = True
                            message_text = message_text.replace(
                                mention_text, ""
                            ).strip()
                            break

            # 2. Check text-based mention with @ symbol (multiple variations)
            if not is_mentioned and self.me and self.me.username:
                mention_variations = [
                    f"@{self.me.username}",
                    f"@{self.me.username.lower()}",
                ]

                for variation in mention_variations:
                    if variation.lower() in message_text.lower():
                        is_mentioned = True
                        logger.info(f"Bot mentioned in text (variation): {variation}")
                        # Find the actual text as it appears in the message (case preserving)
                        idx = message_text.lower().find(variation.lower())
                        if idx >= 0:
                            actual_length = len(variation)
                            actual_mention = message_text[idx : idx + actual_length]
                            message_text = message_text.replace(
                                actual_mention, ""
                            ).strip()
                        break

            # 3. Check if message is a reply to bot's message
            if (
                not is_mentioned
                and update.message.reply_to_message
                and update.message.reply_to_message.from_user
            ):
                reply_user_id = update.message.reply_to_message.from_user.id
                bot_id = self.me.id if self.me else None

                logger.info(
                    "Reply detection check",
                    reply_to_user_id=reply_user_id,
                    bot_id=bot_id,
                )

                if bot_id and reply_user_id == bot_id:
                    is_mentioned = True
                    logger.info("Message is a reply to bot")

            # Log mention detection result
            logger.info(
                "Group mention detection result",
                is_mentioned=is_mentioned,
                chat_id=chat_id,
                user_id=user_id,
                chat_type=update.effective_chat.type,
                bot_username=self.me.username if self.me else "unknown",
            )

            # Only respond to mentions in group chats
            if not is_mentioned:
                logger.debug(
                    "Ignoring group message (not mentioned)",
                    chat_id=chat_id,
                    user_id=user_id,
                )
                return

            # If the message was just the mention with no content, respond with a greeting
            if not message_text:
                message_text = "Hello"
                logger.info(
                    "Empty mention received, responding with greeting",
                    chat_id=chat_id,
                    user_id=user_id,
                )

        # For private chats, respond to all messages (default behavior)
        # No special processing needed as we want to reply to everything

        # Access control check
        if not self._is_user_allowed(user_id):
            # For private chats, inform the user they're not authorized
            if is_private_chat:
                await update.message.reply_text(
                    "Sorry, you're not authorized to use this bot."
                )
            # For group chats, just silently ignore unauthorized users
            logger.warning(
                "Unauthorized message",
                user_id=user_id,
                chat_id=chat_id,
                is_group=is_group_chat,
            )
            return

        logger.info(
            "Processing message",
            user_id=user_id,
            chat_id=chat_id,
            is_group=is_group_chat,
            message_text=message_text,
        )

        # Generate AI response
        try:
            # Send typing action to show the bot is processing
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")

            # Generate response from AI provider
            ai_response = self.ai_provider.generate_content(message_text)
            response_text = ai_response.text

            # Track last processed time
            self.last_processed_time[chat_id] = time.time()

            # Send response
            await update.message.reply_text(response_text)
            logger.info(
                "Sent AI response",
                chat_id=chat_id,
                user_id=user_id,
                is_group=is_group_chat,
            )

        except Exception as e:
            logger.error(f"Error generating AI response: {e}", exc_info=True)
            await update.message.reply_text(
                "I'm having trouble processing your request. Please try again later."
            )

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors in the telegram bot."""
        logger.error(f"Telegram error: {context.error}", update=update)

    async def initialize(self) -> None:
        """Initialize the bot application."""
        logger.info("Initializing Telegram bot")
        # Create application
        self.application = Application.builder().token(self.api_token).build()

        # Get bot information first - before registering handlers
        try:
            self.me = await Bot(self.api_token).get_me()
            logger.info(
                "Bot information retrieved",
                bot_id=self.me.id,
                bot_username=self.me.username,
                bot_first_name=self.me.first_name,
            )
        except TelegramError as e:
            logger.exception(f"Failed to get bot info: {e}")
            self.me = None

        # Add handlers
        # Catch-all handler for debugging - highest priority
        self.application.add_handler(
            MessageHandler(filters.ALL, self.catch_all), group=-9999
        )

        # Raw update handler (debugging) - high priority
        self.application.add_handler(
            MessageHandler(filters.ALL, self.raw_update_handler), group=-999
        )

        # Debug command
        self.application.add_handler(CommandHandler("debug", self.debug_command))

        # Normal handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Add error handler
        self.application.add_error_handler(self.error_handler)

        # Initialize the application
        await self.application.initialize()

    async def start_polling(self) -> None:
        """Start polling for updates."""
        if not self.application:
            msg = "Bot not initialized. Call initialize() first."
            raise RuntimeError(msg)

        logger.info("Starting Telegram bot polling")
        await self.application.start()
        await self.application.updater.start_polling(
            poll_interval=self.polling_interval,
            timeout=30,  # Increase timeout
            bootstrap_retries=5,  # Allow multiple retries on startup
            read_timeout=30,  # Longer read timeout
            write_timeout=30,  # Longer write timeout
        )

    async def shutdown(self) -> None:
        """Shut down the bot."""
        if self.application:
            logger.info("Shutting down Telegram bot")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

    async def start(self) -> None:
        """Start the Telegram bot."""
        try:
            logger.info("Starting Telegram bot")
            await self.initialize()
            await self.start_polling()

            # Keep the bot running indefinitely
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Telegram bot stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in Telegram bot: {e}", exc_info=True)
        finally:
            await self.shutdown()
