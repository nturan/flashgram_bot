"""Message handlers for the conversational chatbot system."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.my_telegram.session import session_manager
from app.my_telegram.session.config_manager import config_manager
from app.my_graph.chatbot_tutor import ConversationalRussianTutor
from app.common.telegram_utils import safe_send_markdown
from .learning_handlers import process_answer
from app.config import settings
from pydantic import SecretStr

logger = logging.getLogger(__name__)

# Per-user chatbot instances
user_chatbots: dict[int, ConversationalRussianTutor] = {}


def get_user_chatbot(user_id: int) -> ConversationalRussianTutor:
    """Get or create a chatbot instance for a specific user."""
    # Check if user has an API key configured
    api_key = config_manager.get_setting(user_id, "openai_api_key")
    if not api_key:
        raise ValueError("User has no API key configured")
    
    # Get user's preferred model
    model = config_manager.get_setting(user_id, "model") or "gpt-4o"
    
    # Create or update chatbot for this user
    if user_id not in user_chatbots:
        logger.info(f"Creating new chatbot for user {user_id} with model: {model}")
        user_chatbots[user_id] = ConversationalRussianTutor(
            api_key=SecretStr(api_key), model=model
        )
    else:
        # Check if we need to update the API key or model
        existing_chatbot = user_chatbots[user_id]
        current_model = existing_chatbot.default_model
        current_api_key = existing_chatbot.api_key.get_secret_value()
        
        if current_api_key != api_key or current_model != model:
            logger.info(f"Updating chatbot for user {user_id} with model: {model}")
            user_chatbots[user_id] = ConversationalRussianTutor(
                api_key=SecretStr(api_key), model=model
            )
    
    return user_chatbots[user_id]


def clear_user_chatbot(user_id: int):
    """Clear chatbot instance for a user (useful when settings change)."""
    if user_id in user_chatbots:
        del user_chatbots[user_id]
        logger.info(f"Cleared chatbot instance for user {user_id}")


def set_chatbot_tutor(tutor: ConversationalRussianTutor):
    """Legacy method for backward compatibility."""
    logger.warning("set_chatbot_tutor is deprecated, using per-user chatbots")


def reinit_chatbot_with_model(model: str):
    """Legacy method for backward compatibility - now clears all chatbots to force recreation."""
    global user_chatbots
    logger.info(f"Model changed to {model}, clearing all chatbot instances for recreation")
    user_chatbots.clear()


async def handle_chatbot_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle messages using the conversational chatbot system."""
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    # Debug logging to track session state
    logger.info(
        f"Chatbot message routing for user {user_id}: regenerating={session.regenerating_mode}, editing={session.editing_mode}, learning={session.learning_mode}"
    )

    # Check if user is in regeneration mode
    if session.regenerating_mode:
        logger.info(f"Routing to regeneration handler for user {user_id}")
        from .message_handlers import process_regeneration_hint

        await process_regeneration_hint(update, context)
        return

    # Check if user is in editing mode
    elif session.editing_mode:
        logger.info(f"Routing to editing handler for user {user_id}")
        from .message_handlers import process_flashcard_edit

        await process_flashcard_edit(update, context)
        return

    # Check if user is in learning mode
    elif session.learning_mode and session.current_flashcard:
        logger.info(f"Routing to answer handler for user {user_id}")
        await process_answer(update, context)
        return

    # Use chatbot for normal conversation
    logger.info(f"Routing to chatbot handler for user {user_id}")
    await process_chatbot_conversation(update, context)


async def process_chatbot_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Process user message through the conversational chatbot."""
    user_id = update.effective_user.id
    user_text = update.message.text.strip()
    session = session_manager.get_session(user_id)

    # Send typing action
    await update.message.chat.send_action(action="typing")

    try:
        # Get or create user-specific chatbot
        try:
            chatbot_tutor = get_user_chatbot(user_id)
        except ValueError as e:
            # User has no API key configured
            await update.message.reply_text(
                "❌ **API Key Required**\n\n"
                "You need to configure your OpenAI API key to use the chatbot.\n\n"
                "**To set up your API key:**\n"
                "1. Get your API key from https://platform.openai.com/api-keys\n"
                "2. Use: `/configure openai_api_key sk-your-key-here`\n\n"
                "Type `/start` for more detailed setup instructions."
            )
            return

        # Get conversation history from session
        conversation_history = session.get_conversation_history()

        # Process message through chatbot
        result = chatbot_tutor.chat(user_text, conversation_history, user_id)

        if result.get("success"):
            response = result.get("response", "I'm not sure how to respond to that.")
            updated_messages = result.get("messages", [])

            # Update conversation history in session
            # Only store the new messages (excluding system message)
            if updated_messages:
                # Filter out system messages and store only human/AI messages
                for msg in updated_messages:
                    if not isinstance(msg, SystemMessage):
                        session.add_message_to_history(msg)

            # Send response
            if response:
                # Try markdown first, fallback to plain text
                try:
                    await update.message.reply_text(response, parse_mode="Markdown")
                except Exception:
                    # Fallback to plain text
                    await update.message.reply_text(response)
            else:
                await update.message.reply_text(
                    "I processed your message but don't have a response ready."
                )

        else:
            error_msg = result.get("error", "Unknown error occurred")
            logger.error(f"Chatbot error for user {user_id}: {error_msg}")
            await update.message.reply_text(
                "❌ I encountered an error processing your message. Please try again."
            )

    except Exception as e:
        logger.error(f"Error in chatbot conversation for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Sorry, I encountered an error. Please try again."
        )


# Additional helper functions for chatbot-specific features


async def handle_chatbot_feedback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, feedback: str
) -> None:
    """Handle user feedback about chatbot responses or generated content."""
    user_text = f"User feedback: {feedback}. Please adjust accordingly."

    # Process feedback through chatbot
    result = chatbot_tutor.chat(user_text)

    if result.get("success"):
        response = result.get("response", "Thank you for the feedback!")
        await safe_send_markdown(update, response)
    else:
        await update.message.reply_text(
            "Thank you for the feedback. I'll try to improve."
        )


def get_chatbot_conversation_context(user_id: int) -> dict:
    """Get conversation context for a user (placeholder for future context management)."""
    # This could be extended to maintain longer conversation histories,
    # user preferences, learning progress, etc.
    session = session_manager.get_session(user_id)
    return {
        "learning_mode": session.learning_mode,
        "editing_mode": session.editing_mode,
        "regenerating_mode": session.regenerating_mode,
        "user_settings": config_manager.get_all_settings(user_id),
    }


def clear_chatbot_conversation(user_id: int):
    """Clear conversation history for a user."""
    session = session_manager.get_session(user_id)
    session.clear_conversation_history()
    logger.info(f"Cleared chatbot conversation history for user {user_id}")
