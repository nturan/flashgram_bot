"""Common inline keyboard factory for Telegram bot."""

import logging
from typing import List, Tuple, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


def create_edit_delete_keyboard(
    item_id: str,
    show_answer: bool = True,
    additional_buttons: Optional[List[Tuple[str, str]]] = None,
) -> InlineKeyboardMarkup:
    """Create a standard edit/delete keyboard for flashcards.

    Args:
        item_id: ID of the item to edit/delete
        show_answer: Whether to show answer button
        additional_buttons: List of (text, callback_data) tuples for extra buttons

    Returns:
        InlineKeyboardMarkup with edit/delete buttons
    """
    try:
        buttons = []

        # Main action buttons
        main_row = [
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{item_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{item_id}"),
        ]
        buttons.append(main_row)

        # Answer button for non-multiple choice cards
        if show_answer:
            buttons.append(
                [InlineKeyboardButton("📝 Answer", callback_data=f"answer_{item_id}")]
            )

        # Additional buttons if provided
        if additional_buttons:
            for text, callback_data in additional_buttons:
                buttons.append(
                    [InlineKeyboardButton(text, callback_data=callback_data)]
                )

        return InlineKeyboardMarkup(buttons)

    except Exception as e:
        logger.error(f"Error creating edit/delete keyboard: {e}")
        return InlineKeyboardMarkup([])


def create_confirmation_keyboard(
    item_id: str,
    action: str = "delete",
    confirm_text: str = "⚠️ Yes",
    cancel_text: str = "❌ Cancel",
) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard for destructive actions.

    Args:
        item_id: ID of the item
        action: Action to confirm (e.g., 'delete', 'reset')
        confirm_text: Text for confirmation button
        cancel_text: Text for cancel button

    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    try:
        buttons = [
            [
                InlineKeyboardButton(
                    confirm_text, callback_data=f"confirm_{action}_{item_id}"
                ),
                InlineKeyboardButton(
                    cancel_text, callback_data=f"cancel_{action}_{item_id}"
                ),
            ]
        ]

        return InlineKeyboardMarkup(buttons)

    except Exception as e:
        logger.error(f"Error creating confirmation keyboard: {e}")
        return InlineKeyboardMarkup([])


def create_multiple_choice_keyboard(
    options: List[str], item_id: str, include_controls: bool = True
) -> InlineKeyboardMarkup:
    """Create a multiple choice keyboard with options.

    Args:
        options: List of option texts
        item_id: ID of the flashcard
        include_controls: Whether to include edit/delete controls

    Returns:
        InlineKeyboardMarkup with option buttons
    """
    try:
        buttons = []

        # Add option buttons
        for i, option in enumerate(options):
            callback_data = f"mc_{item_id}_{i}"
            button = InlineKeyboardButton(
                text=f"{chr(65 + i)}. {option}",  # A, B, C, etc.
                callback_data=callback_data,
            )
            buttons.append([button])  # Each button on its own row

        # Add control buttons if requested
        if include_controls:
            control_buttons = [
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{item_id}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{item_id}"),
            ]
            buttons.append(control_buttons)

        return InlineKeyboardMarkup(buttons)

    except Exception as e:
        logger.error(f"Error creating multiple choice keyboard: {e}")
        return InlineKeyboardMarkup([])
