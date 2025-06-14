"""Learning mode handlers for flashcard practice."""

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from app.flashcards import flashcard_service, TwoSidedCard, FillInTheBlank
from app.my_telegram.session import session_manager, config_manager
from app.common.telegram_utils import safe_send_markdown

logger = logging.getLogger(__name__)


async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start the flashcard learning mode.

    Loads flashcards from the database and initializes a learning session
    for the user. Supports multiple flashcard types including two-sided cards,
    fill-in-the-blank, and multiple choice questions.

    Args:
        update: Telegram update object containing the message
        context: Telegram context object
    """
    user_id = update.effective_user.id

    # Send typing action while loading flashcards
    await update.message.chat.send_action(action="typing")

    try:
        # Get user's cards per session setting
        cards_per_session = config_manager.get_setting(user_id, "cards_per_session") or 20
        
        # Get flashcards for learning session
        flashcards = flashcard_service.get_learning_session_flashcards(user_id=user_id, limit=cards_per_session)

        if not flashcards:
            await update.message.reply_text(
                "❌ No flashcards found in the database!\n\n"
                "Please add some flashcards first or contact the administrator."
            )
            return

        # Start learning session
        session = session_manager.start_learning_session(user_id, flashcards)

        response = (
            f"🎓 *Learning Mode Started!*\n\n"
            f"📚 Loaded {len(flashcards)} flashcards from database\n"
            f"I'll ask you flashcard questions. Answer them and I'll check your responses.\n"
            f"Type /finish to exit learning mode.\n\n"
            f"Let's begin!"
        )

        await safe_send_markdown(update, response)

        # Ask the first question
        await ask_next_question(update, context)

    except Exception as e:
        logger.error(f"Error loading flashcards: {e}")
        await update.message.reply_text(
            "❌ Error loading flashcards from database.\n"
            "Please try again later or contact the administrator."
        )


async def finish_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exit the flashcard learning mode."""
    try:
        user_id = update.effective_user.id
        session = session_manager.get_session(user_id)

        if session.learning_mode:
            score = session.score
            total = session.total_questions

            # Clear session
            session_manager.clear_session(user_id)

            accuracy_text = (
                f"🎯 Accuracy: {(score/total*100):.1f}%"
                if total > 0
                else "No questions answered."
            )

            response = (
                f"🎓 *Learning Session Finished!*\n\n"
                f"📊 Final Score: {score}/{total}\n"
                f"{accuracy_text}\n\n"
                f"Back to normal mode. Send me a Russian word to analyze!"
            )

            await safe_send_markdown(update, response)
        else:
            await update.message.reply_text(
                "You're not in learning mode. Use /learn to start!"
            )

    except Exception as e:
        logger.error(f"Error in finish command: {e}")
        await update.message.reply_text(
            "❌ Error finishing learning session. Please try again."
        )


async def ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the next flashcard question."""
    try:
        user_id = update.effective_user.id
        session = session_manager.get_session(user_id)

        if not session.learning_mode:
            return

        if session.flashcards:
            # Get next flashcard
            flashcard = session.flashcards.pop(0)
            session.current_flashcard = flashcard

            # Format question for display
            question_text, keyboard = flashcard_service.format_question_for_bot(
                flashcard
            )

            # Send question with safe markdown
            await safe_send_markdown(update, question_text, keyboard)
        else:
            # No more questions - end the session
            score = session.score
            total = session.total_questions

            # Clear session to exit learning mode
            session_manager.clear_session(user_id)

            accuracy_text = (
                f"🎯 Accuracy: {(score/total*100):.1f}%" if total > 0 else ""
            )

            response = (
                f"🎉 *All questions completed!*\n\n"
                f"📊 Final Score: {score}/{total}\n"
                f"{accuracy_text}\n\n"
                f"Back to normal mode. Send me a Russian word to analyze or type /learn to start another session!"
            )

            await safe_send_markdown(update, response)

    except Exception as e:
        logger.error(f"Error asking next question: {e}")
        await update.message.reply_text(
            "❌ Error loading next question. Please try /learn again."
        )


async def ask_next_question_after_callback(
    query, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Ask the next flashcard question after a callback query."""
    try:
        user_id = query.from_user.id
        session = session_manager.get_session(user_id)

        if not session.learning_mode:
            return

        if session.flashcards:
            # Get next flashcard
            flashcard = session.flashcards.pop(0)
            session.current_flashcard = flashcard

            # Format question for display
            question_text, keyboard = flashcard_service.format_question_for_bot(
                flashcard
            )

            # Send question with safe markdown
            try:
                await query.message.reply_text(
                    question_text, parse_mode="Markdown", reply_markup=keyboard
                )
            except Exception as markdown_error:
                logger.warning(
                    f"Markdown parsing failed for callback question: {markdown_error}"
                )
                await query.message.reply_text(question_text, reply_markup=keyboard)
        else:
            # No more questions - end the session
            score = session.score
            total = session.total_questions

            # Clear session to exit learning mode
            session_manager.clear_session(user_id)

            accuracy_text = (
                f"🎯 Accuracy: {(score/total*100):.1f}%" if total > 0 else ""
            )

            response = (
                f"🎉 *All questions completed!*\n\n"
                f"📊 Final Score: {score}/{total}\n"
                f"{accuracy_text}\n\n"
                f"Back to normal mode. Send me a Russian word to analyze or type /learn to start another session!"
            )

            await safe_send_markdown(query.message, response)

    except Exception as e:
        logger.error(f"Error asking next question after callback: {e}")
        await query.message.reply_text(
            "❌ Error loading next question. Please try /learn again."
        )


async def process_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the user's answer to a flashcard question."""
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)

    if not session.learning_mode:
        return

    current_flashcard = session.current_flashcard
    if not current_flashcard:
        await update.message.reply_text("❌ No active flashcard found.")
        return

    user_answer = update.message.text.strip()

    # Update total questions count
    session.total_questions += 1

    # Check answer using the flashcard service
    is_correct, feedback = flashcard_service.check_answer(
        current_flashcard, user_answer
    )

    if is_correct:
        session.score += 1

    # Update flashcard statistics in database
    flashcard_service.update_flashcard_after_review(user_id, current_flashcard, is_correct)

    # Send feedback
    await safe_send_markdown(update, feedback)

    # Ask next question
    await ask_next_question(update, context)
