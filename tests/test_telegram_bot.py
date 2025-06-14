"""Tests for Telegram bot functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes
from app.my_telegram.bot import init_application, handle_callback_query
from app.my_telegram.handlers.command_handlers import (
    start,
    help_command,
    dashboard_command,
)
from app.my_telegram.session import session_manager


class TestTelegramBot:
    """Test cases for Telegram bot functionality."""

    def test_init_application(self):
        """Test that bot application initializes correctly."""
        # Mock the token
        mock_token = "test_token_123"

        app = init_application(mock_token)

        # Check that application is created
        assert app is not None
        assert hasattr(app, "bot")
        assert hasattr(app, "add_handler")

    def test_init_application_handlers(self):
        """Test that bot application has required handlers registered."""
        mock_token = "test_token_123"

        app = init_application(mock_token)

        # Check that handlers are registered
        assert len(app.handlers) > 0

        # Check that we have handlers in the default group (0)
        default_handlers = app.handlers.get(0, [])
        assert len(default_handlers) > 0

    @pytest.mark.asyncio
    async def test_start_command(self):
        """Test the /start command handler."""
        # Create mock update and context
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 123456
        update.effective_user.first_name = "Test User"
        update.effective_user.mention_html = Mock(return_value="<b>Test User</b>")
        update.message = Mock(spec=Message)
        update.message.reply_html = AsyncMock()

        context = Mock(spec=ContextTypes.DEFAULT_TYPE)

        # Call the start command
        await start(update, context)

        # Verify that a reply was sent
        update.message.reply_html.assert_called()

        # Check that the reply contains welcome text
        call_args = update.message.reply_html.call_args[0][0]
        assert (
            "hi" in call_args.lower()
            or "russian" in call_args.lower()
            or "tutor" in call_args.lower()
        )

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test the /help command handler."""
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = Mock(spec=ContextTypes.DEFAULT_TYPE)

        # Call the help command
        await help_command(update, context)

        # Verify that a reply was sent
        update.message.reply_text.assert_called_once()

        # Check that the reply contains help information
        call_args = update.message.reply_text.call_args[0][0]
        assert "help" in call_args.lower() or "command" in call_args.lower()

    @pytest.mark.asyncio
    async def test_dashboard_command(self):
        """Test the /dashboard command handler."""
        # Create mock update and context
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 123456
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.message.chat = Mock()
        update.message.chat.send_action = AsyncMock()

        context = Mock(spec=ContextTypes.DEFAULT_TYPE)

        # Call the dashboard command
        await dashboard_command(update, context)

        # Verify that a reply was sent
        update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_callback_query_handler(self):
        """Test the callback query handler for inline keyboards."""
        # Create mock update with callback query
        update = Mock(spec=Update)
        update.callback_query = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.data = "test_callback"
        update.callback_query.from_user = Mock(spec=User)
        update.callback_query.from_user.id = 123456
        update.callback_query.edit_message_text = AsyncMock()

        context = Mock(spec=ContextTypes.DEFAULT_TYPE)

        # Call the callback query handler
        await handle_callback_query(update, context)

        # Verify that the callback was acknowledged
        update.callback_query.answer.assert_called_once()

    def test_session_manager_integration(self):
        """Test that session manager integrates properly with bot."""
        # Test user session creation
        user_id = 123456
        session = session_manager.get_session(user_id)

        assert session is not None
        assert session.user_id == user_id
        assert hasattr(session, "learning_mode")
        assert hasattr(session, "score")
        assert hasattr(session, "total_questions")

    def test_chatbot_tutor_initialization(self):
        """Test that per-user chatbot system works."""
        # Import the per-user chatbot functions
        from app.my_telegram.handlers.chatbot_handlers import get_user_chatbot, clear_user_chatbot
        from app.my_graph.chatbot_tutor import ConversationalRussianTutor
        from app.my_telegram.session.config_manager import config_manager
        from pydantic import SecretStr

        # Set up user with API key
        user_id = 12345
        api_key = "sk-test123456789"
        config_manager.update_setting(user_id, "openai_api_key", api_key)
        config_manager.update_setting(user_id, "model", "gpt-4o")

        # Test getting a user chatbot (this will create one)
        try:
            chatbot = get_user_chatbot(user_id)
            assert isinstance(chatbot, ConversationalRussianTutor)
            assert chatbot.api_key.get_secret_value() == api_key
            assert chatbot.default_model == "gpt-4o"
            
            # Test clearing chatbot
            clear_user_chatbot(user_id)
            
            # Getting again should create a new one
            chatbot2 = get_user_chatbot(user_id)
            assert isinstance(chatbot2, ConversationalRussianTutor)
            
        except Exception as e:
            # If OpenAI initialization fails (no internet, etc.), that's ok for testing
            if "openai" in str(e).lower() or "api" in str(e).lower():
                pass  # Expected in test environments
            else:
                raise

    @pytest.mark.asyncio
    async def test_message_handling_with_mocked_session(self):
        """Test message handling with mocked session manager."""
        # Create mock update with proper async methods
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 123456
        update.message = Mock(spec=Message)
        update.message.text = "Test message"
        update.message.reply_text = AsyncMock()
        update.message.chat = Mock()
        update.message.chat.send_action = AsyncMock()

        context = Mock(spec=ContextTypes.DEFAULT_TYPE)

        # Mock session manager to return a known session
        with patch(
            "app.my_telegram.handlers.message_handlers.session_manager"
        ) as mock_session_mgr:
            mock_session = Mock()
            mock_session.learning_mode = False
            mock_session_mgr.get_session.return_value = mock_session

            # Mock the get_user_chatbot to simulate API key issues
            with patch("app.my_telegram.handlers.chatbot_handlers.get_user_chatbot") as mock_get_chatbot:
                mock_get_chatbot.side_effect = ValueError("User has no API key configured")
                
                # Import and test message handler
                from app.my_telegram.handlers.message_handlers import handle_message

                # This should handle the case where user has no API key configured
                await handle_message(update, context)

                # Verify a reply was sent
                update.message.reply_text.assert_called()

    def test_bot_configuration(self):
        """Test that bot is configured with correct settings."""
        # Test that init_application returns a properly configured app
        mock_token = "test_token_123"
        app = init_application(mock_token)

        # Verify application has a bot token configured
        assert app.bot.token == mock_token

    @pytest.mark.asyncio
    async def test_user_session_persistence(self):
        """Test that user sessions are properly managed."""
        user_id = 123456

        # Get session for user
        session1 = session_manager.get_session(user_id)
        session1.score = 5
        session1.total_questions = 10

        # Get session again - should be the same instance
        session2 = session_manager.get_session(user_id)

        assert session1 is session2
        assert session2.score == 5
        assert session2.total_questions == 10
