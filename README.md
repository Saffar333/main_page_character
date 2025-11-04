# WebApp Secure - AI Characters Platform

Secure Telegram Web App для выбора и создания AI персонажей с гибридной системой аутентификации.

## 🎯 Особенности

- **Гибридная аутентификация**: URL параметр + Telegram Web App API
- **Base64 кодирование**: Безопасная передача telegram_id через URL
- **Двойная валидация**: Проверка соответствия ID из URL и Telegram
- **Real-time обновления**: Синхронизация через Supabase Realtime
- **Адаптивный дизайн**: Оптимизирован для мобильных устройств
- **Telegram-нативный UI**: Использование цветовой схемы Telegram

## 📁 Структура проекта

```
webapp-secure/
├── index.html          # Главная страница (персонажи + профиль)
├── create.html         # Страница создания персонажа
├── config.js           # Конфигурация Supabase
├── js/
│   ├── auth.js        # Функции Base64 кодирования/декодирования
│   ├── app.js         # Основная логика приложения
│   └── create.js      # Логика создания персонажа
├── bot-example.py     # Пример использования в aiogram
├── vercel.json        # Конфигурация Vercel
└── README.md          # Документация
```

## 🚀 Быстрый старт

### 1. Настройка Supabase

1. Создайте проект на [supabase.com](https://supabase.com)
2. Создайте таблицы в БД:

```sql
-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    active_character_id INTEGER,
    total_message_count INTEGER DEFAULT 0,
    daily_message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP
);

-- Таблица персонажей
CREATE TABLE characters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    personality TEXT NOT NULL,
    greeting_message TEXT NOT NULL,
    avatar_url VARCHAR(512),
    is_preset BOOLEAN NOT NULL DEFAULT false,
    creator_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- Таблица диалогов
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    character_id INTEGER NOT NULL REFERENCES characters(id),
    created_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    summary TEXT
);
```

3. Создайте Storage bucket для аватаров:
   - Название: `character-avatars`
   - Public: да
   - Allowed MIME types: `image/*`

### 2. Конфигурация

Отредактируйте `config.js`:

```javascript
const CONFIG = {
    SUPABASE_URL: 'https://your-project.supabase.co',
    SUPABASE_ANON_KEY: 'your-anon-key',
    SECRET_KEY: 'your-secret-key-2025'
};
```

### 3. Деплой на Vercel

```bash
# Установите Vercel CLI
npm i -g vercel

# Деплой
cd webapp-secure
vercel
```

Или подключите GitHub репозиторий к Vercel для автоматического деплоя.

### 4. Настройка бота

Используйте `bot-example.py` как основу:

```python
import base64
from aiogram.types import WebAppInfo, InlineKeyboardButton

# Конфигурация
WEBAPP_URL = "https://your-site.vercel.app/webapp-secure"

# Кодирование telegram_id
def encode_telegram_id(telegram_id: int) -> str:
    return base64.b64encode(str(telegram_id).encode()).decode()

# Создание URL
def create_webapp_url(telegram_id: int) -> str:
    encoded_id = encode_telegram_id(telegram_id)
    return f"{WEBAPP_URL}?user={encoded_id}"

# Отправка кнопки
telegram_id = message.from_user.id
webapp_url = create_webapp_url(telegram_id)

keyboard = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(
        text="🎭 Выбрать персонажа",
        web_app=WebAppInfo(url=webapp_url)
    )
]])
```

## 📖 Как это работает

### Архитектура гибридной аутентификации

```
┌─────────────────────────────────────────────────────────────┐
│  1. БОТ                                                     │
│  - Кодирует telegram_id в Base64                           │
│  - Создает URL: ?user=ENCODED_ID                           │
│  - Отправляет через WebAppInfo (кнопка)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. WEBAPP                                                  │
│  - Декодирует telegram_id из URL                           │
│  - Получает tg.initDataUnsafe.user.id                      │
│  - Валидирует совпадение (опционально)                     │
│  - Использует URL telegram_id как основной                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. SUPABASE                                                │
│  - Загружает данные пользователя                           │
│  - Загружает персонажей (публичные + личные)               │
│  - Сохраняет созданных персонажей                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  4. ВЫБОР ПЕРСОНАЖА                                         │
│  - Использует tg.sendData() для отправки в бот             │
│  - Бот получает данные через web_app_data                  │
│  - Сохраняет выбор в БД                                    │
└─────────────────────────────────────────────────────────────┘
```

### Процесс выбора персонажа

1. **Пользователь открывает приложение**
   - Бот создает URL с закодированным ID
   - Отправляет через WebAppInfo кнопку

2. **Приложение декодирует ID**
   - `getTelegramIdFromURL()` декодирует Base64
   - Загружает данные пользователя из Supabase
   - Отображает персонажей (публичные + личные)

3. **Выбор персонажа**
   - Пользователь нажимает на карточку
   - `selectCharacter()` формирует данные
   - `tg.sendData()` отправляет в бот

4. **Бот обрабатывает выбор**
   - Получает через `@dp.message(F.web_app_data)`
   - Сохраняет выбор в БД
   - Начинает диалог с персонажем

## 🎨 Функциональность

### Главная страница (index.html)

**Навигация:**
- Верхняя: заголовок + кнопка "+" (создать персонажа)
- Нижняя: "Персонажи" / "Профиль"

**Табы персонажей:**
- **Публичные**: `is_preset = true`
- **Личные**: `is_preset = false AND creator_id = user.id`

**Карточка персонажа:**
- Аватар (изображение или первая буква имени)
- Имя
- Краткое описание (до 80 символов)
- При клике: отправка данных в бот через `tg.sendData()`

**Профиль:**
- Аватар пользователя
- Имя, username
- Статистика:
  - `total_message_count` - всего сообщений
  - `daily_message_count` - сообщений сегодня
- Дополнительная информация:
  - Telegram ID
  - Username
  - Язык
  - Premium статус
  - Платформа

### Создание персонажа (create.html)

**Форма:**
- **Имя** (обязательно, макс 100 символов)
- **Описание** (обязательно, макс 500 символов)
- **Личность** (обязательно, макс 1000 символов)
- **Приветственное сообщение** (обязательно, макс 500 символов)
- **Аватар** (необязательно, макс 5 МБ)
- **Публичный персонаж** (чекбокс)

**Процесс создания:**
1. Валидация данных
2. Поиск пользователя в БД по telegram_id
3. Создание персонажа в таблице `characters`
4. Загрузка аватара в Supabase Storage (если выбран)
5. Обновление URL аватара
6. Перенаправление на главную страницу

## 📊 База данных

### Таблица `users`

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | ID пользователя (PK) |
| telegram_id | BIGINT | ID в Telegram (UNIQUE) |
| username | VARCHAR(255) | Username |
| first_name | VARCHAR(255) | Имя |
| created_at | TIMESTAMP | Дата регистрации |
| last_active | TIMESTAMP | Последняя активность |
| active_character_id | INTEGER | Активный персонаж (FK) |
| total_message_count | INTEGER | Всего сообщений |
| daily_message_count | INTEGER | Сообщений сегодня |
| last_message_at | TIMESTAMP | Последнее сообщение |

### Таблица `characters`

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | ID персонажа (PK) |
| name | VARCHAR(255) | Имя персонажа |
| description | TEXT | Описание |
| personality | TEXT | Личность |
| greeting_message | TEXT | Приветствие |
| avatar_url | VARCHAR(512) | URL аватара |
| is_preset | BOOLEAN | Публичный персонаж |
| creator_id | INTEGER | Создатель (FK) |
| created_at | TIMESTAMP | Дата создания |
| is_active | BOOLEAN | Активен |

### Таблица `conversations`

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | ID диалога (PK) |
| user_id | INTEGER | Пользователь (FK) |
| character_id | INTEGER | Персонаж (FK) |
| created_at | TIMESTAMP | Начало диалога |
| last_message_at | TIMESTAMP | Последнее сообщение |
| message_count | INTEGER | Количество сообщений |
| summary | TEXT | Краткое содержание |

## 🔐 Безопасность

### Base64 кодирование

**Преимущества:**
- ✅ Простота реализации
- ✅ Нет зависимостей
- ✅ Работает в браузере и Python
- ✅ Обратимое кодирование

**Ограничения:**
- ⚠️ Легко декодируется (не шифрование!)
- ⚠️ Подходит только для передачи ID, не секретных данных

**Для большей безопасности:**
- Используйте JWT токены с секретным ключом
- Проверяйте `tg.initDataUnsafe.hash` на сервере
- Ограничивайте доступ к данным по telegram_id

### Валидация

```javascript
// В app.js
const urlTelegramId = getTelegramIdFromURL();
const tgTelegramId = tg.initDataUnsafe?.user?.id;

if (urlTelegramId && tgTelegramId) {
    validateTelegramId(urlTelegramId, tgTelegramId);
}
```

Это обеспечивает дополнительную проверку соответствия ID.

## 🛠 Разработка

### Локальное тестирование

```bash
# Запустите локальный сервер
python -m http.server 8000

# Откройте в браузере
http://localhost:8000/index.html?user=MTIzNDU2Nzg5
```

**Примечание:** Telegram Web App API работает только внутри Telegram!

### Отладка

Включите логирование в консоли:
```javascript
console.log('🚀 Инициализация приложения...');
console.log('👤 Telegram User:', tg.initDataUnsafe?.user);
console.log('🔗 Telegram ID из URL:', urlTelegramId);
```

## 📝 TODO

- [ ] Добавить JWT токены вместо Base64
- [ ] Реализовать поиск персонажей
- [ ] Добавить категории персонажей
- [ ] Реализовать рейтинг персонажей
- [ ] Добавить возможность редактирования персонажей
- [ ] Реализовать удаление персонажей
- [ ] Добавить историю диалогов
- [ ] Реализовать экспорт диалогов

## 📄 Лицензия

MIT

## 🤝 Поддержка

Если у вас возникли вопросы:
- Откройте Issue на GitHub
- Напишите в Telegram: @your_support

## 🎉 Благодарности

- [Telegram Web Apps](https://core.telegram.org/bots/webapps)
- [Supabase](https://supabase.com)
- [aiogram](https://docs.aiogram.dev)
- [Vercel](https://vercel.com)
