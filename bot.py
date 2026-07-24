import asyncio
import logging
from datetime import date

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN, FREE_MESSAGES_PER_DAY
import db
import rag
import ai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

router = Router()

LANG_RU = "ru"
LANG_EN = "en"

user_lang: dict[int, str] = {}


def get_lang(user_id: int) -> str:
    return user_lang.get(user_id, LANG_RU)


def t(user_id: int, ru: str, en: str) -> str:
    return ru if get_lang(user_id) == LANG_RU else en


class SetupStates(StatesGroup):
    waiting_business_name = State()
    waiting_faq = State()
    waiting_welcome = State()
    waiting_prompt = State()


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        ]
    ])


def admin_kb(uid: int) -> InlineKeyboardMarkup:
    ru = get_lang(uid) == LANG_RU
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📚 Добавить знания" if ru else "📚 Add Knowledge",
            callback_data="admin:add_faq",
        )],
        [InlineKeyboardButton(
            text="👋 Приветствие" if ru else "👋 Set Welcome Message",
            callback_data="admin:set_welcome",
        )],
        [InlineKeyboardButton(
            text="🤖 Личность AI" if ru else "🤖 Set AI Personality",
            callback_data="admin:set_prompt",
        )],
        [InlineKeyboardButton(
            text="📊 Статистика" if ru else "📊 Statistics",
            callback_data="admin:stats",
        )],
        [InlineKeyboardButton(
            text="🗑 Очистить базу" if ru else "🗑 Clear Knowledge Base",
            callback_data="admin:clear",
        )],
        [InlineKeyboardButton(
            text="💬 Тест от клиента" if ru else "💬 Test as Customer",
            callback_data="admin:test",
        )],
        [InlineKeyboardButton(
            text="🌐 Language / Язык" ,
            callback_data="admin:lang",
        )],
    ])


# --- выбор языка ---


