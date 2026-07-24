# SupportBot SaaS

AI-powered customer support bot for Telegram. Business owners upload their FAQ and knowledge base — the bot answers customer questions instantly using AI.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)

## What it does

1. **Business owner** registers via `/start`, uploads FAQ/product info
2. **AI learns** the knowledge base and answers customer questions based on it
3. **Customers** ask questions in Telegram — get instant, accurate answers 24/7

No coding required. Just send your FAQ as text — the bot does the rest.

## Screenshots

<!-- TODO: add screenshots -->
<!-- ![Start screen](screenshots/start.png) -->
<!-- ![Admin panel](screenshots/admin.png) -->
<!-- ![Customer chat](screenshots/chat.png) -->

## Features

- **Knowledge base** — send any text (FAQ, product info, pricing) and the bot learns it
- **AI answers** — powered by LLaMA 3.3 70B, answers only from your knowledge base
- **Bilingual** — Russian and English interface, switchable anytime
- **Admin panel** — manage knowledge base, set welcome message, customize AI personality
- **Statistics** — track total messages, unique users, daily activity
- **Test mode** — try the bot as a customer before going live
- **Free to run** — uses Groq API (free tier), no OpenAI costs

## Tech stack

- Python 3.12+ / aiogram 3.x
- Groq API (LLaMA 3.3 70B) — free
- SQLite for business data and analytics
- Keyword-based RAG for knowledge retrieval

## Setup

```bash
git clone https://github.com/9kaBAN4ik/support-bot-saas.git
cd support-bot-saas
pip install -r requirements.txt
```

Create `.env` from the example:

```bash
cp .env.example .env
```

Fill in your tokens:

```
TELEGRAM_BOT_TOKEN=your_bot_token
GROQ_API_KEY=your_groq_key
```

Get a bot token from [@BotFather](https://t.me/BotFather) and a free Groq API key from [console.groq.com](https://console.groq.com).

Run:

```bash
python bot.py
```

## Project structure

```
├── bot.py           # Telegram bot (admin + customer handlers)
├── ai.py            # AI response generation via Groq
├── rag.py           # Knowledge base search engine
├── db.py            # SQLite database (businesses, stats)
├── config.py        # Configuration
├── requirements.txt
└── .env.example
```

## How it works

1. Owner sends text to the bot → text is split into chunks and indexed
2. Customer asks a question → bot searches the knowledge base for relevant chunks
3. Relevant chunks + question are sent to LLaMA 3.3 70B → AI generates an answer based only on the knowledge base
4. If the answer isn't in the knowledge base, the bot says so and suggests contacting support directly

## License

MIT
