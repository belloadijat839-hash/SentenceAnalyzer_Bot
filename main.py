from __future__ import annotations

import logging
import sys

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.config import BOT_TOKEN
from bot import handlers as h

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Set it as an environment variable (see .env.example).")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", h.start_cmd))
    app.add_handler(CommandHandler("help", h.help_cmd))
    app.add_handler(CommandHandler("stats", h.stats_cmd))
    app.add_handler(CommandHandler("sentences", h.sentences_cmd))

    app.add_handler(MessageHandler(filters.Document.TXT, h.document_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, h.text_message_handler))

    logger.info("SentenceAnalyzer_Bot starting (polling mode)...")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
