from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.my_graph.language_tutor import RussianTutor
from app.my_telegram.handlers import (
    start, help_command, dashboard_command, dbstatus_command, dictionary_command,
    learn_command, finish_command, handle_message
)
from app.my_telegram.handlers.message_handlers import set_russian_tutor

# Legacy callback handlers using new session manager
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.flashcards import flashcard_service, TwoSidedCard, FillInTheBlank, MultipleChoice
from app.my_telegram.session import session_manager

logger = logging.getLogger(__name__)

# Session management now handled by session_manager

# Command handlers moved to app.my_telegram.handlers.command_handlers

# Learning handlers moved to app.my_telegram.handlers.learning_handlers

# finish_command moved to app.my_telegram.handlers.command_handlers

# dashboard_command moved to app.my_telegram.handlers.command_handlers

# dbstatus_command moved to app.my_telegram.handlers.command_handlers

# extract_russian_words moved to app.utils.common

# build_grammar_response moved to app.utils.formatters

# ask_next_question moved to app.my_telegram.handlers.learning_handlers

# process_answer moved to app.my_telegram.handlers.learning_handlers

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboard buttons."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    
    try:
        # Parse callback data
        callback_data = query.data
        
        if callback_data.startswith("mc_"):
            # Multiple choice answer
            parts = callback_data.split("_")
            if len(parts) >= 3:
                flashcard_id = parts[1]
                selected_option = int(parts[2])
                
                # Get user session using session manager
                user_id = query.from_user.id
                session = session_manager.get_session(user_id)
                
                if session.learning_mode and session.current_flashcard:
                    current_flashcard = session.current_flashcard
                    
                    # Verify this is the correct flashcard
                    if str(current_flashcard.id) == flashcard_id:
                        # Check the answer
                        from app.flashcards.models import MultipleChoice
                        if isinstance(current_flashcard, MultipleChoice):
                            is_correct = selected_option in current_flashcard.correct_indices
                            
                            # Update session
                            session.total_questions += 1
                            if is_correct:
                                session.score += 1
                            
                            # Update flashcard in database
                            flashcard_service.update_flashcard_after_review(current_flashcard, is_correct)
                            
                            # Create feedback message
                            selected_letter = chr(65 + selected_option)
                            selected_text = current_flashcard.options[selected_option]
                            
                            if is_correct:
                                feedback = f"✅ Correct! You selected {selected_letter}. {selected_text}"
                            else:
                                correct_indices = current_flashcard.correct_indices
                                correct_letters = [chr(65 + i) for i in correct_indices]
                                correct_texts = [current_flashcard.options[i] for i in correct_indices]
                                feedback = f"❌ Incorrect. You selected {selected_letter}. {selected_text}\n"
                                feedback += f"Correct answer: {', '.join(correct_letters)}. {', '.join(correct_texts)}"
                            
                            # Edit the message to show the result
                            await query.edit_message_text(
                                text=f"{query.message.text}\n\n{feedback}",
                                parse_mode='Markdown'
                            )
                            
                            # Ask next question after a short delay
                            import asyncio
                            await asyncio.sleep(1.5)
                            await ask_next_question_after_callback(query, context)
                            
                        else:
                            await query.edit_message_text(
                                text="❌ Error: This is not a multiple choice question."
                            )
                    else:
                        await query.edit_message_text(
                            text="❌ Error: Question has changed. Please start a new learning session."
                        )
                else:
                    await query.edit_message_text(
                        text="❌ Error: No active learning session found."
                    )
            else:
                await query.edit_message_text(
                    text="❌ Error: Invalid callback data."
                )
        elif callback_data.startswith("edit_"):
            # Edit flashcard
            flashcard_id = callback_data.split("_", 1)[1]
            await handle_edit_flashcard(query, context, flashcard_id)
        
        elif callback_data.startswith("delete_"):
            # Delete flashcard
            flashcard_id = callback_data.split("_", 1)[1]
            await handle_delete_flashcard(query, context, flashcard_id)
        
        elif callback_data.startswith("answer_"):
            # Show answer for non-multiple choice cards
            flashcard_id = callback_data.split("_", 1)[1]
            await handle_show_answer(query, context, flashcard_id)
        
        elif callback_data.startswith("confirm_delete_"):
            # Confirm deletion
            flashcard_id = callback_data.split("_", 2)[2]
            await handle_confirm_delete(query, context, flashcard_id)
        
        elif callback_data.startswith("cancel_delete_"):
            # Cancel deletion
            flashcard_id = callback_data.split("_", 2)[2]
            await handle_cancel_delete(query, context, flashcard_id)
        
        elif callback_data.startswith("cancel_edit_"):
            # Cancel editing
            flashcard_id = callback_data.split("_", 2)[2]
            await handle_cancel_edit(query, context, flashcard_id)
        
        elif callback_data.startswith("regen_sentence_"):
            # Regenerate sentence with LLM
            flashcard_id = callback_data.split("_", 2)[2]
            await handle_regenerate_sentence(query, context, flashcard_id)
        
        elif callback_data.startswith("regen_no_hint_"):
            # Regenerate sentence without hint
            flashcard_id = callback_data.split("_", 3)[3]
            await regenerate_flashcard_sentence(query, flashcard_id, None)
        
        else:
            await query.edit_message_text(
                text="❌ Error: Unknown callback type."
            )
            
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        await query.edit_message_text(
            text="❌ Error processing your answer. Please try again."
        )

