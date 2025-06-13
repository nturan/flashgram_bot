"""Tests for MongoDB connection and database functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.flashcards.database import FlashcardDatabaseV2
from app.flashcards.models import TwoSidedCard, FlashcardType, DifficultyLevel


class TestMongoDBConnection:
    """Test cases for MongoDB connection and basic database operations."""
    
    def test_database_connection_success(self):
        """Test successful MongoDB connection."""
        # This test will use the actual database connection
        # It should work if MongoDB credentials are properly configured
        try:
            db = FlashcardDatabaseV2()
            assert db.client is not None
            assert db.db is not None
            assert db.collection is not None
            assert db.dictionary_words_collection is not None
        except (ConnectionFailure, ServerSelectionTimeoutError):
            pytest.skip("MongoDB connection not available for testing")
    
    @patch('app.flashcards.database.MongoClient')
    def test_database_connection_failure(self, mock_mongo_client):
        """Test MongoDB connection failure handling."""
        # Mock connection failure
        mock_mongo_client.side_effect = ConnectionFailure("Connection failed")
        
        with pytest.raises(ConnectionFailure):
            FlashcardDatabaseV2()
    
    @patch('app.flashcards.database.MongoClient')
    def test_database_ping_failure(self, mock_mongo_client):
        """Test MongoDB ping failure handling."""
        # Mock successful client creation but ping failure
        mock_client = Mock()
        mock_client.admin.command.side_effect = ServerSelectionTimeoutError("Ping failed")
        mock_mongo_client.return_value = mock_client
        
        with pytest.raises(ServerSelectionTimeoutError):
            FlashcardDatabaseV2()
    
    def test_add_flashcard_success(self):
        """Test adding a flashcard to the database."""
        try:
            db = FlashcardDatabaseV2()
            
            # Create a test flashcard
            test_card = TwoSidedCard(
                front="Test Question",
                back="Test Answer",
                type=FlashcardType.TWO_SIDED,
                tags=["test"],
                difficulty=DifficultyLevel.EASY
            )
            
            # Try to add the flashcard
            card_id = db.add_flashcard(test_card)
            
            # Should return a valid ID string
            assert card_id is not None
            assert isinstance(card_id, str)
            assert len(card_id) > 0
            
            # Clean up - try to remove the test card
            if card_id:
                try:
                    from bson import ObjectId
                    db.collection.delete_one({"_id": ObjectId(card_id)})
                except:
                    pass  # Cleanup failure is not critical for the test
                    
        except (ConnectionFailure, ServerSelectionTimeoutError):
            pytest.skip("MongoDB connection not available for testing")
    
    @patch('app.flashcards.database.FlashcardDatabaseV2._connect')
    def test_add_flashcard_with_mock(self, mock_connect):
        """Test adding flashcard with mocked database connection."""
        # Create a database instance with mocked connection
        db = FlashcardDatabaseV2()
        
        # Mock the collection and its insert_one method
        mock_collection = Mock()
        mock_result = Mock()
        mock_result.inserted_id = "test_id_123"
        mock_collection.insert_one.return_value = mock_result
        db.collection = mock_collection
        
        # Create test flashcard
        test_card = TwoSidedCard(
            front="Test Question",
            back="Test Answer",
            type=FlashcardType.TWO_SIDED,
            tags=["test"],
            difficulty=DifficultyLevel.EASY
        )
        
        # Test adding flashcard
        result_id = db.add_flashcard(test_card)
        
        # Verify the result
        assert result_id == "test_id_123"
        assert mock_collection.insert_one.called
    
    def test_database_collections_exist(self):
        """Test that required database collections are accessible."""
        try:
            db = FlashcardDatabaseV2()
            
            # Test that we can access collection methods
            assert hasattr(db.collection, 'insert_one')
            assert hasattr(db.collection, 'find')
            assert hasattr(db.dictionary_words_collection, 'insert_one')
            assert hasattr(db.dictionary_words_collection, 'find')
            
        except (ConnectionFailure, ServerSelectionTimeoutError):
            pytest.skip("MongoDB connection not available for testing")
    
    def test_connection_timeout_settings(self):
        """Test that connection timeout settings are properly configured."""
        try:
            with patch('app.flashcards.database.MongoClient') as mock_client:
                # Mock successful connection
                mock_instance = Mock()
                mock_instance.admin.command.return_value = True
                mock_client.return_value = mock_instance
                
                db = FlashcardDatabaseV2()
                
                # Verify MongoClient was called with timeout settings
                mock_client.assert_called_once()
                call_args = mock_client.call_args
                
                # Check that timeout parameters were passed in kwargs
                if call_args and len(call_args) > 1:
                    kwargs = call_args[1]
                    assert 'serverSelectionTimeoutMS' in kwargs
                    assert 'connectTimeoutMS' in kwargs
                    assert 'socketTimeoutMS' in kwargs
                    
                    # Verify timeout values
                    assert kwargs['serverSelectionTimeoutMS'] == 5000
                    assert kwargs['connectTimeoutMS'] == 5000
                    assert kwargs['socketTimeoutMS'] == 5000
                
        except Exception as e:
            pytest.fail(f"Connection timeout test failed: {e}")