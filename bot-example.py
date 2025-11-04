"""
Пример использования webapp-secure с aiogram 3.x

Этот файл показывает, как интегрировать webapp-secure в вашего Telegram бота.
"""

import base64
import json
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# ======================
# КОНФИГУРАЦИЯ
# ======================

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
WEBAPP_URL = "https://your-site.vercel.app/webapp-secure"  # Замените на ваш URL

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================
# ФУНКЦИИ ДЛЯ РАБОТЫ С BASE64
# ======================

def encode_telegram_id(telegram_id: int) -> str:
    """
    Кодирует telegram_id в Base64

    Args:
        telegram_id: ID пользователя в Telegram

    Returns:
        Закодированная строка в Base64
    """
    return base64.b64encode(str(telegram_id).encode()).decode()


def decode_telegram_id(encoded_id: str) -> int:
    """
    Декодирует telegram_id из Base64

    Args:
        encoded_id: Закодированная строка в Base64

    Returns:
        Декодированный telegram_id
    """
    return int(base64.b64decode(encoded_id).decode())


def create_webapp_url(telegram_id: int) -> str:
    """
    Создает URL для Web App с закодированным telegram_id

    Args:
        telegram_id: ID пользователя в Telegram

    Returns:
        Полный URL с параметром ?user=ENCODED_ID
    """
    encoded_id = encode_telegram_id(telegram_id)
    return f"{WEBAPP_URL}?user={encoded_id}"

# ======================
# ХЕНДЛЕРЫ
# ======================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start
    Отправляет кнопку для открытия Web App с персонажами
    """
    telegram_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Пользователь"

    # Создаем URL с закодированным telegram_id
    webapp_url = create_webapp_url(telegram_id)

    print(f"👤 Пользователь: {first_name} (@{username}, ID: {telegram_id})")
    print(f"🔗 Сгенерирован URL: {webapp_url}")

    # Создаем клавиатуру с Web App кнопкой
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎭 Выбрать персонажа",
            web_app=WebAppInfo(url=webapp_url)
        )]
    ])

    await message.answer(
        f"Привет, {first_name}! 👋\n\n"
        f"Выбери персонажа для общения из нашей коллекции.\n"
        f"У нас есть публичные персонажи и ты можешь создать своего!",
        reply_markup=keyboard
    )


@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """
    Обработчик команды /profile
    Открывает страницу профиля пользователя
    """
    telegram_id = message.from_user.id
    webapp_url = create_webapp_url(telegram_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="👤 Мой профиль",
            web_app=WebAppInfo(url=webapp_url)
        )]
    ])

    await message.answer(
        "Открой свой профиль, чтобы посмотреть статистику:",
        reply_markup=keyboard
    )


@dp.message(Command("create"))
async def cmd_create(message: types.Message):
    """
    Обработчик команды /create
    Открывает страницу создания персонажа
    """
    telegram_id = message.from_user.id
    encoded_id = encode_telegram_id(telegram_id)
    create_url = f"{WEBAPP_URL}/create.html?user={encoded_id}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ Создать персонажа",
            web_app=WebAppInfo(url=create_url)
        )]
    ])

    await message.answer(
        "Создай своего уникального персонажа!",
        reply_markup=keyboard
    )


@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    """
    Обработчик данных от Web App
    Получает выбранного персонажа и сохраняет его в БД
    """
    try:
        # Парсим данные от Web App
        data = json.loads(message.web_app_data.data)

        print("📥 Получены данные от Web App:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        action = data.get('action')

        if action == 'select_character':
            # Пользователь выбрал персонажа
            character_id = data['character_id']
            character_name = data['character_name']
            character_description = data.get('character_description', '')
            character_avatar = data.get('character_avatar')
            telegram_id = data['telegram_id']
            username = data.get('username')
            first_name = data.get('first_name')

            print(f"✅ Персонаж выбран: {character_name} (ID: {character_id})")
            print(f"👤 Пользователь: {first_name} (@{username}, ID: {telegram_id})")

            # TODO: Сохраните выбор персонажа в вашу БД
            # await db.update_user_character(telegram_id, character_id)

            # Отправляем подтверждение
            await message.answer(
                f"✅ Ты выбрал персонажа: <b>{character_name}</b>\n\n"
                f"{character_description}\n\n"
                f"Теперь можешь начать общение! Просто напиши сообщение.",
                parse_mode="HTML"
            )

        else:
            print(f"⚠️ Неизвестное действие: {action}")
            await message.answer("Данные получены, но действие не распознано.")

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        await message.answer("Ошибка обработки данных от приложения.")
    except Exception as e:
        print(f"❌ Ошибка обработки данных: {e}")
        await message.answer("Произошла ошибка при обработке выбора.")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """
    Обработчик команды /help
    Показывает список доступных команд
    """
    help_text = (
        "📚 <b>Доступные команды:</b>\n\n"
        "/start - Выбрать персонажа для общения\n"
        "/profile - Посмотреть свой профиль и статистику\n"
        "/create - Создать своего персонажа\n"
        "/help - Показать эту справку\n\n"
        "💡 <b>Как это работает?</b>\n"
        "1. Выбери персонажа из списка или создай своего\n"
        "2. Начни общение, просто написав сообщение\n"
        "3. Персонаж ответит в своем уникальном стиле!"
    )

    await message.answer(help_text, parse_mode="HTML")

# ======================
# ПРИМЕР: Обработка обычных сообщений
# ======================

@dp.message(F.text)
async def handle_message(message: types.Message):
    """
    Обработчик обычных текстовых сообщений
    Здесь должна быть логика общения с выбранным персонажем
    """
    telegram_id = message.from_user.id
    user_message = message.text

    # TODO: Получите активного персонажа пользователя из БД
    # active_character = await db.get_user_active_character(telegram_id)

    # TODO: Сгенерируйте ответ от персонажа через AI
    # response = await ai.generate_response(active_character, user_message)

    # Для примера просто отправляем эхо
    await message.answer(
        f"Ты написал: {user_message}\n\n"
        f"💡 Выбери персонажа командой /start, чтобы начать общение!"
    )

# ======================
# ЗАПУСК БОТА
# ======================

async def main():
    """
    Основная функция для запуска бота
    """
    print("🚀 Бот запущен!")
    print(f"🌐 Web App URL: {WEBAPP_URL}")
    print("⏳ Ожидание сообщений...")

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Запуск бота
    asyncio.run(main())


# ======================
# ДОПОЛНИТЕЛЬНЫЕ ПРИМЕРЫ
# ======================

"""
Пример 1: Проверка кодирования/декодирования
-----------------------------------------
telegram_id = 123456789
encoded = encode_telegram_id(telegram_id)
print(f"Encoded: {encoded}")  # MTIzNDU2Nzg5

