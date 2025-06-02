from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

class BanCheckMiddleware(BaseMiddleware):
    def __init__(self, shared_data: dict):
        self.shared_data = shared_data

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        
        user_id = event.from_user.id

        bans = dict()
        async with self.shared_data['lock']:
            for item in self.shared_data['config']['banned']:
                bans[item['id']] = item['reason'] 
        if user_id in bans.keys():
            await event.answer(f"🚫 Вы заблокированы.\nПричина: {bans[user_id]}")
            return  # прервать дальнейшую обработку

        return await handler(event, data)
