from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import json
import random
from pydantic import SecretStr
import logging
from typing import Dict, List, Tuple, Optional

from app.my_graph.language_tutor import RussianTutor

# Get module-level logger
logger = logging.getLogger(__name__)

# This will be initialized in init_application
russian_tutor = None

# Simple flashcard test data (question -> answer)
TEST_FLASHCARDS: List[Tuple[str, str]] = [
    ("What is A?", "B"),
    ("What is C?", "D"),
    ("What is E?", "F"),
    ("What is G?", "H"),
    ("What is I?", "J"),
]

# User session data to track learn mode
user_sessions: Dict[int, Dict] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm a Russian language tutor bot. Send me a Russian noun, adjective, or verb, and I'll analyze its grammar for you.",
        reply_markup=ForceReply(selective=True)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "I can help you learn Russian grammar!\n\n"
        "Just send me a Russian word, and I'll analyze it for you:\n\n"
        "• For nouns: I'll show gender, animacy, and all case forms\n"
        "• For adjectives: I'll show all gender forms, cases, and special forms\n"
        "• For verbs: I'll show aspect, conjugation, and all tense forms\n\n"
        "Commands:\n"
        "• /learn - Start flashcard learning mode\n"
        "• /finish - Exit learning mode\n\n"
        "Examples to try:\n"
        "- 'книга' (book) or 'стол' (table) for nouns\n"
        "- 'красивый' (beautiful) or 'хороший' (good) for adjectives\n"
        "- 'читать' (to read) or 'идти' (to go) for verbs"
    )

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the flashcard learning mode."""
    user_id = update.effective_user.id
    
    # Initialize user session
    user_sessions[user_id] = {
        'learning_mode': True,
        'flashcards': TEST_FLASHCARDS.copy(),
        'current_question': None,
        'current_answer': None,
        'score': 0,
        'total_questions': 0
    }
    
    # Shuffle flashcards for random order
    random.shuffle(user_sessions[user_id]['flashcards'])
    
    await update.message.reply_text(
        "🎓 *Learning Mode Started!*\n\n"
        "I'll ask you flashcard questions. Answer them and I'll check your responses.\n"
        "Type /finish to exit learning mode.\n\n"
        "Let's begin!", 
        parse_mode='Markdown'
    )
    
    # Ask the first question
    await ask_next_question(update, context)

async def finish_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exit the flashcard learning mode."""
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