decoded = decode_telegram_id(encoded)
print(f"Decoded: {decoded}")  # 123456789


Пример 2: Создание URL для разных страниц
----------------------------------------
# Главная страница
main_url = create_webapp_url(telegram_id)
# https://your-site.com/webapp-secure?user=MTIzNDU2Nzg5

# Страница создания персонажа
encoded_id = encode_telegram_id(telegram_id)
create_url = f"{WEBAPP_URL}/create.html?user={encoded_id}"
# https://your-site.com/webapp-secure/create.html?user=MTIzNDU2Nzg5


Пример 3: Отправка кнопки с Web App
----------------------------------
keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="🎭 Персонажи",
        web_app=WebAppInfo(url=create_webapp_url(telegram_id))
    )],
    [InlineKeyboardButton(
        text="👤 Профиль",
        web_app=WebAppInfo(url=create_webapp_url(telegram_id))
    )],
    [InlineKeyboardButton(
        text="➕ Создать",
        web_app=WebAppInfo(url=f"{WEBAPP_URL}/create.html?user={encode_telegram_id(telegram_id)}")
    )]
])


Пример 4: Обработка данных от Web App
------------------------------------
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    data = json.loads(message.web_app_data.data)

    if data['action'] == 'select_character':
        character_id = data['character_id']
        telegram_id = data['telegram_id']

        # Сохраняем в БД
        await db.users.update_one(
            {'telegram_id': telegram_id},
            {'$set': {'active_character_id': character_id}}
        )

        await message.answer(f"Персонаж выбран: {data['character_name']}")
"""
