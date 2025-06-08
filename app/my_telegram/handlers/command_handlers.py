"""Basic command handlers for the Telegram bot."""

import logging
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

from app.flashcards import flashcard_service
from app.common.telegram_utils import safe_send_markdown

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm a Russian language tutor bot. Send me Russian words or sentences, and I'll automatically analyze them and create flashcards for practice!",
        reply_markup=ForceReply(selective=True)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
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
    
    await update.message.reply_text(help_text)


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
        await safe_send_markdown(update, response)
    
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
                
            response = (
                f"🟢 *Database Status: Connected*\n\n"
                f"📊 *Flashcard Statistics:*\n"
                f"• Total: {stats.get('total', 0)}\n"
                f"• Two-sided: {stats.get('two_sided', 0)}\n"
                f"• Fill-in-blank: {stats.get('fill_in_blank', 0)}\n"
                f"• Multiple choice: {stats.get('multiple_choice', 0)}\n"
                f"• Due for review: {stats.get('due_for_review', 0)}\n"
                f"• Unique tags: {stats.get('unique_tags', 0)}\n"
                f"• Sample tags: {tags_str}"
            )
            
            await safe_send_markdown(update, response)
        else:
            await safe_send_markdown(
                update,
                f"🟢 *Database Status: Connected*\n\n"
                f"❌ Could not retrieve statistics"
            )
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        await safe_send_markdown(
            update,
            f"🔴 *Database Status: Disconnected*\n\n"
            f"❌ Error: {str(e)}\n\n"
            f"Please contact the administrator."
        )