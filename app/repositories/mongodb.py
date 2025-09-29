"""
MongoDB client and repository module.
"""

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings

_mongo_client = None


def get_mongodb_client() -> MongoClient:
    """
    Get a MongoDB client instance (singleton).

    Returns:
        MongoClient: A MongoDB client instance
    """
    global _mongo_client

    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(settings.MONGODB_URI)
            # Ping the database to verify the connection
            _mongo_client.admin.command("ping")
            print(f"Connected to MongoDB: {settings.MONGODB_URI}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    return _mongo_client


def get_database() -> Database:
    """
    Get the MongoDB database instance.

    Returns:
        Database: A MongoDB database instance
    """
    client = get_mongodb_client()
    return client[settings.MONGODB_DB_NAME]


class MongoRepository:
    """Base MongoDB repository class."""

    def __init__(self, collection_name):
        """
        Initialize the repository with a collection.

        Args:
            collection_name (str): The name of the MongoDB collection
        """
        self.db = get_database()
        self.collection = self.db[collection_name]
