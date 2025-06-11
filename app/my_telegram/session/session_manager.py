"""User session state management for the Telegram bot."""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """Represents a user's session state."""
    user_id: int
    
    # Learning mode state
    learning_mode: bool = False
    flashcards: list = field(default_factory=list)
    current_flashcard: Any = None
    score: int = 0
    total_questions: int = 0
    
    # Editing mode state
    editing_mode: bool = False
    editing_flashcard_id: Optional[str] = None
    
    # Regeneration mode state
    regenerating_mode: bool = False
    regenerating_flashcard_id: Optional[str] = None
    
    # Chatbot conversation history (last 20 messages)
    conversation_history: list = field(default_factory=list)
    
    def clear_learning_state(self):
        """Clear learning-related session state."""
        self.learning_mode = False
        self.flashcards = []
        self.current_flashcard = None
        self.score = 0
        self.total_questions = 0
    
    def clear_editing_state(self):
        """Clear editing-related session state."""
        self.editing_mode = False
        self.editing_flashcard_id = None
    
    def clear_regeneration_state(self):
        """Clear regeneration-related session state."""
        self.regenerating_mode = False
        self.regenerating_flashcard_id = None
    
    def clear_all_states(self):
        """Clear all session states."""
        self.clear_learning_state()
        self.clear_editing_state()
        self.clear_regeneration_state()
        self.clear_conversation_history()
    
    def add_message_to_history(self, message):
        """Add a message to conversation history, keeping only last 20 messages."""
        self.conversation_history.append(message)
        
        # Keep only the last 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def clear_conversation_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_conversation_history(self):
        """Get current conversation history."""
        return self.conversation_history.copy()


class SessionManager:
    """Manages user sessions for the Telegram bot."""
    
    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}
    
    def get_session(self, user_id: int) -> UserSession:
        """Get or create a user session.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            UserSession object
        """
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession(user_id=user_id)
        
        return self._sessions[user_id]
    
    def clear_session(self, user_id: int) -> bool:
        """Clear a user's session completely.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if session was cleared, False if it didn't exist
        """
        if user_id in self._sessions:
            del self._sessions[user_id]
            logger.info(f"Cleared session for user {user_id}")
            return True
        return False
    
    def is_in_learning_mode(self, user_id: int) -> bool:
        """Check if user is in learning mode."""
        session = self.get_session(user_id)
        return session.learning_mode
    
    def is_in_editing_mode(self, user_id: int) -> bool:
        """Check if user is in editing mode."""
        session = self.get_session(user_id)
        return session.editing_mode
    
    def is_in_regenerating_mode(self, user_id: int) -> bool:
        """Check if user is in regenerating mode."""
        session = self.get_session(user_id)
        return session.regenerating_mode
    
    def start_learning_session(self, user_id: int, flashcards: list) -> UserSession:
        """Start a learning session for a user.
        
        Args:
            user_id: Telegram user ID
            flashcards: List of flashcards to learn
            
        Returns:
            Updated UserSession
        """
        session = self.get_session(user_id)
        session.clear_all_states()
        session.learning_mode = True
        session.flashcards = flashcards.copy()
        session.score = 0
        session.total_questions = 0
        
        logger.info(f"Started learning session for user {user_id} with {len(flashcards)} flashcards")
        return session
    
    def start_editing_session(self, user_id: int, flashcard_id: str) -> UserSession:
        """Start an editing session for a user.
        
        Args:
            user_id: Telegram user ID
            flashcard_id: ID of flashcard being edited
            
        Returns:
            Updated UserSession
        """
        session = self.get_session(user_id)
        session.clear_editing_state()
        session.editing_mode = True
        session.editing_flashcard_id = flashcard_id
        
        logger.info(f"Started editing session for user {user_id}, flashcard {flashcard_id}")
        return session
    
    def start_regenerating_session(self, user_id: int, flashcard_id: str) -> UserSession:
        """Start a regenerating session for a user.
        
        Args:
            user_id: Telegram user ID
            flashcard_id: ID of flashcard being regenerated
            
        Returns:
            Updated UserSession
        """
        session = self.get_session(user_id)
        session.clear_regeneration_state()
        session.regenerating_mode = True
        session.regenerating_flashcard_id = flashcard_id
        
        logger.info(f"Started regeneration session for user {user_id}, flashcard {flashcard_id}")
        return session
    
    def get_active_sessions_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)
    
    def get_learning_sessions_count(self) -> int:
        """Get the number of users in learning mode."""
        return sum(1 for session in self._sessions.values() if session.learning_mode)


# Global session manager instance
session_manager = SessionManager()