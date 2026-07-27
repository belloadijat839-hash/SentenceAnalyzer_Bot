from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.text_stats import analyze, format_stats, split_sentences

logger = logging.getLogger(__name__)

MAX_TEXT_LEN = 20000  # guard against absurdly large pastes

HELP_TEXT = (
    "*SentenceAnalyzer_Bot*\n\n"
    "Just send me any text (or a `.txt` file) and I'll break it down for you: "
    "sentence count, word count, character count, syllables, reading time, "
    "and a readability score.\n\n"
    "Commands:\n"
    "/stats - re-show the analysis for the last text you sent\n"
    "/sentences - list out each sentence from the last text, numbered\n"
    "/help - show this message"
)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to SentenceAnalyzer_Bot!\n\n" + HELP_TEXT, parse_mode="Markdown"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def _analyze_and_store(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    text = text.strip()
    if not text:
        await update.message.reply_text("That looks empty — send me some text to analyze.")
        return

    if len(text) > MAX_TEXT_LEN:
        await update.message.reply_text(
            f"That's a lot of text ({len(text)} characters) — please send under {MAX_TEXT_LEN} characters at a time."
        )
        return

    context.user_data["last_text"] = text
    stats = analyze(text)
    await update.message.reply_text(format_stats(stats), parse_mode="Markdown")


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _analyze_and_store(update, context, update.message.text)


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.lower().endswith(".txt"):
        await update.message.reply_text("I can only read `.txt` files right now.", parse_mode="Markdown")
        return

    file = await doc.get_file()
    raw = await file.download_as_bytearray()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        await update.message.reply_text("Couldn't read that file as UTF-8 text.")
        return

    await _analyze_and_store(update, context, text)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get("last_text")
    if not text:
        await update.message.reply_text("Send me some text first, then I can show stats for it.")
        return
    stats = analyze(text)
    await update.message.reply_text(format_stats(stats), parse_mode="Markdown")


async def sentences_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get("last_text")
    if not text:
        await update.message.reply_text("Send me some text first, then I can list its sentences.")
        return

    sentences = split_sentences(text)
    if not sentences:
        await update.message.reply_text("No sentences detected in the last text.")
        return

    lines = [f"{i}. {s}" for i, s in enumerate(sentences, start=1)]
    reply = "\n".join(lines)

    # Telegram messages cap at 4096 chars; chunk if needed.
    for i in range(0, len(reply), 4000):
        await update.message.reply_text(reply[i:i + 4000])
