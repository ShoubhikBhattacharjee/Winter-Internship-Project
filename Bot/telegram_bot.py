from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *
import faiss, json
from pathlib import Path
import numpy as np

BOT_TOKEN = "8538854872:AAHa38H5p-s01trjVxqLmdpDtY2KcFdKN1Y"
DATA_DIR = Path("./Data")

# Load FAISS index + KB metadata
INDEX = faiss.read_index(str(DATA_DIR / "embeddings.faiss"))
KB = json.loads((DATA_DIR / "meta.json").read_text())

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

    if not query:
        return

    scores, idxs = semantic_search(query)

    for score, i in zip(scores, idxs):
        item = KB[i]
        text = f"Q: {item['question']}\nA: {item['answer']}"

        btn = InlineKeyboardButton(
            "Get Source Files",
            callback_data=f"src:{item['id']}"
        )

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup([[btn]])
        )


# ----- Handle file buttons -----
async def handle_callback(update: Update, ctx):
    data = update.callback_query.data

    if data.startswith("src:"):
        item_id = data.split(":")[1]
        item = next(it for it in KB if it["id"] == item_id)

        buttons = []
        for ext in item["source"]["path"]:
            buttons.append([
                InlineKeyboardButton(
                    f"Get {ext.upper()}",
                    url=f"http://localhost:8001/fetch?id={item_id}&ext={ext}"
                )
            ])

        await update.callback_query.edit_message_reply_markup(
            InlineKeyboardMarkup(buttons)
        )

async def start(update, ctx):
    await update.message.reply_text("Hi! Just type anything to ask your KB.")


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
