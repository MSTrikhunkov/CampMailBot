#!/usr/bin/python3

import asyncio
import yaml
import os
from aiogram import Bot, Dispatcher
from handlers import get_router
from ban_checker import BanCheckMiddleware




CONFIG_PATH = 'config/config.yaml'
MAILS_PATH = 'mails'


async def main(shared_data):
    async with shared_data['lock']:
        bot = Bot(token=shared_data['config']['token'])

    dp = Dispatcher()
    dp.message.middleware(BanCheckMiddleware(shared_data))
    dp.include_router(get_router(shared_data))

    print(f"MailerBot Successfully started")
    await dp.start_polling(bot)


if __name__ == '__main__':
    with open(CONFIG_PATH, 'r') as cfg:
        config = yaml.safe_load(cfg)

    for item in config['locations']:
        if not os.path.exists(f"{MAILS_PATH}{os.sep}{item['file']}"):
            with open(f"{MAILS_PATH}{os.sep}{item['file']}", 'w') as f:
                f.write("{}")

    shared_data = dict()
    shared_data['config'] = config
    shared_data['lock'] = asyncio.Lock()
    asyncio.run(main(shared_data))
