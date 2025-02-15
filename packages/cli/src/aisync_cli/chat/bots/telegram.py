from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from aisync_cli.chat.bots.base import BaseBot


class TelegramBot(BaseBot):
    def __init__(self):
        self.app = None

    def setup(self) -> None:
        self.app = ApplicationBuilder().token(self.config["token"]).build()

        # Register handlers
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._message_handler)
        )

        super().setup()

    def start(self) -> None:
        super().start()
        self.app.run_polling()

    async def astart(self) -> None:
        # Telegram doesn't support async run_polling
        raise NotImplementedError("Telegram bot doesn't support async start")

    def stop(self) -> None:
        super().stop()
        self.app.stop()

    async def astop(self) -> None:
        super().astop()
        await self.app.shutdown()

    async def _start_command(self, update, context):
        await update.message.reply_text("Hello! I'm a Telegram bot.")

    async def _message_handler(self, update, context):
        await update.message.reply_text(f"You said: {update.message.text}")
