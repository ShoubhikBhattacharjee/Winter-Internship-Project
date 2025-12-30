"""
Personal Knowledge Base Telegram Bot

This bot:
- Runs locally using Telegram polling (no public server)
- Uses FAISS + sentence-transformers for semantic retrieval
- Answers only when confident
- Can safely merge multiple KB entries into one response
- Sends source files directly via Telegram callbacks

Design goals:
- No hallucination
- No training data leakage
- Honest confidence signaling
- Long-term maintainability
"""

from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# Configuration
# ============================================================

#BOT_TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
BOT_TOKEN = "8538854872:AAHa38H5p-s01trjVxqLmdpDtY2KcFdKN1Y"

DATA_DIR = Path("./Data")

TOP_K_RESULTS = 5
MIN_MERGE_SCORE = 0.55

CONFIDENCE_LEVELS = [
    (0.70, "high"),
    (0.60, "medium"),
    (0.50, "low"),
]

CONFIDENCE_MESSAGES = {
    "high": "✅ I’m fairly confident about this:",
    "medium": "🤔 I might be able to help with this, though I’m not completely sure:",
    "low": "⚠️ I found something that *might* be related, but my confidence is low:",
    "none": (
        "😕 I couldn’t find anything relevant to that yet.\n\n"
        "I’m still learning — you could try rephrasing your question or using more specific terms."
    ),
}

# ============================================================
# Load models and data (once at startup)
# ============================================================

INDEX = faiss.read_index(str(DATA_DIR / "embeddings.faiss"))
KB = json.loads((DATA_DIR / "meta.json").read_text(encoding="utf-8"))

EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# ============================================================
# Core retrieval & reasoning helpers
# ============================================================

def semantic_search(query: str, top_k: int):
    """
    Encode a query and retrieve top_k most similar KB entries.
    Returns (scores, indices).
    """
    vector = EMBED_MODEL.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(vector)
    scores, indices = INDEX.search(vector, top_k)
    return scores[0], indices[0]


def confidence_from_score(score: float) -> str:
    """Map cosine similarity score to a confidence label."""
    for threshold, level in CONFIDENCE_LEVELS:
        if score >= threshold:
            return level
    return "none"


def infer_intent(query: str) -> str:
    """Lightweight intent inference based on keywords."""
    q = query.lower()
    if any(w in q for w in ("how", "steps", "do i", "procedure")):
        return "how"
    if any(w in q for w in ("why", "reason", "cause")):
        return "why"
    if any(w in q for w in ("check", "status", "verify")):
        return "check"
    return "general"


def frame_answer(answer: str, intent: str, confidence: str) -> str:
    """
    Frame a single KB answer based on user intent and confidence.
    No factual rewriting is done here.
    """
    prefix = {
        "high": "I’m confident this addresses what you’re asking.\n\n",
        "medium": "This should help, though it may not cover every detail.\n\n",
        "low": "This may be partially relevant.\n\n",
    }.get(confidence, "")

    intent_opening = {
        "how": "Here’s how you can do it:\n\n",
        "why": "Here’s the reasoning behind it:\n\n",
        "check": "To check or verify this:\n\n",
        "general": "Here’s the relevant information:\n\n",
    }[intent]

    return prefix + intent_opening + answer


def merge_prefix(confidence: str) -> str:
    """Intro text for merged answers."""
    if confidence == "high":
        return "I’m confident the following points together address your question:\n\n"
    if confidence == "medium":
        return "Here are a few related notes that together should help:\n\n"
    return "I found several partially related notes. They may help when read together:\n\n"


def merge_answers(results):
    """
    Merge multiple KB answers safely by concatenation.
    results: list of (score, kb_item)
    """
    return "\n\n---\n\n".join(item["answer"].strip() for _, item in results)

# ============================================================
# Telegram handlers
# ============================================================

async def handle_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle all non-command text messages as KB queries."""
    query = update.message.text.strip()

    if len(query) < 4:
        await update.message.reply_text(
            "😅 That doesn’t look like a meaningful question yet."
        )
        return

    scores, indices = semantic_search(query, TOP_K_RESULTS)

    candidates = [(s, KB[i]) for s, i in zip(scores, indices)]
    relevant = [(s, it) for s, it in candidates if s >= MIN_MERGE_SCORE]

    if not relevant:
        await update.message.reply_text(CONFIDENCE_MESSAGES["none"])
        return

    best_score = relevant[0][0]
    confidence = confidence_from_score(best_score)

    # Single-answer path
    if len(relevant) == 1:
        item = relevant[0][1]
        intent = infer_intent(query)

        reply = frame_answer(
            answer=item["answer"],
            intent=intent,
            confidence=confidence,
        )

        button = InlineKeyboardButton(
            "Get Source Files",
            callback_data=f"src:{item['id']}",
        )

        await update.message.reply_text(
            reply,
            reply_markup=InlineKeyboardMarkup([[button]]),
        )
        return

    # Multi-answer merge path
    merged = merge_prefix(confidence) + merge_answers(relevant)
    await update.message.reply_text(merged)


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks."""
    query = update.callback_query
    data = query.data

    if data.startswith("src:"):
        item_id = data.split(":", 1)[1]
        item = next(it for it in KB if it["id"] == item_id)

        buttons = [
            [
                InlineKeyboardButton(
                    f"Get {ext.upper()}",
                    callback_data=f"getfile:{item_id}:{ext}",
                )
            ]
            for ext in item["source"]["path"]
        ]

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("getfile:"):
        _, item_id, ext = data.split(":", 2)
        item = next(it for it in KB if it["id"] == item_id)

        file_path = Path(item["source"]["path"][ext])

        if not file_path.exists():
            await query.answer("File not found on disk.")
            return

        await ctx.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_path.open("rb"),
            filename=file_path.name,
        )
        await query.answer("File sent 📎")


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Just type anything — I’ll search my knowledge base and help if I can."
    )

# ============================================================
# Entrypoint
# ============================================================

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot running... just message it anything!")
    app.run_polling()
