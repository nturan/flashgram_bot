from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import json
from pydantic import SecretStr
import logging

from app.my_graph.language_tutor import RussianTutor

# Get module-level logger
logger = logging.getLogger(__name__)

# This will be initialized in init_application
russian_tutor = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm a Russian language tutor bot. Send me a Russian noun, and I'll analyze its grammar for you.",
        reply_markup=ForceReply(selective=True)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "I can help you learn Russian grammar!\n\n"
        "Just send me a Russian noun, and I'll tell you all about its gender, cases, and forms.\n\n"
        "For example, try sending me 'книга' (book) or 'стол' (table)."
    )

async def process_russian_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the Russian word using the language tutor."""
    user_text = update.message.text

    # Send a typing action
    await update.message.chat.send_action(action="typing")

    try:
        # Get the result from the Russian tutor
        result = russian_tutor.invoke(user_text)

        if "final_answer" in result and result["final_answer"]:
            # Try to parse JSON from the final answer
            try:
                grammar_data = json.loads(result["final_answer"])

                # Format a nice response for the user
                response = (
                    f"📝 *Word:* {grammar_data['dictionary_form']}\n"
                    f"🔤 *Gender:* {grammar_data['gender']}\n"
                    f"🧬 *Animacy:* {'Animate' if grammar_data['animacy'] else 'Inanimate'}\n"
                    f"🇬🇧 *English:* {grammar_data['english_translation']}\n\n"
                    f"*Singular Forms:*\n"
                    f"• Nom: {grammar_data['singular']['nom']}\n"
                    f"• Gen: {grammar_data['singular']['gen']}\n"
                    f"• Dat: {grammar_data['singular']['dat']}\n"
                    f"• Acc: {grammar_data['singular']['acc']}\n"
                    f"• Ins: {grammar_data['singular']['ins']}\n"
                    f"• Pre: {grammar_data['singular']['pre']}\n\n"
                    f"*Plural Forms:*\n"
                    f"• Nom: {grammar_data['plural']['nom']}\n"
                    f"• Gen: {grammar_data['plural']['gen']}\n"
                    f"• Dat: {grammar_data['plural']['dat']}\n"
                    f"• Acc: {grammar_data['plural']['acc']}\n"
                    f"• Ins: {grammar_data['plural']['ins']}\n"
                    f"• Pre: {grammar_data['plural']['pre']}"
                )

                await update.message.reply_markdown(response)
            except json.JSONDecodeError:
                # If we can't parse JSON, just send the raw result
                await update.message.reply_text(f"Analysis result:\n\n{result['final_answer']}")
        else:
            await update.message.reply_text("I couldn't analyze that word. Please try again with a Russian noun.")

    except Exception as e:
        logger.error(f"Error processing word: {str(e)}")
        await update.message.reply_text("Sorry, I encountered an error processing your request. Please try again.")

def init_application(token: str, tutor: RussianTutor) -> Application:
    """Start the bot with the Russian tutor."""
    global russian_tutor
    russian_tutor = tutor

    # Create the Application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_russian_word))

    return application