@router.callback_query(F.data.startswith("lang:"))
async def on_lang_select(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    user_lang[callback.from_user.id] = lang
    uid = callback.from_user.id

    msg = "🇷🇺 Язык изменён на русский!" if lang == LANG_RU else "🇬🇧 Language set to English!"
    await callback.message.edit_text(msg)
    await callback.answer()

    biz = await db.get_business_by_owner(uid)
    if biz:
        await callback.message.answer(
            t(uid, "Панель управления:", "Admin panel:"),
            reply_markup=admin_kb(uid),
        )


@router.callback_query(F.data == "admin:lang")
async def on_change_lang(callback: CallbackQuery):
    uid = callback.from_user.id
    await callback.message.answer(
        t(uid, "Выберите язык:", "Choose language:"),
        reply_markup=lang_kb(),
    )
    await callback.answer()


# --- хендлеры владельца бизнеса ---


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    uid = message.from_user.id
    biz = await db.get_business_by_owner(uid)

    if biz:
        docs = rag.get_doc_count(biz["id"])
        await message.answer(
            t(uid,
              f"👋 С возвращением, <b>{biz['name']}</b>!\n\n"
              f"📚 База знаний: {docs} фрагментов\n"
              f"Используйте панель ниже для управления ботом.",
              f"👋 Welcome back, <b>{biz['name']}</b>!\n\n"
              f"📚 Knowledge base: {docs} chunks\n"
              f"Use the panel below to manage your bot."),
            parse_mode="HTML",
            reply_markup=admin_kb(uid),
        )
        return

    await message.answer(
        "🌐 Выберите язык / Choose language:",
        reply_markup=lang_kb(),
    )

    await message.answer(
        t(uid,
          "👋 <b>Добро пожаловать в SupportBot!</b>\n\n"
          "Я помогу создать AI-бота поддержки для вашего бизнеса.\n\n"
          "Ваши клиенты смогут задавать вопросы и получать мгновенные ответы "
          "на основе вашей базы знаний.\n\n"
          "Начнём! <b>Как называется ваш бизнес?</b>",
          "👋 <b>Welcome to SupportBot!</b>\n\n"
          "I'll help you create an AI-powered support bot for your business.\n\n"
          "Your customers will be able to ask questions and get instant answers "
          "based on your FAQ and knowledge base.\n\n"
          "Let's start! <b>What's your business name?</b>"),
        parse_mode="HTML",
    )
    await state.set_state(SetupStates.waiting_business_name)


@router.message(SetupStates.waiting_business_name)
async def on_business_name(message: Message, state: FSMContext):
    uid = message.from_user.id
    name = message.text.strip()
    if len(name) < 2:
        await message.answer(t(uid, "Слишком короткое название. Попробуйте ещё:", "Name is too short. Try again:"))
        return

    await db.create_business(uid, name)
    await state.clear()

    await message.answer(
        t(uid,
          f"✅ <b>{name}</b> зарегистрирован!\n\n"
          "Теперь добавьте базу знаний — отправьте FAQ, информацию о товарах "
          "или любой текст, по которому клиенты могут задавать вопросы.\n\n"
          "Или используйте панель управления:",
          f"✅ <b>{name}</b> registered!\n\n"
          "Now let's add your knowledge base. Send me your FAQ, product info, "
          "or any text your customers might ask about.\n\n"
          "You can also use the admin panel:"),
        parse_mode="HTML",
        reply_markup=admin_kb(uid),
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    uid = message.from_user.id
    biz = await db.get_business_by_owner(uid)
    if not biz:
        await message.answer(
            t(uid, "У вас ещё нет бизнеса. Используйте /start.", "You don't have a business yet. Use /start to create one.")
        )
        return
    await message.answer(
        t(uid, "Панель управления:", "Admin panel:"),
        reply_markup=admin_kb(uid),
    )


@router.callback_query(F.data == "admin:add_faq")
async def on_add_faq(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    await callback.message.answer(
        t(uid,
          "📚 Отправьте текст для добавления в базу знаний.\n\n"
          "Можно отправить:\n"
          "• Часто задаваемые вопросы (FAQ)\n"
          "• Описания товаров/услуг\n"
          "• Информацию о ценах\n"
          "• Любую информацию для клиентов\n\n"
          "Отправьте /done когда закончите.",
          "📚 Send me text to add to your knowledge base.\n\n"
          "You can send:\n"
          "• FAQ text\n"
          "• Product descriptions\n"
          "• Pricing info\n"
          "• Any information your customers ask about\n\n"
          "Send /done when finished.")
    )
    await state.set_state(SetupStates.waiting_faq)
    await callback.answer()


@router.message(SetupStates.waiting_faq, Command("done"))
async def on_faq_done(message: Message, state: FSMContext):
    uid = message.from_user.id
    biz = await db.get_business_by_owner(uid)
    docs = rag.get_doc_count(biz["id"]) if biz else 0
    await state.clear()
    await message.answer(
        t(uid,
          f"✅ База знаний обновлена! Всего: {docs} фрагментов.\n\n"
          "Бот готов отвечать на вопросы клиентов.",
          f"✅ Knowledge base updated! Total: {docs} chunks.\n\n"
          "Your bot is ready to answer customer questions."),
        reply_markup=admin_kb(uid),
    )


@router.message(SetupStates.waiting_faq)
async def on_faq_text(message: Message):
    uid = message.from_user.id
    biz = await db.get_business_by_owner(uid)
    if not biz:
        await message.answer(t(uid, "Ошибка: бизнес не найден.", "Error: business not found."))
        return

    text = message.text or ""
    if len(text) < 10:
        await message.answer(
            t(uid, "Текст слишком короткий. Отправьте более подробную информацию.", "Text is too short. Send more detailed information.")
        )
        return

    count = await asyncio.to_thread(rag.add_document, biz["id"], text)
    total = rag.get_doc_count(biz["id"])
    await message.answer(
        t(uid,
          f"✅ Добавлено {count} фрагментов (всего: {total}).\n"
          "Отправьте ещё текст или /done для завершения.",
          f"✅ Added {count} chunks (total: {total}).\n"
          "Send more text or /done to finish.")
    )


@router.callback_query(F.data == "admin:set_welcome")
async def on_set_welcome(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    await callback.message.answer(
        t(uid,
          "👋 Отправьте приветственное сообщение, которое увидят ваши клиенты.\n\n"
          "Пример: \"Привет! Я бот-помощник магазина CoolShop. Спрашивайте о наших товарах!\"",
          "👋 Send the welcome message your customers will see when they start the bot.\n\n"
          "Example: \"Hi! I'm the support assistant for CoolShop. Ask me anything about our products!\"")
    )
    await state.set_state(SetupStates.waiting_welcome)
    await callback.answer()


@router.message(SetupStates.waiting_welcome)
async def on_welcome_text(message: Message, state: FSMContext):
    uid = message.from_user.id
    await db.update_business(uid, welcome_message=message.text)
    await state.clear()
    await message.answer(
        t(uid, "✅ Приветствие сохранено!", "✅ Welcome message saved!"),
        reply_markup=admin_kb(uid),
    )


@router.callback_query(F.data == "admin:set_prompt")
async def on_set_prompt(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    await callback.message.answer(
        t(uid,
          "🤖 Задайте личность AI для вашего бота поддержки.\n\n"
          "Пример: \"Ты дружелюбный помощник магазина CoolShop, "
          "интернет-магазина электроники. Отвечай полезно, кратко и профессионально.\"",
          "🤖 Set the AI personality for your support bot.\n\n"
          "Example: \"You are a friendly support agent for CoolShop, an online electronics store. "
          "Be helpful, concise, and professional. Answer in the customer's language.\"")
    )
    await state.set_state(SetupStates.waiting_prompt)
    await callback.answer()


@router.message(SetupStates.waiting_prompt)
async def on_prompt_text(message: Message, state: FSMContext):
    uid = message.from_user.id
    await db.update_business(uid, system_prompt=message.text)
    await state.clear()
    await message.answer(
        t(uid, "✅ Личность AI сохранена!", "✅ AI personality saved!"),
        reply_markup=admin_kb(uid),
    )


@router.callback_query(F.data == "admin:stats")
async def on_stats(callback: CallbackQuery):
    uid = callback.from_user.id
    biz = await db.get_business_by_owner(uid)
    if not biz:
        await callback.answer(t(uid, "Бизнес не найден", "No business found"))
        return

    stats = await db.get_stats(biz["id"])
    docs = rag.get_doc_count(biz["id"])

    await callback.message.answer(
        t(uid,
          f"📊 <b>Статистика {biz['name']}</b>\n\n"
          f"📚 База знаний: {docs} фрагментов\n"
          f"💬 Всего сообщений: {stats['total_messages']}\n"
          f"👥 Уникальных пользователей: {stats['unique_users']}\n"
          f"📅 Сегодня: {stats['today']} сообщений",
          f"📊 <b>Stats for {biz['name']}</b>\n\n"
          f"📚 Knowledge base: {docs} chunks\n"
          f"💬 Total messages: {stats['total_messages']}\n"
          f"👥 Unique users: {stats['unique_users']}\n"
          f"📅 Today: {stats['today']} messages"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:clear")
async def on_clear(callback: CallbackQuery):
    uid = callback.from_user.id
    biz = await db.get_business_by_owner(uid)
    if not biz:
        await callback.answer(t(uid, "Бизнес не найден", "No business found"))
        return

    await asyncio.to_thread(rag.clear_knowledge, biz["id"])
    await callback.message.answer(
        t(uid, "🗑 База знаний очищена.", "🗑 Knowledge base cleared."),
        reply_markup=admin_kb(uid),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:test")
async def on_test(callback: CallbackQuery):
    uid = callback.from_user.id
    await callback.message.answer(
        t(uid,
          "💬 Режим тестирования — задайте вопрос как клиент.\n"
          "Отправьте /admin чтобы вернуться в панель.",
          "💬 Test mode — send a question as if you were a customer.\n"
          "Send /admin to go back to the panel.")
    )
    await callback.answer()


# --- обработка сообщений от клиентов ---


@router.message(F.text)
async def on_message(message: Message):
    uid = message.from_user.id
    biz = await db.get_business_by_owner(uid)

    if biz:
        if rag.get_doc_count(biz["id"]) == 0:
            await message.answer(
                t(uid, "База знаний пуста. Сначала добавьте контент:", "Your knowledge base is empty. Add content first:"),
                reply_markup=admin_kb(uid),
            )
            return

        thinking = await message.answer("⏳")
        answer = await asyncio.to_thread(
            ai.answer_question, biz["id"], message.text, biz.get("system_prompt", "")
        )
        await thinking.delete()
        await message.answer(answer)
        await db.log_message(biz["id"], uid, message.text, answer)
        return

    await message.answer(
        t(uid,
          "👋 Добро пожаловать! Я SupportBot.\n\n"
          "Если вы владелец бизнеса — /start для создания AI-бота поддержки.\n"
          "Если вы клиент — используйте ссылку от бизнеса.",
          "👋 Welcome! I'm SupportBot.\n\n"
          "If you're a business owner, use /start to create your AI support bot.\n"
          "If you're a customer, use the direct link provided by the business.")
    )


# --- запуск ---


async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать / Start"),
        BotCommand(command="admin", description="Панель управления / Admin panel"),
    ])


async def main():
    await db.init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await set_commands(bot)
    logger.info("SupportBot SaaS started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
