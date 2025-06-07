import logging
from typing import List, Dict, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings

logger = logging.getLogger(__name__)

class FlashcardDatabase:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB cluster."""
        try:
            # Build MongoDB connection string
            connection_string = (
                f"mongodb+srv://{settings.mongodb_username}:{settings.mongodb_password}@"
                f"{settings.mongodb_cluster_url}/?retryWrites=true&w=majority"
            )
            
            # Connect to MongoDB
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test the connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client[settings.mongodb_database]
            self.collection = self.db.dev
            
            logger.info(f"Successfully connected to MongoDB: {settings.mongodb_cluster_url}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    def get_flashcards(self, limit: Optional[int] = None) -> List[Dict]:
        """Retrieve flashcards from the database."""
        try:
            cursor = self.collection.find({})
            
            if limit:
                cursor = cursor.limit(limit)
            
            flashcards = list(cursor)
            
            # Convert ObjectId to string and format for the bot
            formatted_flashcards = []
            for card in flashcards:
                # Convert MongoDB document to (question, answer) tuple format
                question = card.get('question', 'No question')
                answer = card.get('answer', 'No answer')
                formatted_flashcards.append((question, answer))
            
            logger.info(f"Retrieved {len(formatted_flashcards)} flashcards from database")
            return formatted_flashcards
            
        except Exception as e:
            logger.error(f"Error retrieving flashcards: {e}")
            return []
    
    def add_flashcard(self, question: str, answer: str, metadata: Optional[Dict] = None) -> bool:
        """Add a new flashcard to the database."""
        try:
            flashcard_doc = {
                'question': question,
                'answer': answer,
                'created_at': None,  # Will be set by MongoDB if using default
            }
            
            if metadata:
                flashcard_doc.update(metadata)
            
            result = self.collection.insert_one(flashcard_doc)
            
            if result.inserted_id:
                logger.info(f"Added flashcard with ID: {result.inserted_id}")
                return True
            else:
                logger.error("Failed to add flashcard")
                return False
                
        except Exception as e:
            logger.error(f"Error adding flashcard: {e}")
            return False
    
    def get_flashcard_count(self) -> int:
        """Get the total number of flashcards in the database."""
        try:
            count = self.collection.count_documents({})
            logger.info(f"Total flashcards in database: {count}")
            return count
        except Exception as e:
            logger.error(f"Error counting flashcards: {e}")
            return 0
    
    def close_connection(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global database instance
flashcard_db = FlashcardDatabase()