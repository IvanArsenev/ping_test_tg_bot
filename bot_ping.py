import asyncio, requests, aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from urllib.parse import urlparse

TOKEN = ''
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)
user_dict = {}
last_message_id = {}

PING_INTERVALS = {
    "5 минут": 300,
    "30 минут": 1800,
    "1 час": 3600,
    "3 часа": 10800,
    "12 часов": 43200,
    "24 часа": 86400
}

class IntervalCallback(CallbackData, prefix="interval"):
    name: str

async def create_user_list():
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT id FROM User") as cursor:
            users = await cursor.fetchall()
            if len(users) != 0:
                for user_id in users:
                    user_dict[user_id[0]] = 0
                    if await get_user_status(user_id[0]):
                        asyncio.create_task(ping_servers(user_id[0]))

async def init_db():
    global users
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS User (
                            id INTEGER PRIMARY KEY,
                            link_limit INTEGER,
                            enable BOOLEAN,
                            bot_timeout INTEGER)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS Server (
                            user_id INTEGER,
                            link TEXT,
                            type TEXT,
                            FOREIGN KEY(user_id) REFERENCES User(id))''')
        await db.commit()

async def get_user_status(user_id: int):
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT enable FROM User WHERE id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def get_user_link(user_id: int, link: str):
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT link FROM Server WHERE user_id = ? AND link = ?", (user_id,link,)) as cursor:
            result = await cursor.fetchall()
            return result[0] if result else None

async def get_user_links(user_id: int):
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT link FROM Server WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchall()
            return result

async def get_user_link_count(user_id: int):
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT link FROM Server WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchall()
            return len(result)

async def get_user_limit(user_id: int):
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT link_limit FROM User WHERE id = ?", (user_id,)) as cursor:
            result = await cursor.fetchall()
            return result

async def ensure_user_exists(user_id: int):
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute("INSERT OR IGNORE INTO User (id) VALUES (?)", (user_id,))
        await db.commit()

async def add_user_link(user_id: int, link: str, type: str):
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute("INSERT OR IGNORE INTO Server (user_id, link, type) VALUES (?,?,?)", (user_id,link,type,))
        await db.execute("UPDATE User SET enable = ? WHERE id = ?", (True, user_id))
        await db.commit()

async def ping_servers(user_id):
    while True:
        if await get_user_status(user_id):
            async with aiosqlite.connect('bot_database.db') as db:
                message = ""
                async with db.execute(f"SELECT User.id, User.enable, User.bot_timeout, Server.link, Server.type FROM User JOIN Server ON User.id = Server.user_id WHERE Server.type = 'web' AND User.id = ?", (user_id,)) as cursor:
                    result = await cursor.fetchall()
                    message += "Серверы:\n"
                    for row in result:
                        user_id, active, bot_timeout, server_link, ping_type = row
                        if active and user_dict[user_id] != 1 and user_dict[user_id] != 2:
                            try:
                                response = requests.get(server_link, timeout=5).status_code
                                if response == 200:
                                    message += f'🟢 {server_link}\n'
                                else:
                                    message += f'🔴 {server_link}\n'
                            except:
                                message += f'🔴 {server_link}\n'
            if user_id in last_message_id:
                try:
                    await bot.delete_message(user_id, last_message_id[user_id])
                except:
                    pass
            sent_message = await bot.send_message(user_id, message, disable_web_page_preview=True)
            last_message_id[user_id] = sent_message.message_id
            await asyncio.sleep(int(result[0][2]))
        else:
            break

def interval_keyboard():
    buttons = [[InlineKeyboardButton(text=name, callback_data=IntervalCallback(name=name).pack())] for name in PING_INTERVALS.keys()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    user_dict[user_id] = 0
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    sent_message = await message.answer("✌️Привет! Я бот для проверки доступности ваших серверов. Пожалуйста, выберите частоту пинга для серверов:", reply_markup=interval_keyboard())
    last_message_id[user_id] = sent_message.message_id

@dp.message(Command("timeout"))
async def timeout_command(message: types.Message):
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    sent_message = await message.answer("Выберите новую частоту пинг-теста для серверов:", reply_markup=interval_keyboard())
    last_message_id[user_id] = sent_message.message_id

@dp.message(Command("add_server"))
async def add_server_command(message: types.Message):
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    link_count = await get_user_link_count(user_id)
    user_limit = await get_user_limit(user_id)
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    if int(link_count) == int(user_limit[0][0]):
        sent_message = await message.answer(f"У вас лимит: {user_limit[0][0]} ссылок")
    else:
        user_dict[message.from_user.id] = 1
        sent_message = await message.answer("Укажите ссылку на сервер")
    last_message_id[user_id] = sent_message.message_id

@dp.message(Command("add_database"))
async def add_database_command(message: types.Message):
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    link_count = await get_user_link_count(user_id)
    user_limit = await get_user_limit(user_id)
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    if link_count == user_limit:
        sent_message = await message.answer(f"У вас лимит: {user_limit[0][0]} ссылок")
    else:
        user_dict[message.from_user.id] = 2
        sent_message = await message.answer("Укажите ссылку на базу данных")
    last_message_id[user_id] = sent_message.message_id

@dp.message(Command("start_ping"))
async def start_ping_command(message: types.Message):
    user_id = message.from_user.id
    current_status = await get_user_status(user_id)
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    if current_status:
        sent_message = await message.answer("Пинг-тест уже запущен! Измените временной интервал на более маленький или подождите!")
    else:
        async with aiosqlite.connect('bot_database.db') as db:
            await db.execute("UPDATE User SET enable = ? WHERE id = ?", (True, user_id))
            await db.commit()
        asyncio.create_task(ping_servers(user_id))
        sent_message = await message.answer("Пинг-тест возобновлен!")
    last_message_id[user_id] = sent_message.message_id

@dp.message(Command("break_ping"))
async def break_ping_command(message: types.Message):
    user_id = message.from_user.id
    current_status = await get_user_status(user_id)
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    if not current_status:
        sent_message = await message.answer("Пинг-тест уже приостановлен!")
    else:
        async with aiosqlite.connect('bot_database.db') as db:
            await db.execute("UPDATE User SET enable = ? WHERE id = ?", (False, user_id))
            await db.commit()
        sent_message = await message.answer("Пинг-тест приостановлен!")
    last_message_id[user_id] = sent_message.message_id

@dp.message(Command("remove_ping"))
async def remove_ping_command(message: types.Message):
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    users_links = await get_user_links(user_id)
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    if len(users_links) != 0:
        buttons = [[InlineKeyboardButton(text=name[0], callback_data=f"{user_id}-{i}")] for i, name in enumerate(users_links)]
        sent_message = await message.answer("Выберите сервер/базу данных из списка, чтобы удалить:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        sent_message = await message.answer("У Вас нет добавленных ссылок!")
    last_message_id[user_id] = sent_message.message_id

@dp.message(Command("fast_ping"))
async def fast_ping_command(message: types.Message):
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    link_count = await get_user_link_count(user_id)
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    if int(link_count) == 0:
        sent_message = await message.answer(f"У вас нет активных ссылок")
    else:
        async with aiosqlite.connect('bot_database.db') as db:
            message = ""
            async with db.execute(f"SELECT User.id, User.enable, User.bot_timeout, Server.link, Server.type FROM User JOIN Server ON User.id = Server.user_id WHERE Server.type = 'web' AND User.id = ?", (user_id,)) as cursor:
                result = await cursor.fetchall()
                message += "Серверы:\n"
                for row in result:
                    user_id, active, bot_timeout, server_link, ping_type = row
                    if active and user_dict[user_id] != 1 and user_dict[user_id] != 2:
                        try:
                            response = requests.get(server_link, timeout=5).status_code
                            if response == 200:
                                message += f'🟢 {server_link}\n'
                            else:
                                message += f'🔴 {server_link}\n'
                        except:
                            message += f'🔴 {server_link}\n'
        sent_message = await bot.send_message(user_id, message, disable_web_page_preview=True)
    last_message_id[user_id] = sent_message.message_id

@dp.callback_query(IntervalCallback.filter())
async def set_interval(callback_query: CallbackQuery, callback_data: IntervalCallback):
    user_id = callback_query.from_user.id
    interval_name = callback_data.name
    bot_timeout = PING_INTERVALS[interval_name]
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute("UPDATE User SET bot_timeout = ?, link_limit = ? WHERE id = ?", (bot_timeout, 5, user_id))
        await db.commit()
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    sent_message = await callback_query.message.answer("Интервал установлен.")
    last_message_id[user_id] = sent_message.message_id

@dp.callback_query()
async def remove_ping(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    button_data = int(callback_query.data.split("-")[1])
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT rowid FROM Server WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            rowid_to_delete = rows[button_data][0]
        await db.execute("DELETE FROM Server WHERE rowid = ?", (rowid_to_delete,))
        await db.commit()
    asyncio.create_task(ping_servers(user_id))
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    sent_message = await callback_query.message.answer(f"Ссылка успешно удалена!")
    last_message_id[user_id] = sent_message.message_id

@dp.message()
async def handle_server_link(message: types.Message):
    user_id = message.from_user.id
    if user_id in last_message_id:
        try:
            await bot.delete_message(user_id, last_message_id[user_id])
        except:
            pass
    if user_dict[user_id] == 1:
        link = message.text.strip()
        if not is_valid_url(link):
            sent_message = await message.answer("Некорректная ссылка. Пожалуйста, укажите корректную URL.")
            return
        existing_link = await get_user_link(user_id, link)
        if existing_link:
            sent_message = await message.answer("Эта ссылка уже добавлена.")
        else:
            await add_user_link(user_id, link, type='web')
            sent_message = await message.answer("Ссылка успешно добавлена.")
        user_dict[user_id] = 0
        last_message_id[user_id] = sent_message.message_id
    elif user_dict[user_id] == 2:
        sent_message = await message.answer("Поддержка баз данных в разработке!")
        # link = message.text.strip()
        # existing_link = await get_user_link(user_id, link)
        # if existing_link:
        #     await message.answer("Эта база данных уже добавлена.")
        # else:
        #     await add_user_link(user_id, link, type='db')
        #     await message.answer("База данных успешно добавлена.")
        user_dict[user_id] = 0
        last_message_id[user_id] = sent_message.message_id
        
if __name__ == "__main__":
    dp.startup.register(init_db)
    dp.startup.register(create_user_list)
    dp.run_polling(bot)
