"""Markdown escaping utilities for Telegram messages."""

import logging

logger = logging.getLogger(__name__)


def escape_markdown(text: str) -> str:
    """Escape markdown special characters to prevent parsing errors.
    
    Args:
        text: Text to escape
        
    Returns:
        Text with markdown special characters escaped
    """
    try:
        # Characters that need escaping in Telegram markdown
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        escaped_text = text
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        
        return escaped_text
    except Exception as e:
        logger.error(f"Error escaping markdown: {e}")
        # Return plain text if escaping fails
        return text