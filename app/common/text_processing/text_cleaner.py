"""Text cleaning utilities for Telegram compatibility."""

import logging

logger = logging.getLogger(__name__)


def clean_sentence_for_telegram(sentence: str) -> str:
    """Clean sentence to avoid Telegram markdown parsing issues.

    Args:
        sentence: Raw sentence from LLM or other source

    Returns:
        Cleaned sentence safe for Telegram
    """
    try:
        # Remove or replace problematic characters that can break markdown
        problematic_chars = {
            '"': "",  # Remove quotes
            "'": "",  # Remove single quotes
            "«": "",  # Remove Russian quotes
            "»": "",  # Remove Russian quotes
            "_": " ",  # Replace underscores with spaces
            "*": "",  # Remove asterisks
            "`": "",  # Remove backticks
            "[": "(",  # Replace square brackets
            "]": ")",
            "{": "(",  # Replace curly brackets
            "}": ")",
            "|": " ",  # Replace pipes with spaces
            "\\": "",  # Remove backslashes
        }

        cleaned = sentence
        for char, replacement in problematic_chars.items():
            cleaned = cleaned.replace(char, replacement)

        # Clean up multiple spaces
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")

        return cleaned.strip()

    except Exception as e:
        logger.error(f"Error cleaning sentence: {e}")
        return sentence
