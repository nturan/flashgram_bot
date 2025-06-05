# Flashgram Bot

A Telegram bot that helps you learn Russian language using LangGraph and AI.

## Features

- Analyze Russian nouns for grammar details
- Get case forms, gender, and other grammar information
- API endpoint for word analysis
- FastAPI web server running alongside the bot

## Local Development

### Prerequisites

- Python 3.11+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nturan/flashgram_bot.git
   cd flashgram_bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   LLM_MODEL=gpt-4o  # Optional, defaults to gpt-4o
   ```

### Running Locally

Start the bot and API server:
```bash
python run.py
```

## API Usage

The bot also exposes an API endpoint:

- `GET /api/analyze/{word}` - Analyzes a Russian word and returns its grammar details

Example:
```bash
curl http://localhost:8080/api/analyze/книга
```

## Docker

To run the bot using Docker:

```bash
# Build the Docker image
docker build -t flashgram-bot .

# Run the container
docker run -e TELEGRAM_BOT_TOKEN=your_token_here -e OPENAI_API_KEY=your_key_here flashgram-bot
```

## How It Works

1. The bot receives a Russian noun from a user via Telegram
2. The message is processed through a LangGraph workflow:
   - First, the word is classified by part of speech
   - Then, detailed grammar information is retrieved
3. The result is formatted and sent back to the user as a Telegram message
