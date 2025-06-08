from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import json
import logging
import re
from typing import Dict, List, Optional, Any

from pydantic import SecretStr

from app.my_graph.language_tutor import RussianTutor
from app.flashcards import flashcard_service, TwoSidedCard, FillInTheBlank, MultipleChoice

# Get module-level logger
logger = logging.getLogger(__name__)

# This will be initialized in init_application
russian_tutor: Optional[RussianTutor] = None

# User session data to track learn mode and editing
user_sessions: Dict[int, Dict[str, Any]] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm a Russian language tutor bot. Send me Russian words or sentences, and I'll automatically analyze them and create flashcards for practice!",
        reply_markup=ForceReply(selective=True)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "I can help you learn Russian grammar!\n\n"
        "Just send me Russian words or sentences and I'll:\n"
        "• Analyze each word's grammar automatically\n"
        "• Generate flashcards for practice\n"
        "• Save them for spaced repetition learning\n\n"
        "Supported word types:\n"
        "• Nouns: gender, animacy, and all case forms\n"
        "• Adjectives: all gender forms, cases, and special forms\n"
        "• Verbs: aspect, conjugation, and all tense forms\n\n"
        "Commands:\n"
        "• /dashboard - View flashcard statistics and progress\n"
        "• /learn - Start flashcard learning mode\n"
        "• /finish - Exit learning mode\n"
        "• /dbstatus - Check database connection status\n\n"
        "Examples to try:\n"
        "- 'книга' (book) or 'стол' (table) for nouns\n"
        "- 'красивый' (beautiful) or 'хороший' (good) for adjectives\n"
        "- 'читать' (to read) or 'идти' (to go) for verbs\n"
        "- 'Я читаю интересную книгу' (full sentences work too!)"
    )

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
        # Get flashcards for learning session
        flashcards = flashcard_service.get_learning_session_flashcards(limit=20)
        
        if not flashcards:
            await update.message.reply_text(
                "❌ No flashcards found in the database!\n\n"
                "Please add some flashcards first or contact the administrator.",
                parse_mode='Markdown'
            )
            return
        
        # Initialize user session
        user_sessions[user_id] = {
            'learning_mode': True,
            'flashcards': flashcards.copy(),
            'current_flashcard': None,
            'score': 0,
            'total_questions': 0
        }
        
        await update.message.reply_text(
            f"🎓 *Learning Mode Started!*\n\n"
            f"📚 Loaded {len(flashcards)} flashcards from database\n"
            f"I'll ask you flashcard questions. Answer them and I'll check your responses.\n"
            f"Type /finish to exit learning mode.\n\n"
            f"Let's begin!", 
            parse_mode='Markdown'
        )
        
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
        
        if user_id in user_sessions and user_sessions[user_id].get('learning_mode'):
            session = user_sessions[user_id]
            score = session.get('score', 0)
            total = session.get('total_questions', 0)
            
            # Clear session
            del user_sessions[user_id]
            
            await update.message.reply_text(
                f"🎓 *Learning Session Finished!*\n\n"
                f"📊 Final Score: {score}/{total}\n"
                f"🎯 Accuracy: {(score/total*100):.1f}%" if total > 0 else "No questions answered.\n\n"
                f"Back to normal mode. Send me a Russian word to analyze!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("You're not in learning mode. Use /learn to start!")
            
    except Exception as e:
        logger.error(f"Error in finish command: {e}")
        await update.message.reply_text("❌ Error finishing learning session. Please try again.")

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show flashcard dashboard with statistics and progress."""
    await update.message.chat.send_action(action="typing")
    
    try:
        # Get dashboard data
        dashboard_data = flashcard_service.get_dashboard_data()
        
        if not dashboard_data:
            await update.message.reply_text(
                "❌ Error retrieving dashboard data. Please try again later."
            )
            return
        
        # Extract data
        total = dashboard_data.get("total", 0)
        due_today = dashboard_data.get("due_today", 0)
        due_this_week = dashboard_data.get("due_this_week", 0)
        new_cards = dashboard_data.get("new", 0)
        mastered = dashboard_data.get("mastered", 0)
        recent_additions = dashboard_data.get("recent_additions", 0)
        recent_reviews = dashboard_data.get("recent_reviews", 0)
        progress_pct = dashboard_data.get("progress_percentage", 0)
        workload_pct = dashboard_data.get("workload_percentage", 0)
        
        # Build dashboard response
        response = "📊 *Flashcard Dashboard*\n\n"
        
        # Overview section
        response += "📚 *Overview:*\n"
        response += f"• Total flashcards: {total}\n"
        response += f"• Learning progress: {progress_pct}%\n"
        
        if total > 0:
            response += f"• Collection status: "
            if total < 50:
                response += "🌱 Getting started"
            elif total < 200:
                response += "📈 Growing collection"
            elif total < 500:
                response += "🎯 Solid foundation"
            else:
                response += "🏆 Extensive library"
            response += "\n\n"
        else:
            response += "\n"
        
        # Due cards section
        response += "⏰ *Due for Review:*\n"
        response += f"• Today: {due_today}"
        if workload_pct > 0:
            response += f" ({workload_pct}% of collection)"
        response += "\n"
        response += f"• This week: {due_this_week}\n"
        
        # Workload indicator
        if due_today == 0:
            response += "✅ No cards due today!\n\n"
        elif due_today <= 10:
            response += "😌 Light workload today\n\n"
        elif due_today <= 25:
            response += "📝 Moderate workload today\n\n"
        else:
            response += "💪 Heavy workload today\n\n"
        
        # Card status section
        response += "📈 *Card Status:*\n"
        response += f"• New cards: {new_cards}\n"
        response += f"• Mastered: {mastered}\n"
        response += f"• In progress: {total - new_cards - mastered}\n\n"
        
        # Recent activity section
        response += "🔄 *Recent Activity (7 days):*\n"
        response += f"• Cards added: {recent_additions}\n"
        response += f"• Reviews completed: {recent_reviews}\n\n"
        
        # Action suggestions
        if due_today > 0:
            response += f"💡 *Suggestion:* Use /learn to practice {min(due_today, 20)} cards!"
        elif new_cards > 0:
            response += "💡 *Suggestion:* Send Russian text to generate more flashcards!"
        else:
            response += "💡 *Suggestion:* Great job! Add more content to continue learning."
        
        # Send response
        try:
            await update.message.reply_markdown(response)
        except Exception as markdown_error:
            logger.warning(f"Markdown parsing failed: {markdown_error}. Sending as plain text.")
            await update.message.reply_text(response)
    
    except Exception as e:
        logger.error(f"Error in dashboard command: {e}")
        await update.message.reply_text(
            "❌ Error generating dashboard. Please try again later."
        )

async def dbstatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check MongoDB connection status and flashcard count."""
    await update.message.chat.send_action(action="typing")
    
    try:
        # Get flashcard statistics
        stats = flashcard_service.get_flashcard_stats()
        
        if stats:
            tags_str = ", ".join(stats.get('tags', [])[:5])  # Show first 5 tags
            if len(stats.get('tags', [])) > 5:
                tags_str += "..."
                
            await update.message.reply_text(
                f"🟢 *Database Status: Connected*\n\n"
                f"📊 *Flashcard Statistics:*\n"
                f"• Total: {stats.get('total', 0)}\n"
                f"• Two-sided: {stats.get('two_sided', 0)}\n"
                f"• Fill-in-blank: {stats.get('fill_in_blank', 0)}\n"
                f"• Multiple choice: {stats.get('multiple_choice', 0)}\n"
                f"• Due for review: {stats.get('due_for_review', 0)}\n"
                f"• Unique tags: {stats.get('unique_tags', 0)}\n"
                f"• Sample tags: {tags_str}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"🟢 *Database Status: Connected*\n\n"
                f"❌ Could not retrieve statistics",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        await update.message.reply_text(
            f"🔴 *Database Status: Disconnected*\n\n"
            f"❌ Error: {str(e)}\n\n"
            f"Please contact the administrator.",
            parse_mode='Markdown'
        )

def extract_russian_words(text: str) -> List[str]:
    """Extract Russian words from text, filtering out punctuation and non-Russian words."""
    # Remove punctuation and split into words
    # Cyrillic pattern to match Russian words
    russian_word_pattern = r'[а-яё]+(?:-[а-яё]+)*'
    words = re.findall(russian_word_pattern, text.lower())
    
    # Filter out very short words (likely particles/prepositions)
    meaningful_words = [word for word in words if len(word) >= 3]
    
    # Remove duplicates while preserving order
    unique_words = []
    seen = set()
    for word in meaningful_words:
        if word not in seen:
            unique_words.append(word)
            seen.add(word)
    
    return unique_words

async def build_grammar_response(grammar_data: dict) -> str:
    """Build a formatted response from grammar data."""
    # Determine if we're dealing with a noun, adjective, or verb based on the data structure
    if "gender" in grammar_data and "animacy" in grammar_data:
        # This is a noun
        response = (
            f"📝 *Noun:* {grammar_data['dictionary_form']}\n"
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
    elif "masculine" in grammar_data and "feminine" in grammar_data and "neuter" in grammar_data:
        # This is an adjective (showing first few forms for brevity)
        response = (
            f"📝 *Adjective:* {grammar_data['dictionary_form']}\n"
            f"🇬🇧 *English:* {grammar_data['english_translation']}\n\n"
            f"*Masculine Forms:*\n"
            f"• Nom: {grammar_data['masculine']['nom']}\n"
            f"• Gen: {grammar_data['masculine']['gen']}\n"
            f"• ... (and more forms)\n\n"
            f"*Feminine Forms:*\n"
            f"• Nom: {grammar_data['feminine']['nom']}\n"
            f"• Gen: {grammar_data['feminine']['gen']}\n"
            f"• ... (and more forms)"
        )
    elif "aspect" in grammar_data and "past_masculine" in grammar_data:
        # This is a verb (showing key forms for brevity)
        response = (
            f"📝 *Verb:* {grammar_data['dictionary_form']}\n"
            f"🇬🇧 *English:* {grammar_data['english_translation']}\n"
            f"⚡ *Aspect:* {grammar_data['aspect']}\n"
            f"🔄 *Conjugation:* {grammar_data['conjugation']}\n\n"
            f"*Past Tense:*\n"
            f"• он: {grammar_data['past_masculine']}\n"
            f"• она: {grammar_data['past_feminine']}\n"
            f"• ... (and more forms)"
        )
    else:
        # Unknown structure
        response = f"Analysis result:\n\n{json.dumps(grammar_data, indent=2, ensure_ascii=False)}"
    
    return response

async def ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the next flashcard question."""
    try:
        user_id = update.effective_user.id
        session = user_sessions.get(user_id)
        
        if not session or not session.get('learning_mode'):
            return
        
        if session['flashcards']:
            # Get next flashcard
            flashcard = session['flashcards'].pop(0)
            session['current_flashcard'] = flashcard
            
            # Format question for display
            question_text, keyboard = flashcard_service.format_question_for_bot(flashcard)
            
            # Try to send with markdown, fallback to plain text if it fails
            try:
                await update.message.reply_text(
                    question_text,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            except Exception as markdown_error:
                logger.warning(f"Markdown parsing failed for question: {markdown_error}. Sending as plain text.")
                await update.message.reply_text(
                    question_text,
                    reply_markup=keyboard
                )
        else:
            # No more questions - end the session
            score = session.get('score', 0)
            total = session.get('total_questions', 0)
            
            # Clear session to exit learning mode
            del user_sessions[user_id]
            
            await update.message.reply_text(
                f"🎉 *All questions completed!*\n\n"
                f"📊 Final Score: {score}/{total}\n"
                f"🎯 Accuracy: {(score/total*100):.1f}%\n\n" if total > 0 else ""
                f"Back to normal mode. Send me a Russian word to analyze or type /learn to start another session!",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error asking next question: {e}")
        await update.message.reply_text("❌ Error loading next question. Please try /learn again.")

async def process_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the user's answer to a flashcard question."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.get('learning_mode'):
        return
    
    current_flashcard = session.get('current_flashcard')
    if not current_flashcard:
        await update.message.reply_text("❌ No active flashcard found.")
        return
    
    user_answer = update.message.text.strip()
    
    # Update total questions count
    session['total_questions'] += 1
    
    # Check answer using the flashcard service
    is_correct, feedback = flashcard_service.check_answer(current_flashcard, user_answer)
    
    if is_correct:
        session['score'] += 1
    
    # Update flashcard statistics in database
    flashcard_service.update_flashcard_after_review(current_flashcard, is_correct)
    
    # Send feedback
    await update.message.reply_text(feedback, parse_mode='Markdown')
    
    # Ask next question
    await ask_next_question(update, context)

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
                
                # Get user session
                user_id = query.from_user.id
                session = user_sessions.get(user_id)
                
                if session and session.get('learning_mode') and session.get('current_flashcard'):
                    current_flashcard = session['current_flashcard']
                    
                    # Verify this is the correct flashcard
                    if str(current_flashcard.id) == flashcard_id:
                        # Check the answer
                        from app.flashcards.models import MultipleChoice
                        if isinstance(current_flashcard, MultipleChoice):
                            is_correct = selected_option in current_flashcard.correct_indices
                            
                            # Update session
                            session['total_questions'] += 1
                            if is_correct:
                                session['score'] += 1
                            
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
        session = user_sessions.get(user_id)
        
        if not session or not session.get('learning_mode'):
            return
        
        if session['flashcards']:
            # Get next flashcard
            flashcard = session['flashcards'].pop(0)
            session['current_flashcard'] = flashcard
            
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
            score = session.get('score', 0)
            total = session.get('total_questions', 0)
            
            # Clear session to exit learning mode
            del user_sessions[user_id]
            
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
        
        # Set user in editing mode
        user_id = query.from_user.id
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        
        user_sessions[user_id]['editing_mode'] = True
        user_sessions[user_id]['editing_flashcard_id'] = flashcard_id
        
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
        
        cancel_button = [[InlineKeyboardButton("❌ Cancel Edit", callback_data=f"cancel_edit_{flashcard_id}")]]
        keyboard = InlineKeyboardMarkup(cancel_button)
        
        await query.edit_message_text(
            f"✏️ *Edit Flashcard*\n\n"
            f"📋 Please copy the JSON below, edit it, and send it back:\n\n"
            f"```json\n{json_text}\n```\n\n"
            f"💡 *Instructions:*\n"
            f"• Copy the JSON text above\n"
            f"• Edit the fields you want to change\n"
            f"• Send the modified JSON back to me\n"
            f"• I'll validate and update the flashcard",
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
        # Get user session
        user_id = query.from_user.id
        session = user_sessions.get(user_id)
        
        if session and session.get('learning_mode') and session.get('current_flashcard'):
            current_flashcard = session['current_flashcard']
            
            if str(current_flashcard.id) == flashcard_id:
                # Update session stats
                session['total_questions'] += 1
                
                # Show the answer
                if isinstance(current_flashcard, TwoSidedCard):
                    answer_text = current_flashcard.back
                elif isinstance(current_flashcard, FillInTheBlank):
                    answer_text = ", ".join(current_flashcard.answers)
                else:
                    answer_text = "Answer not available"
                
                # Update flashcard as "seen" (neutral review)
                flashcard_service.update_flashcard_after_review(current_flashcard, True)
                
                await query.edit_message_text(
                    f"{query.message.text}\n\n"
                    f"💡 *Answer:* {answer_text}\n\n"
                    f"Moving to next question...",
                    parse_mode='Markdown'
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
            session = user_sessions.get(user_id)
            if session and session.get('learning_mode'):
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
        session = user_sessions.get(user_id)
        
        if session and session.get('learning_mode') and session.get('current_flashcard'):
            current_flashcard = session['current_flashcard']
            
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
        session = user_sessions.get(user_id)
        
        if session:
            # Clear editing mode
            session.pop('editing_mode', None)
            session.pop('editing_flashcard_id', None)
        
        # Return to the original question if in learning mode
        if session and session.get('learning_mode') and session.get('current_flashcard'):
            current_flashcard = session['current_flashcard']
            
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

async def process_flashcard_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process JSON edit input from user."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.get('editing_mode'):
        return
    
    flashcard_id = session.get('editing_flashcard_id')
    if not flashcard_id:
        await update.message.reply_text("❌ Error: No flashcard being edited.")
        return
    
    user_input = update.message.text.strip()
    
    try:
        # Parse JSON input
        import json
        updated_data = json.loads(user_input)
        
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
            # Clear editing mode
            session.pop('editing_mode', None)
            session.pop('editing_flashcard_id', None)
            
            await update.message.reply_text(
                "✅ *Flashcard Updated Successfully!*\n\n"
                "Your changes have been saved to the database.",
                parse_mode='Markdown'
            )
            
            # If in learning mode, continue with the updated flashcard
            if session.get('learning_mode'):
                # Get the updated flashcard
                updated_flashcard = flashcard_service.db.get_flashcard_by_id(flashcard_id)
                if updated_flashcard and session.get('current_flashcard') and str(session['current_flashcard'].id) == flashcard_id:
                    session['current_flashcard'] = updated_flashcard
                    
                    # Show the updated question
                    question_text, keyboard = flashcard_service.format_question_for_bot(updated_flashcard)
                    
                    try:
                        await update.message.reply_text(
                            f"📝 *Updated Question:*\n\n{question_text}",
                            parse_mode='Markdown',
                            reply_markup=keyboard
                        )
                    except Exception as markdown_error:
                        logger.warning(f"Markdown parsing failed: {markdown_error}")
                        await update.message.reply_text(
                            f"📝 Updated Question:\n\n{question_text}",
                            reply_markup=keyboard
                        )
        else:
            await update.message.reply_text("❌ Failed to update flashcard. Please try again.")
            
    except json.JSONDecodeError as e:
        await update.message.reply_text(
            f"❌ *Invalid JSON Format*\n\n"
            f"Error: {str(e)}\n\n"
            f"Please check your JSON syntax and try again.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error processing flashcard edit: {e}")
        await update.message.reply_text("❌ Error updating flashcard. Please try again.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route messages between learning mode, editing mode, and normal grammar analysis."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    # Check if user is in editing mode
    if session and session.get('editing_mode'):
        await process_flashcard_edit(update, context)
    # Check if user is in learning mode
    elif session and session.get('learning_mode') and session.get('current_flashcard'):
        await process_answer(update, context)
    else:
        await process_russian_text(update, context)

async def process_russian_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process Russian text (words or sentences) and generate flashcards automatically."""
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
        
        # Track results for each word
        successful_words = []
        failed_words = []
        total_flashcards = 0
        
        # Process each word
        for word in words:
            try:
                # Analyze the word with flashcard generation
                result = russian_tutor.invoke(word, generate_flashcards=True)
                
                if "final_answer" in result and result["final_answer"]:
                    # Parse grammar data
                    try:
                        grammar_data = json.loads(result["final_answer"])
                        word_type = "unknown"
                        
                        # Determine word type
                        if "gender" in grammar_data and "animacy" in grammar_data:
                            word_type = "noun"
                        elif "masculine" in grammar_data and "feminine" in grammar_data:
                            word_type = "adjective"
                        elif "aspect" in grammar_data and "past_masculine" in grammar_data:
                            word_type = "verb"
                        
                        flashcard_count = result.get("flashcards_generated", 0)
                        successful_words.append({
                            "word": word,
                            "type": word_type,
                            "dictionary_form": grammar_data.get("dictionary_form", word),
                            "flashcards": flashcard_count
                        })
                        total_flashcards += flashcard_count
                        
                    except json.JSONDecodeError:
                        failed_words.append(word)
                        
                else:
                    failed_words.append(word)
                    
            except Exception as e:
                logger.error(f"Error processing word '{word}': {e}")
                failed_words.append(word)
        
        # Build summary response
        if successful_words or failed_words:
            response = "📚 *Text Analysis Complete!*\n\n"
            
            if successful_words:
                response += f"✅ *Successfully processed {len(successful_words)} word{'s' if len(successful_words) != 1 else ''}:*\n"
                for word_info in successful_words:
                    response += f"• {word_info['dictionary_form']} ({word_info['type']}) - {word_info['flashcards']} flashcards\n"
                
                response += f"\n🎯 *Total flashcards generated:* {total_flashcards}\n"
                response += f"💾 All flashcards saved to database for spaced repetition!\n"
            
            if failed_words:
                response += f"\n⚠️ *Skipped {len(failed_words)} word{'s' if len(failed_words) != 1 else ''}:*\n"
                response += f"• {', '.join(failed_words)}\n"
                response += f"*(Unsupported word types or analysis errors)*\n"
            
            response += f"\n💡 Use /learn to practice with your flashcards!"
            
            # Send response
            try:
                await update.message.reply_markdown(response)
            except Exception as markdown_error:
                logger.warning(f"Markdown parsing failed: {markdown_error}. Sending as plain text.")
                await update.message.reply_text(response)
                
        else:
            await update.message.reply_text(
                "❌ I couldn't analyze any words from your text. "
                "Please try again with clear Russian words."
            )
    
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        await update.message.reply_text(
            "❌ Sorry, I encountered an error processing your text. Please try again."
        )

def init_application(token: str, tutor: RussianTutor) -> Application:
    """Start the bot with the Russian tutor."""
    global russian_tutor
    russian_tutor = tutor

    # Create the Application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("finish", finish_command))
    application.add_handler(CommandHandler("dbstatus", dbstatus_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application
