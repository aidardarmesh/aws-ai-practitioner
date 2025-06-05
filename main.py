import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from bedrock import chain

load_dotenv(verbose=True)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.replace('/ask ', '', 1).strip()

    if not question:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Задавайте вопрос, используя команду /ask <ваш вопрос>.")
        return

    response = chain.run(question)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('TG_TOKEN')).build()

    ask_handler = CommandHandler('ask', ask)
    application.add_handler(ask_handler)

    application.run_polling()