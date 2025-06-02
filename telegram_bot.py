import asyncio
import os

import telegram
from dotenv import load_dotenv

load_dotenv()

async def main():
    bot = telegram.Bot(os.getenv('TG_TOKEN'))
    async with bot:
        print(await bot.get_me())


if __name__ == '__main__':
    asyncio.run(main())