async def ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the next flashcard question."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.get('learning_mode'):
        return
    
    if session['flashcards']:
        # Get next question
        question, answer = session['flashcards'].pop(0)
        session['current_question'] = question
        session['current_answer'] = answer
        
        await update.message.reply_text(
            f"❓ *Question:*\n{question}",
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

async def process_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the user's answer to a flashcard question."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session or not session.get('learning_mode'):
        return
    
    user_answer = update.message.text.strip()
    correct_answer = session.get('current_answer', '')
    
    # Update total questions count
    session['total_questions'] += 1
    
    # Check if answer is correct (case-insensitive)
    is_correct = user_answer.lower() == correct_answer.lower()
    
    if is_correct:
        session['score'] += 1
        await update.message.reply_text(
            f"✅ *Correct!* \n\nAnswer: {correct_answer}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ *Incorrect.*\n\nYour answer: {user_answer}\nCorrect answer: {correct_answer}",
            parse_mode='Markdown'
        )
    
    # Ask next question after a brief pause
    await ask_next_question(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route messages between learning mode and normal grammar analysis."""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    # Check if user is in learning mode
    if session and session.get('learning_mode') and session.get('current_question'):
        await process_answer(update, context)
    else:
        await process_russian_word(update, context)

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

                # Determine if we're dealing with a noun or adjective based on the data structure
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
                    # This is an adjective
                    response = (
                        f"📝 *Adjective:* {grammar_data['dictionary_form']}\n"
                        f"🇬🇧 *English:* {grammar_data['english_translation']}\n\n"
                        f"*Masculine Forms:*\n"
                        f"• Nom: {grammar_data['masculine']['nom']}\n"
                        f"• Gen: {grammar_data['masculine']['gen']}\n"
                        f"• Dat: {grammar_data['masculine']['dat']}\n"
                        f"• Acc: {grammar_data['masculine']['acc']}\n"
                        f"• Ins: {grammar_data['masculine']['ins']}\n"
                        f"• Pre: {grammar_data['masculine']['pre']}\n\n"
                        f"*Feminine Forms:*\n"
                        f"• Nom: {grammar_data['feminine']['nom']}\n"
                        f"• Gen: {grammar_data['feminine']['gen']}\n"
                        f"• Dat: {grammar_data['feminine']['dat']}\n"
                        f"• Acc: {grammar_data['feminine']['acc']}\n"
                        f"• Ins: {grammar_data['feminine']['ins']}\n"
                        f"• Pre: {grammar_data['feminine']['pre']}\n\n"
                        f"*Neuter Forms:*\n"
                        f"• Nom: {grammar_data['neuter']['nom']}\n"
                        f"• Gen: {grammar_data['neuter']['gen']}\n"
                        f"• Dat: {grammar_data['neuter']['dat']}\n"
                        f"• Acc: {grammar_data['neuter']['acc']}\n"
                        f"• Ins: {grammar_data['neuter']['ins']}\n"
                        f"• Pre: {grammar_data['neuter']['pre']}\n\n"
                        f"*Plural Forms:*\n"
                        f"• Nom: {grammar_data['plural']['nom']}\n"
                        f"• Gen: {grammar_data['plural']['gen']}\n"
                        f"• Dat: {grammar_data['plural']['dat']}\n"
                        f"• Acc: {grammar_data['plural']['acc']}\n"
                        f"• Ins: {grammar_data['plural']['ins']}\n"
                        f"• Pre: {grammar_data['plural']['pre']}"
                    )

                    # Add short forms if available
                    short_forms = []
                    if grammar_data.get('short_form_masculine'):
                        short_forms.append(f"• Masculine: {grammar_data['short_form_masculine']}")
                    if grammar_data.get('short_form_feminine'):
                        short_forms.append(f"• Feminine: {grammar_data['short_form_feminine']}")
                    if grammar_data.get('short_form_neuter'):
                        short_forms.append(f"• Neuter: {grammar_data['short_form_neuter']}")
                    if grammar_data.get('short_form_plural'):
                        short_forms.append(f"• Plural: {grammar_data['short_form_plural']}")

                    if short_forms:
                        response += "\n\n*Short Forms:*\n" + "\n".join(short_forms)

                    # Add comparative and superlative if available
                    degree_forms = []
                    if grammar_data.get('comparative'):
                        degree_forms.append(f"• Comparative: {grammar_data['comparative']}")
                    if grammar_data.get('superlative'):
                        degree_forms.append(f"• Superlative: {grammar_data['superlative']}")

                    if degree_forms:
                        response += "\n\n*Degree Forms:*\n" + "\n".join(degree_forms)
                elif "aspect" in grammar_data and "past_masculine" in grammar_data:
                    # This is a verb
                    response = (
                        f"📝 *Verb:* {grammar_data['dictionary_form']}\n"
                        f"🇬🇧 *English:* {grammar_data['english_translation']}\n"
                        f"⚡ *Aspect:* {grammar_data['aspect']}\n"
                        f"🔄 *Conjugation:* {grammar_data['conjugation']}\n"
                    )
                    
                    # Add aspect pair if available
                    if grammar_data.get('aspect_pair') and grammar_data['aspect_pair'] is not None:
                        response += f"👥 *Aspect Pair:* {grammar_data['aspect_pair']}\n"
                    
                    # Add motion characteristics if applicable
                    if grammar_data.get('unidirectional') or grammar_data.get('multidirectional'):
                        motion_type = []
                        if grammar_data.get('unidirectional'):
                            motion_type.append("unidirectional")
                        if grammar_data.get('multidirectional'):
                            motion_type.append("multidirectional")
                        response += f"🏃 *Motion:* {', '.join(motion_type)}\n"
                    
                    response += "\n"
                    
                    # Add present tense forms (for imperfective verbs)
                    if grammar_data.get('present_first_singular') and grammar_data['present_first_singular'] is not None:
                        response += (
                            f"*Present Tense:*\n"
                            f"• я: {grammar_data['present_first_singular']}\n"
                            f"• ты: {grammar_data['present_second_singular']}\n"
                            f"• он/она/оно: {grammar_data['present_third_singular']}\n"
                            f"• мы: {grammar_data['present_first_plural']}\n"
                            f"• вы: {grammar_data['present_second_plural']}\n"
                            f"• они: {grammar_data['present_third_plural']}\n\n"
                        )
                    
                    # Add past tense forms
                    response += (
                        f"*Past Tense:*\n"
                        f"• он: {grammar_data['past_masculine']}\n"
                        f"• она: {grammar_data['past_feminine']}\n"
                        f"• оно: {grammar_data['past_neuter']}\n"
                        f"• они: {grammar_data['past_plural']}\n"
                    )
                    
                    # Add future tense forms if available
                    if grammar_data.get('future_first_singular') and grammar_data['future_first_singular'] is not None:
                        response += (
                            f"\n*Future Tense:*\n"
                            f"• я: {grammar_data['future_first_singular']}\n"
                            f"• ты: {grammar_data['future_second_singular']}\n"
                            f"• он/она/оно: {grammar_data['future_third_singular']}\n"
                            f"• мы: {grammar_data['future_first_plural']}\n"
                            f"• вы: {grammar_data['future_second_plural']}\n"
                            f"• они: {grammar_data['future_third_plural']}\n"
                        )
                    
                    # Add imperative forms if available
                    imperative_forms = []
                    if grammar_data.get('imperative_singular') and grammar_data['imperative_singular'] is not None:
                        imperative_forms.append(f"• Singular: {grammar_data['imperative_singular']}")
                    if grammar_data.get('imperative_plural') and grammar_data['imperative_plural'] is not None:
                        imperative_forms.append(f"• Plural: {grammar_data['imperative_plural']}")
                    
                    if imperative_forms:
                        response += "\n*Imperative:*\n" + "\n".join(imperative_forms)
                else:
                    # Unknown structure - use text mode to avoid markdown issues
                    response = f"Analysis result:\n\n{json.dumps(grammar_data, indent=2, ensure_ascii=False)}"
                    # Send as plain text to avoid markdown parsing issues
                    await update.message.reply_text(response)
                    return

                # Try to send as markdown, fallback to plain text if it fails
                try:
                    await update.message.reply_markdown(response)
                except Exception as markdown_error:
                    logger.warning(f"Markdown parsing failed: {markdown_error}. Sending as plain text.")
                    await update.message.reply_text(response)
            except json.JSONDecodeError:
                # If we can't parse JSON, just send the raw result
                await update.message.reply_text(f"Analysis result:\n\n{result['final_answer']}")
        else:
            await update.message.reply_text("I couldn't analyze that word. Please try again with a Russian noun or adjective.")

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
    application.add_handler(CommandHandler("learn", learn_command))
    application.add_handler(CommandHandler("finish", finish_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return application
