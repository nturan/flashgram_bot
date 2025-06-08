"""Safe message sending utilities for Telegram bot."""

import logging
from typing import Optional, Union
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def safe_send_markdown(update: Update, 
                           text: str, 
                           reply_markup: Optional[InlineKeyboardMarkup] = None,
                           fallback_plain: bool = True) -> bool:
    """Safely send a message with markdown, falling back to plain text if needed.
    
    Args:
        update: Telegram update object
        text: Message text with markdown formatting
        reply_markup: Optional inline keyboard
        fallback_plain: Whether to send plain text if markdown fails
        
    Returns:
        True if message was sent successfully
    """
    try:
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return True
        
    except Exception as markdown_error:
        logger.warning(f"Markdown parsing failed: {markdown_error}")
        
        if fallback_plain:
            try:
                # Remove markdown formatting and send as plain text
                plain_text = _strip_markdown(text)
                await update.message.reply_text(
                    plain_text,
                    reply_markup=reply_markup
                )
                return True
            except Exception as plain_error:
                logger.error(f"Failed to send plain text message: {plain_error}")
        
        return False


async def safe_edit_markdown(query_or_message, 
                           text: str, 
                           reply_markup: Optional[InlineKeyboardMarkup] = None,
                           fallback_plain: bool = True) -> bool:
    """Safely edit a message with markdown, falling back to plain text if needed.
    
    Args:
        query_or_message: Telegram CallbackQuery or Message object
        text: Message text with markdown formatting
        reply_markup: Optional inline keyboard
        fallback_plain: Whether to send plain text if markdown fails
        
    Returns:
        True if message was edited successfully
    """
    try:
        if hasattr(query_or_message, 'edit_message_text'):
            # This is a callback query
            await query_or_message.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            # This is a message object
            await query_or_message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        return True
        
    except Exception as markdown_error:
        logger.warning(f"Markdown editing failed: {markdown_error}")
        
        if fallback_plain:
            try:
                # Remove markdown formatting and edit as plain text
                plain_text = _strip_markdown(text)
                if hasattr(query_or_message, 'edit_message_text'):
                    await query_or_message.edit_message_text(
                        plain_text,
                        reply_markup=reply_markup
                    )
                else:
                    await query_or_message.edit_text(
                        plain_text,
                        reply_markup=reply_markup
                    )
                return True
            except Exception as plain_error:
                logger.error(f"Failed to edit message with plain text: {plain_error}")
        
        return False


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting from text.
    
    Args:
        text: Text with markdown formatting
        
    Returns:
        Plain text without markdown
    """
    # Remove common markdown formatting
    replacements = {
        '*': '',      # Bold
        '_': '',      # Italic
        '`': '',      # Code
        '\\': '',     # Escapes
    }
    
    plain_text = text
    for char, replacement in replacements.items():
        plain_text = plain_text.replace(char, replacement)
    
    return plain_text