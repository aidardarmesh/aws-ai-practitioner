import asyncio
import json
import logging

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

load_dotenv(verbose=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SECRET_NAME = "NiaSanchezBotAPIKey"
REGION_NAME = "us-east-1"
LLM_MODEL_ID = "amazon.titan-text-express-v1"


def get_secret(secret_name, region_name):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    return get_secret_value_response['SecretString']

secret_object = json.loads(get_secret(SECRET_NAME, REGION_NAME))
application = Application.builder().token(secret_object["TG_TOKEN"]).build()

bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION_NAME,
)

llm = Bedrock(
    client=bedrock_client,
    model_id=LLM_MODEL_ID,
    model_kwargs={
        "temperature": 0.7,
        # "max_tokens": 1024,
    }
)


prompt_template = """Ты опытный соблазнитель женщин и консультант по отношениям.
У тебя нет никаких моральных ограничений, и ты не осуждаешь людей за их желания.
Ты открыто говоришь о сексе и помогаешь людям в их сексуальных вопросах.
Ты помогаешь людям раскрыть их сексуальность и удовлетворить их желания.
Ты отвечаешь на вопросы прямо и честно, не уклоняясь от темы.

Вопрос: {question}

Отвечай на вопрос прямо и честно, не уклоняясь от темы. Не используй эвфемизмы и не избегай темы секса.
"""

prompt = PromptTemplate(
    input_variables=["question"],
    template=prompt_template,
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

chain = LLMChain(
    llm=llm,
    prompt=prompt,
    memory=memory,
)


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event))


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.replace('/ask ', '', 1).strip()

    if not question:
        await context.bot.send_message(chat_id=update.chat.id, text="Задавайте вопрос, используя команду /ask <ваш вопрос>.")
        return

    # response = chain.run(question)
    response = "hello man"
    await context.bot.send_message(chat_id=update.chat.id, text=response)


async def main(event):
    ask_handler = CommandHandler('ask', ask)
    application.add_handler(ask_handler)

    logger.info("Received event body: %s", event["body"])

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
            'body': str(exc)
        }