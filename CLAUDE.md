# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flashgram Bot is a Telegram bot for practicing with flashcards using spaced repetition techniques. The bot is built with Python and uses a conversational AI chatbot as the primary interaction method for Russian language learning.

## Repository Structure

- `app/`: Main source code directory
  - `main.py`: Application entry point with FastAPI server and Telegram bot
  - `config.py`: Application configuration and settings
  - `my_telegram/`: Telegram bot implementation
    - `bot.py`: Bot initialization and callback handlers
    - `handlers/`: Message and command handlers
      - `chatbot_handlers.py`: Conversational chatbot message routing
      - `command_handlers.py`: Bot commands (/start, /help, /learn, etc.)
      - `message_handlers.py`: Message routing and flashcard editing
      - `learning_handlers.py`: Flashcard learning session management
    - `session/`: Session and configuration management
  - `my_graph/`: AI language processing
    - `chatbot_tutor.py`: Main conversational Russian tutor with self-contained grammar analysis tools
    - `flashcard_generator.py`: Flashcard generation from grammar analysis
    - `sentence_generation/`: LLM-powered sentence generation
    - `generators/`: Word-type specific flashcard generators
  - `flashcards/`: Flashcard data models and database
  - `grammar/`: Russian grammar data models
  - `common/`: Shared utilities and text processing
- `requirements.txt`: Python dependencies
- `.env.example`: Example environment variables
- `run.py`: Alternative entry point

## Development Guidelines

### Environment Setup

**IMPORTANT: Always activate the conda environment before running Python code:**

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate flashgram-bot
```

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env file to add your Telegram bot token and OpenAI API key
```

### Running the Bot

To run the bot locally:
```bash
# Activate conda environment first
source ~/miniconda3/etc/profile.d/conda.sh
conda activate flashgram-bot

# Run the bot
python app/main.py
# or alternatively
python run.py
```

### Bot Architecture

The bot now uses a **conversational chatbot as the primary interaction method**:

#### Core Components:
- **ConversationalRussianTutor**: Main AI chatbot with LangGraph tools for:
  - Grammar analysis of Russian words
  - Flashcard generation
  - Text correction and translation
  - Example sentence generation
- **Session Management**: User state tracking for learning modes and configuration
- **Flashcard System**: Spaced repetition learning with multiple card types
- **Legacy Learning Modes**: Flashcard editing, regeneration, and practice sessions

#### Key Features:
- Conversational AI interface for natural language interaction
- Automatic Russian grammar analysis and flashcard generation
- Support for nouns, adjectives, verbs, pronouns, and numbers
- Spaced repetition algorithm for optimal learning
- Interactive flashcard editing and sentence regeneration
- Multi-language support (Russian, English, German)

#### Recent Changes (2024):
- Removed legacy `use_chatbot` configuration flag
- Made conversational chatbot the default and only interaction method
- Cleaned up unused legacy Russian tutor routing code
- Removed unused `/api/analyze/{word}` FastAPI endpoint
- Streamlined bot initialization to focus on chatbot system
- **LATEST**: Eliminated legacy `RussianTutor` class completely - grammar analysis now self-contained in `chatbot_tutor.py`
- Removed `language_tutor.py` file and all dependencies on legacy LangGraph agent

### Development Notes

**Python Environment:**
- Always use `conda activate flashgram-bot` before running any Python code
- The bot requires OpenAI API access for LLM functionality

**Adding New Features:**
- Register new command handlers in `app/my_telegram/bot.py`
- Add new chatbot tools in `app/my_graph/chatbot_tutor.py`
- Follow existing patterns for session management and error handling
- Use the session manager for tracking user state across interactions

**Database:**
- MongoDB is used for flashcard storage and user progress tracking
- Ensure MongoDB is running before starting the bot