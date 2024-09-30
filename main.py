import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
import os
from app.admin_handler import admin_router
from app.user_handler import user_router

#bot = Bot(token=f'{os.getenv('API_Token')}')
bot = Bot(token='7239649070:AAEVL4Hllh8rKLsmfMBHLYY6lUItt_KBTHY')
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    dp.include_router(user_router)
    dp.include_router(admin_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
