import logging
from typing import List, Dict, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from datetime import datetime, timedelta

from app.config import settings
from app.flashcards.models import (
    FlashcardUnion, 
    FlashcardType, 
    TwoSidedCard, 
    FillInTheBlank, 
    MultipleChoice,
    create_flashcard_from_dict
)

logger = logging.getLogger(__name__)

class FlashcardDatabaseV2:
    """Enhanced database service for the new flashcard system."""
    
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
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test the connection
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client[settings.mongodb_database]
            self.collection = self.db.dev  # New collection for v2 flashcards
            
            logger.info(f"Successfully connected to MongoDB: {settings.mongodb_cluster_url}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    def add_flashcard(self, flashcard: FlashcardUnion) -> Optional[str]:
        """Add a new flashcard to the database."""
        try:
            # Convert Pydantic model to dict
            flashcard_dict = flashcard.model_dump()
            
            # Remove the id field if it's None (let MongoDB generate it)
            if flashcard_dict.get('id') is None:
                flashcard_dict.pop('id', None)
            
            # Insert the document
            result = self.collection.insert_one(flashcard_dict)
            
            if result.inserted_id:
                logger.info(f"Added flashcard with ID: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logger.error("Failed to add flashcard")
                return None
                
        except Exception as e:
            logger.error(f"Error adding flashcard: {e}")
            return None
    
    def get_flashcards(self, 
                      flashcard_type: Optional[FlashcardType] = None,
                      tags: Optional[List[str]] = None,
                      due_before: Optional[datetime] = None,
                      limit: Optional[int] = None) -> List[FlashcardUnion]:
        """Retrieve flashcards from the database with optional filtering."""
        try:
            # Build query filter
            query_filter = {}
            
            if flashcard_type:
                query_filter["type"] = flashcard_type.value
            
            if tags:
                query_filter["tags"] = {"$in": tags}
            
            if due_before:
                query_filter["due_date"] = {"$lte": due_before}
            
            # Execute query
            cursor = self.collection.find(query_filter)
            
            if limit:
                cursor = cursor.limit(limit)
            
            # Convert documents to flashcard objects
            flashcards = []
            for doc in cursor:
                try:
                    # Convert ObjectId to string
                    doc["id"] = str(doc["_id"])
                    del doc["_id"]
                    
                    # Create flashcard object
                    flashcard = create_flashcard_from_dict(doc)
                    flashcards.append(flashcard)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse flashcard document: {e}")
                    continue
            
            logger.info(f"Retrieved {len(flashcards)} flashcards from database")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error retrieving flashcards: {e}")
            return []
    
    def get_flashcard_by_id(self, flashcard_id: str) -> Optional[FlashcardUnion]:
        """Get a specific flashcard by its ID."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(flashcard_id)})
            
            if doc:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                
                return create_flashcard_from_dict(doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving flashcard by ID: {e}")
            return None
    
    def update_flashcard(self, flashcard_id: str, updates: Dict) -> bool:
        """Update a flashcard with new data."""
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.now()
            
            result = self.collection.update_one(
                {"_id": ObjectId(flashcard_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated flashcard {flashcard_id}")
                return True
            else:
                logger.warning(f"No flashcard updated for ID: {flashcard_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating flashcard: {e}")
            return False
    
    def update_flashcard_stats(self, flashcard_id: str, is_correct: bool, new_due_date: datetime, 
                              new_interval: int, new_ease_factor: float) -> bool:
        """Update flashcard statistics after a review."""
        try:
            updates = {
                "due_date": new_due_date,
                "interval_days": new_interval,
                "ease_factor": new_ease_factor,
                "repetition_count": {"$inc": 1},
                "updated_at": datetime.now()
            }
            
            if is_correct:
                updates["times_correct"] = {"$inc": 1}
            else:
                updates["times_incorrect"] = {"$inc": 1}
            
            # Use $inc for counters and $set for other fields
            set_updates = {k: v for k, v in updates.items() if not isinstance(v, dict)}
            inc_updates = {k: v["$inc"] for k, v in updates.items() if isinstance(v, dict) and "$inc" in v}
            
            update_doc = {}
            if set_updates:
                update_doc["$set"] = set_updates
            if inc_updates:
                update_doc["$inc"] = inc_updates
            
            result = self.collection.update_one(
                {"_id": ObjectId(flashcard_id)},
                update_doc
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating flashcard stats: {e}")
            return False
    
    def delete_flashcard(self, flashcard_id: str) -> bool:
        """Delete a flashcard from the database."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(flashcard_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted flashcard {flashcard_id}")
                return True
            else:
                logger.warning(f"No flashcard deleted for ID: {flashcard_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting flashcard: {e}")
            return False
    
    def get_flashcard_count(self, flashcard_type: Optional[FlashcardType] = None) -> int:
        """Get the total number of flashcards in the database."""
        try:
            query_filter = {}
            if flashcard_type:
                query_filter["type"] = flashcard_type.value
                
            count = self.collection.count_documents(query_filter)
            logger.info(f"Total flashcards in database: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error counting flashcards: {e}")
            return 0
    
    def get_due_flashcards(self, user_id: Optional[str] = None, limit: int = 20) -> List[FlashcardUnion]:
        """Get flashcards that are due for review."""
        now = datetime.now()
        return self.get_flashcards(due_before=now, limit=limit)
    
    def get_tags(self) -> List[str]:
        """Get all unique tags used in flashcards."""
        try:
            pipeline = [
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags"}},
                {"$sort": {"_id": 1}}
            ]
            
            result = self.collection.aggregate(pipeline)
            tags = [doc["_id"] for doc in result]
            
            logger.info(f"Found {len(tags)} unique tags")
            return tags
            
        except Exception as e:
            logger.error(f"Error retrieving tags: {e}")
            return []
    
    def get_dashboard_stats(self) -> Dict[str, int]:
        """Get dashboard statistics for flashcards."""
        try:
            now = datetime.now()
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            week_end = now + timedelta(days=7)
            
            # Total flashcards
            total_count = self.get_flashcard_count()
            
            # Due today
            due_today = self.collection.count_documents({
                "due_date": {"$lte": today_end}
            })
            
            # Due this week
            due_this_week = self.collection.count_documents({
                "due_date": {"$lte": week_end}
            })
            
            # New flashcards (never reviewed)
            new_cards = self.collection.count_documents({
                "times_reviewed": 0
            })
            
            # Mastered flashcards (high ease factor and long intervals)
            mastered_cards = self.collection.count_documents({
                "ease_factor": {"$gte": 2.5},
                "interval_days": {"$gte": 30}
            })
            
            return {
                "total": total_count,
                "due_today": due_today,
                "due_this_week": due_this_week,
                "new": new_cards,
                "mastered": mastered_cards
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                "total": 0,
                "due_today": 0,
                "due_this_week": 0,
                "new": 0,
                "mastered": 0
            }
    
    def get_recent_activity_stats(self, days: int = 7) -> Dict[str, int]:
        """Get recent activity statistics."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Cards added recently
            recent_additions = self.collection.count_documents({
                "created_at": {"$gte": cutoff_date}
            })
            
            # Cards reviewed recently
            recent_reviews = self.collection.count_documents({
                "last_reviewed": {"$gte": cutoff_date}
            })
            
            return {
                "recent_additions": recent_additions,
                "recent_reviews": recent_reviews
            }
            
        except Exception as e:
            logger.error(f"Error getting recent activity stats: {e}")
            return {
                "recent_additions": 0,
                "recent_reviews": 0
            }
    
    def close_connection(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global database instance
flashcard_db_v2 = FlashcardDatabaseV2()