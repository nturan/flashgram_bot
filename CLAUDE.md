# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flashgram Bot is a Telegram bot for practicing with flashcards using spaced repetition techniques. The bot is built with Python and the python-telegram-bot library.

## Repository Structure

- `src/`: Source code directory
  - `bot.py`: Main bot implementation
- `requirements.txt`: Python dependencies
- `.env.example`: Example environment variables (copy to `.env` for local development)
- `README.md`: Project documentation
- `LICENSE`: Project license information

## Development Guidelines

### Environment Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env file to add your Telegram bot token
```

### Running the Bot

To run the bot locally:
```bash
python src/bot.py
```

### Bot Architecture

The current implementation includes:
- Basic command handlers (/start, /help)
- Message echo functionality
- Logging configuration

When adding new features:
- Register new command handlers in the main() function
- Implement handler functions following the existing pattern
- Use the CallbackContext for sharing data between handlers
- Follow python-telegram-bot patterns for keyboard menus and callbacks