async def ask_next_question_after_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            question_text, keyboard = flashcard_service.format_question_for_bot(flashcard)
            
            # Try to send with markdown, fallback to plain text if it fails
            try:
                await query.message.reply_text(
                    question_text,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            except Exception as markdown_error:
                logger.warning(f"Markdown parsing failed for callback question: {markdown_error}. Sending as plain text.")
                await query.message.reply_text(
                    question_text,
                    reply_markup=keyboard
                )
        else:
            # No more questions - end the session
            score = session.score
            total = session.total_questions
            
            # Clear session to exit learning mode
            session_manager.clear_session(user_id)
            
            await query.message.reply_text(
                f"🎉 *All questions completed!*\n\n"
                f"📊 Final Score: {score}/{total}\n"
                f"🎯 Accuracy: {(score/total*100):.1f}%\n\n" if total > 0 else ""
                f"Back to normal mode. Send me a Russian word to analyze or type /learn to start another session!",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error asking next question after callback: {e}")
        await query.message.reply_text("❌ Error loading next question. Please try /learn again.")

async def handle_edit_flashcard(query, context: ContextTypes.DEFAULT_TYPE, flashcard_id: str) -> None:
    """Handle flashcard editing with JSON input."""
    try:
        # Get the flashcard from database
        flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
        
        if not flashcard:
            await query.edit_message_text("❌ Flashcard not found.")
            return
        
        # Set user in editing mode using session manager
        user_id = query.from_user.id
        session_manager.start_editing_session(user_id, flashcard_id)
        
        # Extract only the essential editable fields based on card type
        edit_data = {}
        
        if isinstance(flashcard, TwoSidedCard):
            edit_data = {
                "front": flashcard.front,
                "back": flashcard.back,
                "title": flashcard.title
            }
        elif isinstance(flashcard, FillInTheBlank):
            edit_data = {
                "text_with_blanks": flashcard.text_with_blanks,
                "answers": flashcard.answers,
                "title": flashcard.title
            }
        elif isinstance(flashcard, MultipleChoice):
            edit_data = {
                "question": flashcard.question,
                "options": flashcard.options,
                "correct_indices": flashcard.correct_indices,
                "title": flashcard.title
            }
        
        # Format JSON nicely
        import json
        json_text = json.dumps(edit_data, indent=2, ensure_ascii=False)
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        buttons = []
        
        # Add regenerate sentence option for fill-in-blank cards
        if isinstance(flashcard, FillInTheBlank):
            buttons.append([InlineKeyboardButton("🔄 Regenerate Sentence", callback_data=f"regen_sentence_{flashcard_id}")])
        
        buttons.append([InlineKeyboardButton("❌ Cancel Edit", callback_data=f"cancel_edit_{flashcard_id}")])
        keyboard = InlineKeyboardMarkup(buttons)
        
        await query.edit_message_text(
            f"✏️ *Edit Flashcard*\n\n"
            f"📋 Please copy the JSON below, edit it, and send it back:\n\n"
            f"```json\n{json_text}\n```\n\n"
            f"💡 *Instructions:*\n"
            f"• Copy ALL the text above (including {{ and }})\n"
            f"• Edit only the values inside the quotes\n"
            f"• Keep the structure exactly the same\n"
            f"• Send the complete JSON back to me\n"
            f"• Example: Change \"old text\" to \"new text\"\n\n"
            f"⚠️ *Important:* Send only the JSON, no other text!",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error handling edit flashcard: {e}")
        await query.edit_message_text("❌ Error opening editor. Please try again.")

async def handle_delete_flashcard(query, context: ContextTypes.DEFAULT_TYPE, flashcard_id: str) -> None:
    """Handle flashcard deletion with confirmation."""
    try:
        # Get the flashcard from database
        flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
        
        if not flashcard:
            await query.edit_message_text("❌ Flashcard not found.")
            return
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        confirm_buttons = [
            [
                InlineKeyboardButton("⚠️ Yes, Delete", callback_data=f"confirm_delete_{flashcard_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_delete_{flashcard_id}")
            ]
        ]
        keyboard = InlineKeyboardMarkup(confirm_buttons)
        
        await query.edit_message_text(
            f"🗑️ *Delete Flashcard?*\n\n"
            f"📋 *Card:* {flashcard.title}\n\n"
            f"⚠️ This action cannot be undone. Are you sure?",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error handling delete flashcard: {e}")
        await query.edit_message_text("❌ Error preparing deletion. Please try again.")

async def handle_show_answer(query, context: ContextTypes.DEFAULT_TYPE, flashcard_id: str) -> None:
    """Show the answer for non-multiple choice cards."""
    try:
        # Get user session using session manager
        user_id = query.from_user.id
        session = session_manager.get_session(user_id)
        
        if session.learning_mode and session.current_flashcard:
            current_flashcard = session.current_flashcard
            
            if str(current_flashcard.id) == flashcard_id:
                # Update session stats
                session.total_questions += 1
                
                # Show the answer
                if isinstance(current_flashcard, TwoSidedCard):
                    answer_text = current_flashcard.back
                elif isinstance(current_flashcard, FillInTheBlank):
                    answer_text = ", ".join(current_flashcard.answers)
                else:
                    answer_text = "Answer not available"
                
                # Update flashcard as "seen" (neutral review)
                flashcard_service.update_flashcard_after_review(current_flashcard, True)
                
                # Use safe markdown utility to handle the entire message
                from app.common.telegram_utils import safe_send_markdown
                
                # Get the original question text without markdown formatting
                original_text = query.message.text
                # Strip any existing markdown formatting for clean display
                import re
                clean_text = re.sub(r'[*_`\[\]()]', '', original_text)
                
                response_text = (
                    f"{clean_text}\n\n"
                    f"💡 *Answer:* {answer_text}\n\n"
                    f"Moving to next question..."
                )
                
                # Create a new message instead of editing to avoid markdown conflicts
                await query.message.reply_text(
                    response_text,
                    parse_mode=None  # Use plain text to avoid any markdown issues
                )
                
                # Ask next question after delay
                import asyncio
                await asyncio.sleep(2)
                await ask_next_question_after_callback(query, context)
            else:
                await query.edit_message_text("❌ Error: Question has changed.")
        else:
            await query.edit_message_text("❌ Error: No active learning session.")
            
    except Exception as e:
        logger.error(f"Error showing answer: {e}")
        await query.edit_message_text("❌ Error showing answer. Please try again.")

async def handle_confirm_delete(query, context: ContextTypes.DEFAULT_TYPE, flashcard_id: str) -> None:
    """Confirm and execute flashcard deletion."""
    try:
        success = flashcard_service.db.delete_flashcard(flashcard_id)
        
        if success:
            await query.edit_message_text(
                "✅ *Flashcard Deleted Successfully*\n\n"
                "The flashcard has been permanently removed from your collection.",
                parse_mode='Markdown'
            )
            
            # If in learning mode, continue to next question
            user_id = query.from_user.id
            session = session_manager.get_session(user_id)
            if session.learning_mode:
                import asyncio
                await asyncio.sleep(1.5)
                await ask_next_question_after_callback(query, context)
        else:
            await query.edit_message_text("❌ Failed to delete flashcard. Please try again.")
            
    except Exception as e:
        logger.error(f"Error confirming delete: {e}")
        await query.edit_message_text("❌ Error deleting flashcard. Please try again.")

async def handle_cancel_delete(query, context: ContextTypes.DEFAULT_TYPE, flashcard_id: str) -> None:
    """Cancel flashcard deletion and return to question."""
    try:
        user_id = query.from_user.id
        session = session_manager.get_session(user_id)
        
        if session.learning_mode and session.current_flashcard:
            current_flashcard = session.current_flashcard
            
            if str(current_flashcard.id) == flashcard_id:
                # Return to the original question
                question_text, keyboard = flashcard_service.format_question_for_bot(current_flashcard)
                
                try:
                    await query.edit_message_text(
                        question_text,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
                except Exception as markdown_error:
                    logger.warning(f"Markdown parsing failed: {markdown_error}")
                    await query.edit_message_text(
                        question_text,
                        reply_markup=keyboard
                    )
            else:
                await query.edit_message_text("❌ Error: Question has changed.")
        else:
            await query.edit_message_text("❌ Error: No active learning session.")
            
    except Exception as e:
        logger.error(f"Error canceling delete: {e}")
        await query.edit_message_text("❌ Error returning to question. Please try again.")

async def handle_cancel_edit(query, context: ContextTypes.DEFAULT_TYPE, flashcard_id: str) -> None:
    """Cancel flashcard editing and return to question."""
    try:
        user_id = query.from_user.id
        session = session_manager.get_session(user_id)
        
        # Clear editing mode
        session.clear_editing_state()
        logger.info(f"CANCEL_EDIT: Cleared editing state for user {user_id}. Current state: editing_mode={session.editing_mode}, learning_mode={session.learning_mode}")
        
        # Return to the original question if in learning mode
        if session.learning_mode and session.current_flashcard:
            current_flashcard = session.current_flashcard
            
            if str(current_flashcard.id) == flashcard_id:
                question_text, keyboard = flashcard_service.format_question_for_bot(current_flashcard)
                
                try:
                    await query.edit_message_text(
                        question_text,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
                except Exception as markdown_error:
                    logger.warning(f"Markdown parsing failed: {markdown_error}")
                    await query.edit_message_text(
                        question_text,
                        reply_markup=keyboard
                    )
            else:
                await query.edit_message_text("❌ Error: Question has changed.")
        else:
            await query.edit_message_text("✅ Edit canceled. You can continue using the bot normally.")
            
    except Exception as e:
        logger.error(f"Error canceling edit: {e}")
        await query.edit_message_text("❌ Error canceling edit. Please try again.")

# REMOVED: Duplicate process_flashcard_edit function - using the one in message_handlers.py

async def handle_regenerate_sentence(query, context: ContextTypes.DEFAULT_TYPE, flashcard_id: str) -> None:
    """Handle LLM-powered sentence regeneration for fill-in-blank cards."""
    try:
        # Get the flashcard from database
        flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
        
        if not flashcard or not isinstance(flashcard, FillInTheBlank):
            await query.edit_message_text("❌ Error: Fill-in-blank flashcard not found.")
            return
        
        # Set user in regeneration mode using session manager
        user_id = query.from_user.id
        session_manager.start_regenerating_session(user_id, flashcard_id)
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Option to regenerate without hint or provide a hint
        buttons = [
            [InlineKeyboardButton("🎲 Generate New Sentence", callback_data=f"regen_no_hint_{flashcard_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_edit_{flashcard_id}")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        
        # Extract metadata for context
        metadata = flashcard.metadata or {}
        dictionary_form = metadata.get('dictionary_form', 'unknown word')
        grammatical_key = metadata.get('grammatical_key', 'grammatical form')
        
        await query.edit_message_text(
            f"🔄 *Regenerate Sentence*\n\n"
            f"📋 *Current:* {flashcard.title}\n"
            f"📝 *Word:* {dictionary_form}\n"
            f"🎯 *Form:* {grammatical_key}\n\n"
            f"Choose an option:\n"
            f"• Click 'Generate New Sentence' for a random new sentence\n"
            f"• Or type a hint/context (e.g., 'about cooking', 'at school', 'family context') and I'll create a sentence with that theme",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error handling regenerate sentence: {e}")
        await query.edit_message_text("❌ Error setting up regeneration. Please try again.")

async def process_regeneration_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    # Generate new sentence with hint
    await regenerate_flashcard_sentence(update, flashcard_id, hint)

async def regenerate_flashcard_sentence(update_or_query, flashcard_id: str, hint: str = None) -> None:
    """Regenerate the sentence for a fill-in-blank flashcard using LLM."""
    try:
        # Get the flashcard from database
        flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
        
        if not flashcard or not isinstance(flashcard, FillInTheBlank):
            message_text = "❌ Error: Fill-in-blank flashcard not found."
            if hasattr(update_or_query, 'edit_message_text'):
                await update_or_query.edit_message_text(message_text)
            else:
                await update_or_query.message.reply_text(message_text)
            return
        
        # Extract metadata
        metadata = flashcard.metadata or {}
        dictionary_form = metadata.get('dictionary_form', 'unknown')
        grammatical_key = metadata.get('grammatical_key', 'grammatical form')
        
        # Get the target form from the current sentence
        current_sentence = flashcard.text_with_blanks
        answers = flashcard.answers
        
        # Try to reconstruct the target form
        if answers and len(answers) > 0:
            # Find the stem by looking at the blank position
            blank_pos = current_sentence.find('{blank}')
            if blank_pos > 0:
                # Look backwards to find word start
                stem_start = blank_pos
                while stem_start > 0 and current_sentence[stem_start - 1].isalpha():
                    stem_start -= 1
                stem = current_sentence[stem_start:blank_pos]
                target_form = stem + answers[0]
            else:
                target_form = dictionary_form
        else:
            target_form = dictionary_form
        
        # Generate new sentence using the modular sentence generator
        from app.my_graph.sentence_generation import LLMSentenceGenerator
        from app.my_graph.utils import SuffixExtractor
        
        sentence_generator = LLMSentenceGenerator()
        suffix_extractor = SuffixExtractor()
        
        # Generate sentence with optional hint
        if hint:
            new_sentence = sentence_generator.generate_contextual_sentence(
                dictionary_form, target_form, grammatical_key, hint
            )
        else:
            new_sentence = sentence_generator.generate_example_sentence(
                dictionary_form, target_form, grammatical_key, "word"
            )
        
        # Extract stem and suffix for the new sentence
        stem, suffix = suffix_extractor.extract_suffix(dictionary_form, target_form)
        
        # Create the sentence with masked suffix using text processor
        from app.my_graph.sentence_generation import TextProcessor
        text_processor = TextProcessor()
        sentence_with_blank = text_processor.create_sentence_with_blank(new_sentence, target_form, stem)
        
        # Update the flashcard in database
        updates = {
            "text_with_blanks": sentence_with_blank,
            "answers": [suffix]
        }
        
        success = flashcard_service.db.update_flashcard(flashcard_id, updates)
        
        if success:
            # Clear regeneration mode using session manager
            if hasattr(update_or_query, 'from_user'):
                user_id = update_or_query.from_user.id
            else:
                user_id = update_or_query.message.from_user.id if update_or_query.message else None
            
            if user_id:
                session = session_manager.get_session(user_id)
                session.clear_regeneration_state()
                # Also clear editing state since regeneration was initiated from edit mode
                session.clear_editing_state()
                logger.info(f"REGENERATE: Cleared both regeneration and editing states for user {user_id}. Current state: editing_mode={session.editing_mode}, learning_mode={session.learning_mode}, regenerating_mode={session.regenerating_mode}")
            
            # Show the updated flashcard
            display_text = sentence_with_blank.replace("{blank}", "_____")
            
            # Escape markdown special characters using common utilities
            from app.common.text_processing import escape_markdown
            escaped_display = escape_markdown(display_text)
            escaped_suffix = escape_markdown(suffix)
            escaped_hint = escape_markdown(hint) if hint else ""
            
            message_text = (
                f"✅ *Sentence Regenerated!*\n\n"
                f"📝 *New Question:*\n{escaped_display}\n\n"
                f"💡 *Answer:* {escaped_suffix}\n\n"
                f"The flashcard has been updated in the database."
            )
            
            if hint:
                message_text += f"\n\n🎯 *Used hint:* {escaped_hint}"
            
            # Try markdown first, fallback to plain text
            try:
                if hasattr(update_or_query, 'edit_message_text'):
                    await update_or_query.edit_message_text(message_text, parse_mode='Markdown')
                else:
                    await update_or_query.message.reply_text(message_text, parse_mode='Markdown')
            except Exception as markdown_error:
                logger.warning(f"Markdown parsing failed in regeneration: {markdown_error}")
                # Fallback to plain text
                plain_message = (
                    f"✅ Sentence Regenerated!\n\n"
                    f"📝 New Question:\n{display_text}\n\n"
                    f"💡 Answer: {suffix}\n\n"
                    f"The flashcard has been updated in the database."
                )
                
                if hint:
                    plain_message += f"\n\n🎯 Used hint: {hint}"
                
                if hasattr(update_or_query, 'edit_message_text'):
                    await update_or_query.edit_message_text(plain_message)
                else:
                    await update_or_query.message.reply_text(plain_message)
                
            # If in learning mode, update the current flashcard and continue
            if user_id:
                session = session_manager.get_session(user_id)
                if session.learning_mode and session.current_flashcard:
                    current_fc = session.current_flashcard
                    if str(current_fc.id) == flashcard_id:
                        # Get updated flashcard and continue learning
                        updated_flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
                        if updated_flashcard:
                            session.current_flashcard = updated_flashcard
                            
                            # Show the updated question after a delay
                            import asyncio
                            await asyncio.sleep(2)
                            question_text, keyboard = flashcard_service.format_question_for_bot(updated_flashcard)
                            
                            try:
                                if hasattr(update_or_query, 'message'):
                                    await update_or_query.message.reply_text(
                                        f"📝 *Continue Learning:*\n\n{question_text}",
                                        parse_mode='Markdown',
                                        reply_markup=keyboard
                                    )
                            except Exception as markdown_error:
                                logger.warning(f"Markdown parsing failed in continue learning: {markdown_error}")
                                if hasattr(update_or_query, 'message'):
                                    await update_or_query.message.reply_text(
                                        f"📝 Continue Learning:\n\n{question_text}",
                                        reply_markup=keyboard
                                    )
        else:
            message_text = "❌ Failed to update flashcard. Please try again."
            if hasattr(update_or_query, 'edit_message_text'):
                await update_or_query.edit_message_text(message_text)
            else:
                await update_or_query.message.reply_text(message_text)
            
    except Exception as e:
        logger.error(f"Error regenerating sentence: {e}")
        message_text = "❌ Error regenerating sentence. Please try again."
        if hasattr(update_or_query, 'edit_message_text'):
            await update_or_query.edit_message_text(message_text)
        else:
            await update_or_query.message.reply_text(message_text)

# handle_message moved to app.my_telegram.handlers.message_handlers

# process_russian_text moved to app.my_telegram.handlers.text_processors

def init_application(token: str, tutor: RussianTutor) -> Application:
    """Start the bot with the Russian tutor."""
    # Set the tutor for message processing
    set_russian_tutor(tutor)

    # Create the Application
    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("finish", finish_command))
    application.add_handler(CommandHandler("dbstatus", dbstatus_command))
    application.add_handler(CommandHandler("dictionary", dictionary_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application
