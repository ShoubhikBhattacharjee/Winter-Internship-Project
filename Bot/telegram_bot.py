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

import logging

# ============================================================
# Configuration
# ============================================================

LOGGER = logging.getLogger(__name__)

#BOT_TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
BOT_TOKEN = "8538854872:AAHa38H5p-s01trjVxqLmdpDtY2KcFdKN1Y"

DATA_DIR = Path("./Data")
NOTES_DIR = Path("./Notes")

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

# Dominance threshold:
# If the top result is this much better than the second-best,
# we assume a single clear answer and avoid merging.
DOMINANCE_MARGIN = 0.12

MIN_COMMON_TAGS = 2

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


def is_dominant(best_score: float, second_score: float) -> bool:
    """
    Determine whether the top result clearly dominates the second-best result.

    Returns True if the difference exceeds the configured dominance margin.
    """
    return (best_score - second_score) >= DOMINANCE_MARGIN


def tag_overlap_count(tags_a, tags_b) -> int:
    """Return number of common tags between two tag lists."""
    return len(set(tags_a) & set(tags_b))

# ============================================================
# Telegram handlers
# ============================================================

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ------------------------------------------------------------
    # 1. Defensive guard: ensure this update actually contains a
    #    text message (Telegram can send many update types)
    # ------------------------------------------------------------
    if not update.message:
        return

    # ------------------------------------------------------------
    # 2. Extract and normalize the user query
    # ------------------------------------------------------------
    query = update.message.text.strip()

    # ------------------------------------------------------------
    # 3. Reject queries that are too short to be meaningful
    # ------------------------------------------------------------
    if len(query) < 4:
        await update.message.reply_text(
            "😅 That doesn’t look like a real question yet."
        )
        return

    # ------------------------------------------------------------
    # 4. Perform semantic search against the FAISS index
    #    Returns similarity scores and KB indices
    # ------------------------------------------------------------
    scores, indices = semantic_search(query, TOP_K_RESULTS)

    # ------------------------------------------------------------
    # 5. Pair FAISS results with KB metadata
    # ------------------------------------------------------------
    candidates = [(s, KB[i]) for s, i in zip(scores, indices)]

    # ------------------------------------------------------------
    # 6. Filter out weak matches below the merge threshold
    # ------------------------------------------------------------
    relevant = [(s, it) for s, it in candidates if s >= MIN_MERGE_SCORE]

    # ------------------------------------------------------------
    # 7. If nothing relevant is found, return a confidence-aware
    #    fallback response
    # ------------------------------------------------------------
    if not relevant:
        await update.message.reply_text(CONFIDENCE_MESSAGES["none"])
        return

    # ------------------------------------------------------------
    # 8. Sort remaining results by descending similarity
    # ------------------------------------------------------------
    relevant.sort(key=lambda x: x[0], reverse=True)

    # ------------------------------------------------------------
    # 9. Enforce semantic coherence by keeping only results
    #    that share enough tags with the top result
    # ------------------------------------------------------------
    top_tags = relevant[0][1].get("tags", [])
    filtered = [
        (s, it)
        for s, it in relevant
        if tag_overlap_count(top_tags, it.get("tags", [])) >= MIN_COMMON_TAGS
    ]

    # ------------------------------------------------------------
    # 10. Compute confidence and dominance metrics
    # ------------------------------------------------------------
    best_score = filtered[0][0]
    second_score = filtered[1][0] if len(filtered) > 1 else 0.0
    confidence = confidence_from_score(best_score)

    # ------------------------------------------------------------
    # 11. Single-answer path:
    #     Used when only one result exists OR when the best
    #     result clearly dominates the rest
    # ------------------------------------------------------------
    if len(filtered) == 1 or is_dominant(best_score, second_score):
        item = filtered[0][1]
        intent = infer_intent(query)

        reply = frame_answer(
            answer=item["answer"],
            intent=intent,
            confidence=confidence,
        )

        # Attach a button allowing the user to request source files
        button = InlineKeyboardButton(
            "Get Source Files",
            callback_data=f"src:{item['id']}",
        )

        await update.message.reply_text(
            reply,
            reply_markup=InlineKeyboardMarkup([[button]]),
        )
        return

    # ------------------------------------------------------------
    # 12. Multi-answer merge path:
    #     Used when multiple results are relevant and comparable
    # ------------------------------------------------------------
    merged = (
        merge_prefix(confidence)
        + merge_answers(filtered)
        + f"\n\n_(Combined from {len(filtered)} related notes.)_"
    )

    LOGGER.info("Merged response generated for query: %s", query)
    await update.message.reply_text(merged)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ------------------------------------------------------------
    # 1. Defensive guard: ensure callback data exists
    # ------------------------------------------------------------
    query = update.callback_query
    if not query:
        return

    data = query.data or ""

    # ------------------------------------------------------------
    # 2. Source selection stage:
    #    User clicked "Get Source Files"
    #    → Show available file formats
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # 3. File delivery stage:
    #    User selected a specific source file to download
    # ------------------------------------------------------------
    if data.startswith("getfile:"):
        _, item_id, ext = data.split(":", 2)
        item = next(it for it in KB if it["id"] == item_id)

        # Resolve file path safely relative to NOTES_DIR
        file_path = NOTES_DIR / item["source"]["path"][ext].lstrip("/")

        # --------------------------------------------------------
        # 4. Validate file existence before sending
        # --------------------------------------------------------
        if not file_path.exists():
            await query.answer("File not found.")
            return

        # --------------------------------------------------------
        # 5. Send file to user via Telegram
        # --------------------------------------------------------
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_path.open("rb"),
            filename=file_path.name,
        )

        await query.answer("File sent 📎")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ------------------------------------------------------------
    # Entry greeting for first-time or returning users
    # ------------------------------------------------------------
    if update.message:
        await update.message.reply_text(
            "Hi! Ask me anything — I’ll search my knowledge base and help if I can."
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
