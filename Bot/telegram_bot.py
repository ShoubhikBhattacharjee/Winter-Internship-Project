from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *
import faiss, json
from pathlib import Path
import numpy as np

BOT_TOKEN = "8538854872:AAHa38H5p-s01trjVxqLmdpDtY2KcFdKN1Y"
DATA_DIR = Path("./Data")

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
    )
}


# Load FAISS index + KB metadata
INDEX = faiss.read_index(str(DATA_DIR / "embeddings.faiss"))
KB = json.loads((DATA_DIR / "meta.json").read_text())
NOTES_BASE = Path("./Notes")  # adjust if needed

# Load model ONCE globally (much faster)
from sentence_transformers import SentenceTransformer
EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# ----- Semantic search -----
def semantic_search(query, top_k=3):
    q = EMBED_MODEL.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q)
    scores, idx = INDEX.search(q, top_k)
    return scores[0], idx[0]


# ----- Handle all user text -----
async def handle_query(update: Update, ctx):
    query = update.message.text.strip()

    # Basic sanity check
    if len(query) < 4:
        await update.message.reply_text(
            "😅 That doesn’t look like a meaningful question yet."
        )
        return

    scores, idxs = semantic_search(query)
    best_score = scores[0]
    confidence = confidence_from_score(best_score)
    intent = infer_intent(query)

    # If no confidence → refuse politely
    if confidence == "none":
        await update.message.reply_text(CONFIDENCE_MESSAGES["none"])
        return

    # Otherwise, answer using the BEST match only
    item = KB[idxs[0]]
    answer = item["answer"]

    text = (
        f"{CONFIDENCE_MESSAGES[confidence]}\n\n"
        f"{answer}"
    )

    # Only show source button if we answered
    btn = InlineKeyboardButton(
        "Get Source Files",
        callback_data=f"src:{item['id']}"
    )

    # Frame an answer based on intent
    framed = frame_answer(
        answer=item["answer"],
        intent=intent,
        confidence=confidence
    )

    await update.message.reply_text(
        framed,
        reply_markup=InlineKeyboardMarkup([[btn]])
    )


async def handle_callback(update: Update, ctx):
    query = update.callback_query
    data = query.data

    # User clicked "Get Source Files"
    if data.startswith("src:"):
        item_id = data.split(":")[1]
        item = next(it for it in KB if it["id"] == item_id)

        buttons = []
        for ext in item["source"]["path"]:
            buttons.append([
                InlineKeyboardButton(
                    f"Get {ext.upper()}",
                    callback_data=f"getfile:{item_id}:{ext}"
                )
            ])

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(buttons)
        )
        return

    # User clicked "Get .MD / .PDF"
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
            filename=file_path.name
        )

        await query.answer("File sent 📎")


async def start(update, ctx):
    await update.message.reply_text("Hi! Just type anything to chat with me. I am willing to assist in any way I can.")

def confidence_from_score(score: float) -> str:
    for threshold, level in CONFIDENCE_LEVELS:
        if score >= threshold:
            return level
    return "none"


def infer_intent(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["how", "steps", "do i", "procedure"]):
        return "how"
    if any(w in q for w in ["why", "reason", "cause"]):
        return "why"
    if any(w in q for w in ["check", "status", "verify"]):
        return "check"
    return "general"


def frame_answer(answer: str, intent: str, confidence: str) -> str:
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





# ----- Main bot -----
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Every text message = search query
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))

    # Callback buttons
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Greet users with /start
    app.add_handler(CommandHandler("start", start))

    print("Bot running... just message it anything!")
    app.run_polling()
