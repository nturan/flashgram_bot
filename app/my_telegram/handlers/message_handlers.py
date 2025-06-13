"""Message handlers for routing user input."""

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.my_telegram.session import session_manager
from app.flashcards.models import WordType
from app.flashcards import flashcard_service

logger = logging.getLogger(__name__)


def map_grammar_to_word_type(grammar_data: dict) -> WordType:
    """Map grammar analysis data to WordType enum."""
    # Determine word type from grammar analysis
    if "gender" in grammar_data and "animacy" in grammar_data:
        return WordType.NOUN
    elif "masculine" in grammar_data and "feminine" in grammar_data:
        return WordType.ADJECTIVE
    elif "aspect" in grammar_data and "past_masculine" in grammar_data:
        return WordType.VERB
    elif "pronoun_type" in grammar_data and "declension_pattern" in grammar_data:
        return WordType.PRONOUN
    else:
        return WordType.UNKNOWN


def get_word_type_display_name(word_type: WordType) -> str:
    """Get human-readable display name for word type."""
    return word_type.value


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route messages to the chatbot system."""
    # Always route to chatbot system
    from .chatbot_handlers import handle_chatbot_message

    await handle_chatbot_message(update, context)


async def process_regeneration_hint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Process user hint for sentence regeneration."""
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    if not session.regenerating_mode:
        return

    flashcard_id = session.regenerating_flashcard_id
    if not flashcard_id:
        await update.message.reply_text("❌ Error: No flashcard being regenerated.")
        return

    hint = update.message.text.strip()

    # Import here to avoid circular imports
    from app.my_telegram.bot import regenerate_flashcard_sentence

    # Generate new sentence with hint
    await regenerate_flashcard_sentence(update, flashcard_id, hint)


async def process_flashcard_edit(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Process JSON edit input from user."""
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    if not session.editing_mode:
        return

    flashcard_id = session.editing_flashcard_id
    if not flashcard_id:
        await update.message.reply_text("❌ Error: No flashcard being edited.")
        return

    user_input = update.message.text.strip()

    # Log the input for debugging
    logger.info(f"Received flashcard edit input: {repr(user_input[:100])}...")

    # Validate input is not empty
    if not user_input:
        await update.message.reply_text(
            "❌ Error: Please provide JSON data to update the flashcard."
        )
        return

    # Check if user might have sent regular text instead of JSON
    if not (user_input.startswith("{") and user_input.endswith("}")):
        await update.message.reply_text(
            "❌ *Invalid Format*\n\n"
            "Please send the flashcard data as JSON (starting with { and ending with }).\n\n"
            "*Example:*\n"
            "```json\n{\n"
            '  "front": "Your question",\n'
            '  "back": "Your answer",\n'
            '  "title": "Your title"\n'
            "}```\n\n"
            "Use the ✏️ Edit button again to see the current JSON format.",
            parse_mode="Markdown",
        )
        return

    try:
        # Parse JSON input
        updated_data = json.loads(user_input)

        # Validate that we got a dictionary
        if not isinstance(updated_data, dict):
            await update.message.reply_text(
                "❌ Error: JSON must be an object (dictionary), not a list or primitive value."
            )
            return

        # Import here to avoid circular imports
        from app.flashcards import (
            flashcard_service,
            TwoSidedCard,
            FillInTheBlank,
            MultipleChoice,
        )

        # Get the current flashcard to determine type and validate accordingly
        current_flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
        if not current_flashcard:
            await update.message.reply_text("❌ Error: Flashcard not found.")
            return

        # Basic validation based on current flashcard type
        if isinstance(current_flashcard, TwoSidedCard):
            if not updated_data.get("front") or not updated_data.get("back"):
                await update.message.reply_text(
                    "❌ Error: Two-sided cards need 'front' and 'back' fields."
                )
                return
        elif isinstance(current_flashcard, FillInTheBlank):
            if not updated_data.get("text_with_blanks") or not updated_data.get(
                "answers"
            ):
                await update.message.reply_text(
                    "❌ Error: Fill-in-blank cards need 'text_with_blanks' and 'answers' fields."
                )
                return
        elif isinstance(current_flashcard, MultipleChoice):
            if (
                not updated_data.get("question")
                or not updated_data.get("options")
                or not updated_data.get("correct_indices")
            ):
                await update.message.reply_text(
                    "❌ Error: Multiple choice cards need 'question', 'options', and 'correct_indices' fields."
                )
                return

        # Update the flashcard in database
        success = flashcard_service.db.update_flashcard(flashcard_id, updated_data)

        if success:
            # Clear editing mode FIRST
            session.clear_editing_state()
            logger.info(
                f"Cleared editing state for user {user_id}. Current state: editing_mode={session.editing_mode}, learning_mode={session.learning_mode}"
            )

            response = (
                "✅ *Flashcard Updated Successfully!*\n\n"
                "Your changes have been saved to the database."
            )

            await safe_send_markdown(update, response)

            # If in learning mode, continue with the updated flashcard
            if session.learning_mode:
                # Get the updated flashcard
                updated_flashcard = flashcard_service.db.get_flashcard_by_id(
                    flashcard_id
                )
                if (
                    updated_flashcard
                    and session.current_flashcard
                    and str(session.current_flashcard.id) == flashcard_id
                ):
                    session.current_flashcard = updated_flashcard

                    # Double-check that editing mode is cleared before showing question
                    logger.info(
                        f"Before showing updated question - editing_mode={session.editing_mode}, learning_mode={session.learning_mode}"
                    )

                    # Show the updated question
                    question_text, keyboard = flashcard_service.format_question_for_bot(
                        updated_flashcard
                    )

                    response = f"📝 *Updated Question:*\n\n{question_text}"
                    await safe_send_markdown(update, response, keyboard)
        else:
            await update.message.reply_text(
                "❌ Failed to update flashcard. Please try again."
            )

    except json.JSONDecodeError as e:
        # Create a helpful error message with examples
        error_msg = f"❌ *Invalid JSON Format*\n\n"
        error_msg += f"Error: {str(e)}\n\n"
        error_msg += f"*Common JSON issues:*\n"
        error_msg += f"• Make sure to use double quotes \" not single quotes '\n"
        error_msg += f"• Don't forget commas between fields\n"
        error_msg += f"• Wrap the entire object in curly braces {{ }}\n\n"
        error_msg += f"*Example format:*\n"
        error_msg += f"```json\n{{\n"
        error_msg += f'  "front": "What is hello in Russian?",\n'
        error_msg += f'  "back": "Привет",\n'
        error_msg += f'  "title": "Hello greeting"\n'
        error_msg += f"}}```\n\n"
        error_msg += f"Please fix the JSON and try again."

        try:
            await update.message.reply_text(error_msg, parse_mode="Markdown")
        except Exception:
            # Fallback to plain text if markdown fails
            plain_msg = (
                error_msg.replace("*", "")
                .replace("`", "")
                .replace("```json", "")
                .replace("```", "")
            )
            await update.message.reply_text(plain_msg)
    except Exception as e:
        logger.error(f"Error processing flashcard edit: {e}")
        await update.message.reply_text(
            "❌ Error updating flashcard. Please try again."
        )
