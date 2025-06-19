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
    """Retrieve secret from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        return get_secret_value_response['SecretString']
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise e


def initialize_bedrock_llm():
    """Initialize Bedrock LLM with proper error handling"""
    try:
        bedrock_client = boto3.client(
            service_name="bedrock-runtime",
            region_name=REGION_NAME,
        )

        llm = Bedrock(
            client=bedrock_client,
            model_id=LLM_MODEL_ID,
            model_kwargs={
                "temperature": 0.7,
                "maxTokenCount": 1024,
            }
        )
        
        logger.info(f"Successfully initialized Bedrock LLM with model: {LLM_MODEL_ID}")
        return llm
        
    except Exception as e:
        logger.error(f"Error initializing Bedrock LLM: {e}")
        raise e


# Initialize components
try:
    secret_object = json.loads(get_secret(SECRET_NAME, REGION_NAME))
    application = Application.builder().token(secret_object["TG_TOKEN"]).build()
    llm = initialize_bedrock_llm()
    
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
    
    logger.info("Successfully initialized all components")
    
except Exception as e:
    logger.error(f"Error during initialization: {e}")
    # Set fallback values
    application = None
    chain = None


def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        return asyncio.get_event_loop().run_until_complete(main(event))
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask command with Bedrock LLM"""
    try:
        question = update.message.text.replace('/ask ', '', 1).strip()

        if not question:
            await context.bot.send_message(
                chat_id=update.message.chat.id, 
                text="Задавайте вопрос, используя команду /ask <ваш вопрос>."
            )
            return

        if not chain:
            await context.bot.send_message(
                chat_id=update.message.chat.id, 
                text="Извините, сервис временно недоступен. Попробуйте позже."
            )
            return

        logger.info(f"Processing question: {question[:50]}...")
        
        # Call Bedrock LLM
        response = chain.run(question)
        
        logger.info("Successfully got response from Bedrock")
        
        await context.bot.send_message(
            chat_id=update.message.chat.id, 
            text=response
        )
        
    except Exception as e:
        logger.error(f"Error in ask function: {e}")
        await context.bot.send_message(
            chat_id=update.message.chat.id, 
            text="Произошла ошибка при обработке вашего запроса. Попробуйте позже."
        )


async def main(event):
    """Main async function to handle Telegram updates"""
    try:
        if not application:
            logger.error("Application not initialized")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Application not initialized'})
            }

        ask_handler = CommandHandler('ask', ask)
        application.add_handler(ask_handler)

        logger.info("Received event body: %s", event.get("body", "")[:200])

        await application.initialize()
        await application.process_update(
            Update.de_json(json.loads(event["body"]), application.bot)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Success'})
        }

    except Exception as exc:
        logger.error(f"Error in main function: {exc}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(exc)})
        }