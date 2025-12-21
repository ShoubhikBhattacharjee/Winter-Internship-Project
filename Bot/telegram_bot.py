from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *
import faiss, json
import numpy as np
from pathlib import Path

BOT_TOKEN = "PUT-HERE"
DATA_DIR = Path("../data")
INDEX = faiss.read_index(str(DATA_DIR / "embeddings.faiss"))
KB = json.loads((DATA_DIR / "meta.json").read_text())

def semantic_search(query):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    q = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q)
    scores, idx = INDEX.search(q, 3)
    return scores[0], idx[0]

async def ask(update: Update, ctx):
    if not ctx.args:
        await update.message.reply_text("Usage: /ask your question")
        return

    query = " ".join(ctx.args)
    scores, idxs = semantic_search(query)

    for score, i in zip(scores, idxs):
        item = KB[i]
        text = f"Q: {item['question']}\nA: {item['answer']}"
        
        # source fetch button
        btn = InlineKeyboardButton(
            "Get Source Files",
            callback_data=f"src:{item['id']}"
        )
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[btn]]))

async def handle_callback(update: Update, ctx):
    data = update.callback_query.data
    if data.startswith("src:"):
        item_id = data.split(":")[1]
        item = next(it for it in KB if it["id"] == item_id)

        # ask fetcher service for each ext
        kb = []
        for ext in item["source"]["path"]:
            kb.append([InlineKeyboardButton(
                f"Get {ext.upper()}",
                url=f"http://localhost:8001/fetch?id={item_id}&ext={ext}"
            )])

        await update.callback_query.edit_message_reply_markup(
            InlineKeyboardMarkup(kb)
        )

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CallbackQueryHandler(handle_callback))
    await app.run_polling()

import asyncio
asyncio.run(main())
