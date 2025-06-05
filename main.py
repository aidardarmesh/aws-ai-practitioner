import json
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
application = ApplicationBuilder().token(os.getenv('TG_TOKEN')).build()


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.replace('/ask ', '', 1).strip()

    if not question:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Задавайте вопрос, используя команду /ask <ваш вопрос>.")
        return

    response = chain.run(question)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def main(event, context):
    ask_handler = CommandHandler('ask', ask)
    application.add_handler(ask_handler)

    try:
        await application.initialize()
        await application.process_update(
            Update.de_json(json.loads(event["body"]), application.bot)
        )

        return {
            'statusCode': 200,
            'body': 'Success'
        }

    except Exception as exc:
        return {
            'statusCode': 500,
            'body': 'Failure'
        }