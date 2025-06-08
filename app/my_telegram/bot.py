from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import json
import logging
import re
from typing import Dict, List, Optional, Any

from pydantic import SecretStr

from app.my_graph.language_tutor import RussianTutor
from app.flashcards import flashcard_service

# Get module-level logger
logger = logging.getLogger(__name__)

# This will be initialized in init_application
russian_tutor: Optional[RussianTutor] = None

# User session data to track learn mode
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
            question_text = flashcard_service.format_question_for_bot(flashcard)
            
            await update.message.reply_text(
                question_text,
                parse_mode='Markdown'
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route messages between learning mode and normal grammar analysis."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    # Check if user is in learning mode
    if session and session.get('learning_mode') and session.get('current_flashcard'):
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application
