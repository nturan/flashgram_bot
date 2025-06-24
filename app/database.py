"""Database initialization and configuration using Beanie ODM."""

import logging
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.models.users import User
from app.models.flashcards import Flashcard
from app.models.words import Word

logger = logging.getLogger(__name__)


async def init_database():
    """Initialize the database connection and Beanie ODM."""
    try:
        # Build MongoDB connection string
        connection_string = (
            f"mongodb+srv://{settings.mongodb_username}:{settings.mongodb_password}@"
            f"{settings.mongodb_cluster_url}/?retryWrites=true&w=majority"
        )

        # Create Motor client
        client = AsyncIOMotorClient(connection_string)
        
        # Get database
        database = client[settings.mongodb_database]
        
        # Initialize Beanie with the models
        await init_beanie(
            database=database,
            document_models=[
                User,
                Flashcard,
                Word
            ]
        )
        
        logger.info(f"Successfully initialized Beanie ODM with MongoDB: {settings.mongodb_cluster_url}")
        logger.info(f"Database: {settings.mongodb_database}")
        
        return client, database
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_database(client: AsyncIOMotorClient):
    """Close the database connection."""
    if client:
        client.close()
        logger.info("Database connection closed")


# Global client instance
_client = None
_database = None


async def get_database():
    """Get the database instance, initializing if needed."""
    global _client, _database
    if _client is None or _database is None:
        _client, _database = await init_database()
    return _database


async def get_client():
    """Get the client instance, initializing if needed."""
    global _client, _database
    if _client is None or _database is None:
        _client, _database = await init_database()
    return _client