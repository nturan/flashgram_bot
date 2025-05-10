# Flashgram Bot

A Telegram bot to practice with flashcards using spaced repetition techniques.

## Features

- Practice flashcards via Telegram
- Spaced repetition algorithm to optimize learning
- Simple command-based interface

## Local Development

### Prerequisites

- Python 3.11+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))

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

3. Set the TELEGRAM_BOT_TOKEN environment variable with your bot token.

### Running Locally

Start the bot in polling mode:
```bash
python src/bot.py
```

## Docker

To run the bot using Docker:

```bash
# Build the Docker image
docker build -t flashgram-bot .

# Run the container
docker run -e TELEGRAM_BOT_TOKEN=your_token_here flashgram-bot
```
