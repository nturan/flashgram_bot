"""Text processing utilities for sentence generation."""

import logging

logger = logging.getLogger(__name__)


class TextProcessor:
    """Processes and cleans text for Telegram compatibility."""

    def clean_sentence_for_telegram(self, sentence: str) -> str:
        """Clean sentence to avoid Telegram markdown parsing issues."""
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

    def create_sentence_with_blank(
        self, sentence: str, target_form: str, stem: str
    ) -> str:
        """Create a sentence with masked suffix for fill-in-the-blank."""
        try:
            # Create the sentence with masked suffix
            masked_word = f"{stem}{{blank}}"
            sentence_with_blank = sentence.replace(target_form, masked_word)

            # If replacement didn't work (case differences, etc.), try case-insensitive
            if "{blank}" not in sentence_with_blank:
                # Try to find the word with different cases
                words = sentence.split()
                for i, word in enumerate(words):
                    clean_word = (
                        word.lower()
                        .replace(".", "")
                        .replace(",", "")
                        .replace("!", "")
                        .replace("?", "")
                    )
                    if clean_word == target_form.lower():
                        # Replace this word with the masked version
                        punctuation = ""
                        for punct in ".,!?":
                            if word.endswith(punct):
                                punctuation = punct
                                break

                        words[i] = f"{stem}{{blank}}{punctuation}"
                        sentence_with_blank = " ".join(words)
                        break

                # If still no blank, add it at the end
                if "{blank}" not in sentence_with_blank:
                    sentence_with_blank = f"{sentence} ({stem}{{blank}})"

            return sentence_with_blank

        except Exception as e:
            logger.error(f"Error creating sentence with blank: {e}")
            return f"{sentence} ({stem}{{blank}})"
