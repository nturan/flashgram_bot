"""Message handlers for routing user input."""

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.my_telegram.session import session_manager
from app.my_telegram.session.config_manager import config_manager
from app.my_graph.language_tutor import RussianTutor
from app.common.text_processing import extract_russian_words
from app.common.telegram_utils import safe_send_markdown
from .learning_handlers import process_answer
from app.flashcards.models import WordType
from app.flashcards import flashcard_service
from app.config import settings
from pydantic import SecretStr

logger = logging.getLogger(__name__)

# This will be initialized in the main bot setup
russian_tutor: RussianTutor = None


def set_russian_tutor(tutor: RussianTutor):
    """Set the Russian tutor instance for message processing."""
    global russian_tutor
    russian_tutor = tutor


def reinit_tutor_with_model(model: str):
    """Reinitialize the global tutor with a new model."""
    global russian_tutor
    logger.info(f"Reinitializing RussianTutor with model: {model}")
    russian_tutor = RussianTutor(
        api_key=SecretStr(settings.openai_api_key),
        model=model
    )


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


async def check_and_process_word(word: str) -> tuple[bool, dict]:
    """
    Check if word is already processed and return result.
    Returns (was_processed, result_info)
    """
    try:
        # First, analyze the word to get its dictionary form and type
        result = russian_tutor.invoke(word, generate_flashcards=False)  # Don't generate flashcards yet
        
        if "final_answer" not in result or not result["final_answer"]:
            return False, {"error": "No analysis result"}
        
        try:
            grammar_data = json.loads(result["final_answer"])
            dictionary_form = grammar_data.get("dictionary_form", word)
            word_type = map_grammar_to_word_type(grammar_data)
            
            # Check if this word+type combination is already processed
            if flashcard_service.db.is_word_processed(dictionary_form, word_type):
                # Get the cached word info
                processed_word = flashcard_service.db.get_processed_word(dictionary_form, word_type)
                return True, {
                    "word": word,
                    "dictionary_form": dictionary_form,
                    "type": get_word_type_display_name(word_type),
                    "flashcards": processed_word.flashcards_generated if processed_word else 0,
                    "processed_date": processed_word.processed_date if processed_word else None,
                    "cached": True
                }
            
            # Word not processed yet, return analysis data for processing
            return False, {
                "word": word,
                "dictionary_form": dictionary_form,
                "word_type": word_type,
                "grammar_data": grammar_data,
                "analysis_result": result
            }
            
        except json.JSONDecodeError:
            return False, {"error": "JSON decode error"}
            
    except Exception as e:
        logger.error(f"Error checking word '{word}': {e}")
        return False, {"error": str(e)}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route messages between learning mode, editing mode, and normal grammar analysis."""
    user_id = update.effective_user.id
    
    # Check if user has chatbot mode enabled
    use_chatbot = config_manager.get_setting(user_id, "use_chatbot")
    
    if use_chatbot:
        # Route to chatbot system
        from .chatbot_handlers import handle_chatbot_message
        await handle_chatbot_message(update, context)
    else:
        # Use original system
        session = session_manager.get_session(user_id)
        
        # Debug logging to track session state
        logger.info(f"Message routing for user {user_id}: regenerating={session.regenerating_mode}, editing={session.editing_mode}, learning={session.learning_mode}, has_flashcard={session.current_flashcard is not None}")
        
        # Check if user is in regeneration mode
        if session.regenerating_mode:
            logger.info(f"Routing to regeneration handler for user {user_id}")
            await process_regeneration_hint(update, context)
        # Check if user is in editing mode
        elif session.editing_mode:
            logger.info(f"Routing to editing handler for user {user_id}")
            await process_flashcard_edit(update, context)
        # Check if user is in learning mode
        elif session.learning_mode and session.current_flashcard:
            logger.info(f"Routing to answer handler for user {user_id}")
            await process_answer(update, context)
        else:
            logger.info(f"Routing to Russian text handler for user {user_id}")
            await process_russian_text(update, context)


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
    
    # Import here to avoid circular imports
    from app.my_telegram.bot import regenerate_flashcard_sentence
    
    # Generate new sentence with hint
    await regenerate_flashcard_sentence(update, flashcard_id, hint)


async def process_flashcard_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        await update.message.reply_text("❌ Error: Please provide JSON data to update the flashcard.")
        return
    
    # Check if user might have sent regular text instead of JSON
    if not (user_input.startswith('{') and user_input.endswith('}')):
        await update.message.reply_text(
            "❌ *Invalid Format*\n\n"
            "Please send the flashcard data as JSON (starting with { and ending with }).\n\n"
            "*Example:*\n"
            "```json\n{\n"
            "  \"front\": \"Your question\",\n"
            "  \"back\": \"Your answer\",\n"
            "  \"title\": \"Your title\"\n"
            "}```\n\n"
            "Use the ✏️ Edit button again to see the current JSON format.",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Parse JSON input
        updated_data = json.loads(user_input)
        
        # Validate that we got a dictionary
        if not isinstance(updated_data, dict):
            await update.message.reply_text("❌ Error: JSON must be an object (dictionary), not a list or primitive value.")
            return
        
        # Import here to avoid circular imports
        from app.flashcards import flashcard_service, TwoSidedCard, FillInTheBlank, MultipleChoice
        
        # Get the current flashcard to determine type and validate accordingly
        current_flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
        if not current_flashcard:
            await update.message.reply_text("❌ Error: Flashcard not found.")
            return
        
        # Basic validation based on current flashcard type
        if isinstance(current_flashcard, TwoSidedCard):
            if not updated_data.get('front') or not updated_data.get('back'):
                await update.message.reply_text("❌ Error: Two-sided cards need 'front' and 'back' fields.")
                return
        elif isinstance(current_flashcard, FillInTheBlank):
            if not updated_data.get('text_with_blanks') or not updated_data.get('answers'):
                await update.message.reply_text("❌ Error: Fill-in-blank cards need 'text_with_blanks' and 'answers' fields.")
                return
        elif isinstance(current_flashcard, MultipleChoice):
            if not updated_data.get('question') or not updated_data.get('options') or not updated_data.get('correct_indices'):
                await update.message.reply_text("❌ Error: Multiple choice cards need 'question', 'options', and 'correct_indices' fields.")
                return
        
        # Update the flashcard in database
        success = flashcard_service.db.update_flashcard(flashcard_id, updated_data)
        
        if success:
            # Clear editing mode FIRST
            session.clear_editing_state()
            logger.info(f"Cleared editing state for user {user_id}. Current state: editing_mode={session.editing_mode}, learning_mode={session.learning_mode}")
            
            response = (
                "✅ *Flashcard Updated Successfully!*\n\n"
                "Your changes have been saved to the database."
            )
            
            await safe_send_markdown(update, response)
            
            # If in learning mode, continue with the updated flashcard
            if session.learning_mode:
                # Get the updated flashcard
                updated_flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
                if updated_flashcard and session.current_flashcard and str(session.current_flashcard.id) == flashcard_id:
                    session.current_flashcard = updated_flashcard
                    
                    # Double-check that editing mode is cleared before showing question
                    logger.info(f"Before showing updated question - editing_mode={session.editing_mode}, learning_mode={session.learning_mode}")
                    
                    # Show the updated question
                    question_text, keyboard = flashcard_service.format_question_for_bot(updated_flashcard)
                    
                    response = f"📝 *Updated Question:*\n\n{question_text}"
                    await safe_send_markdown(update, response, keyboard)
        else:
            await update.message.reply_text("❌ Failed to update flashcard. Please try again.")
            
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
        error_msg += f"  \"front\": \"What is hello in Russian?\",\n"
        error_msg += f"  \"back\": \"Привет\",\n"
        error_msg += f"  \"title\": \"Hello greeting\"\n"
        error_msg += f"}}```\n\n"
        error_msg += f"Please fix the JSON and try again."
        
        try:
            await update.message.reply_text(error_msg, parse_mode='Markdown')
        except Exception:
            # Fallback to plain text if markdown fails
            plain_msg = error_msg.replace('*', '').replace('`', '').replace('```json', '').replace('```', '')
            await update.message.reply_text(plain_msg)
    except Exception as e:
        logger.error(f"Error processing flashcard edit: {e}")
        await update.message.reply_text("❌ Error updating flashcard. Please try again.")


async def process_russian_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process Russian text (words or sentences) and generate flashcards automatically."""
    if not russian_tutor:
        await update.message.reply_text("❌ Russian tutor not initialized. Please contact administrator.")
        return
    
    user_text = update.message.text.strip()
    
    # Send typing action
    await update.message.chat.send_action(action="typing")
    
    try:
        # Extract Russian words from the text
        words = extract_russian_words(user_text)
        
        if not words:
            await update.message.reply_text(
                "I couldn't find any Russian words to analyze. Please send Russian text (words or sentences)."
            )
            return
        
        # Send initial processing message
        word_count = len(words)
        word_plural = "words" if word_count != 1 else "word"
        unique_words = list(set(words))  # Remove duplicates for more accurate count
        unique_count = len(unique_words)
        
        if unique_count != word_count:
            processing_text = f"🔄 Processing {unique_count} unique {word_plural} from your text..."
        else:
            processing_text = f"🔄 Processing {word_count} {word_plural}..."
        
        # Send the initial message and keep reference to edit it later
        processing_message = await update.message.reply_text(processing_text)
        
        # Track results for each word
        successful_words = []
        cached_words = []
        failed_words = []
        total_flashcards = 0
        
        # Process each unique word
        for i, word in enumerate(unique_words, 1):
            try:
                # Check if word is already processed
                was_processed, word_info = await check_and_process_word(word)
                
                if "error" in word_info:
                    failed_words.append(word)
                    continue
                
                if was_processed:
                    # Word was already processed, use cached data
                    cached_words.append(word_info)
                    total_flashcards += word_info["flashcards"]
                    logger.info(f"Using cached data for word '{word}' -> '{word_info['dictionary_form']}'")
                else:
                    # Word not processed yet, generate flashcards
                    try:
                        # Generate flashcards using the pre-analyzed data
                        result = russian_tutor.invoke(word, generate_flashcards=True)
                        
                        if "final_answer" in result and result["final_answer"]:
                            flashcard_count = result.get("flashcards_generated", 0)
                            
                            # Add to processed words cache
                            flashcard_service.db.add_processed_word(
                                word_info["dictionary_form"],
                                word_info["word_type"],
                                flashcard_count,
                                word_info["grammar_data"]
                            )
                            
                            successful_words.append({
                                "word": word,
                                "type": get_word_type_display_name(word_info["word_type"]),
                                "dictionary_form": word_info["dictionary_form"],
                                "flashcards": flashcard_count
                            })
                            total_flashcards += flashcard_count
                            
                        else:
                            failed_words.append(word)
                    
                    except Exception as e:
                        logger.error(f"Error generating flashcards for word '{word}': {e}")
                        failed_words.append(word)
                        
            except Exception as e:
                logger.error(f"Error processing word '{word}': {e}")
                failed_words.append(word)
            
            # Update progress for large texts (every 5 words or if it's the last word)
            if unique_count > 10 and (i % 5 == 0 or i == unique_count):
                try:
                    progress_text = f"🔄 Processing {word_plural}... ({i}/{unique_count})"
                    await processing_message.edit_text(progress_text)
                except Exception:
                    # Don't break processing if we can't edit the message
                    pass
        
        # Build summary response
        if successful_words or cached_words or failed_words:
            response = "📚 *Text Analysis Complete!*\n\n"
            
            if successful_words:
                word_plural = "words" if len(successful_words) != 1 else "word"
                response += f"✅ *Newly processed {len(successful_words)} {word_plural}:*\n"
                for word_info in successful_words:
                    response += f"• {word_info['dictionary_form']} ({word_info['type']}) - {word_info['flashcards']} flashcards\n"
                response += "\n"
            
            if cached_words:
                word_plural = "words" if len(cached_words) != 1 else "word"
                response += f"💾 *Already processed {len(cached_words)} {word_plural} (using cache):*\n"
                for word_info in cached_words:
                    response += f"• {word_info['dictionary_form']} ({word_info['type']}) - {word_info['flashcards']} flashcards\n"
                response += "\n"
            
            if failed_words:
                word_plural = "words" if len(failed_words) != 1 else "word"
                response += f"⚠️ *Skipped {len(failed_words)} {word_plural}:*\n"
                response += f"• {', '.join(failed_words)}\n"
                response += f"*(Unsupported word types or analysis errors)*\n\n"
            
            # Show totals
            total_processed = len(successful_words) + len(cached_words)
            if total_processed > 0:
                response += f"🎯 *Total flashcards available:* {total_flashcards}\n"
                response += f"📖 *Words in dictionary:* {total_processed}\n"
                response += f"💡 Use /learn to practice with your flashcards!"
            
            # Edit the processing message with final results
            try:
                await processing_message.edit_text(response, parse_mode='Markdown')
            except Exception as edit_error:
                logger.warning(f"Failed to edit processing message: {edit_error}")
                # Fallback: send as new message
                await safe_send_markdown(update, response)
                
        else:
            # Edit processing message to show error
            error_text = "❌ I couldn't analyze any words from your text. Please try again with clear Russian words."
            try:
                await processing_message.edit_text(error_text)
            except Exception:
                await update.message.reply_text(error_text)
    
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        error_text = "❌ Sorry, I encountered an error processing your text. Please try again."
        
        # Try to edit the processing message if it exists, otherwise send new message
        try:
            if 'processing_message' in locals():
                await processing_message.edit_text(error_text)
            else:
                await update.message.reply_text(error_text)
        except Exception:
            await update.message.reply_text(error_text)