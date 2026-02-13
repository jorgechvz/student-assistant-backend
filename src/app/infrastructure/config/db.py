"""MongoDB Database Configuration"""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.domain.db.models import (
    UserModel,
    NotionTokenModel,
    GoogleTokenModel,
    CanvasTokenModel,
    ChatSessionModel,
    MessageModel,
)


class Database:
    """MongoDB Database Connection"""

    client: AsyncIOMotorClient = None

    @classmethod
    async def connect_db(cls, mongodb_uri: str, db_name: str):
        """Connect to MongoDB"""
        cls.client = AsyncIOMotorClient(mongodb_uri)

        await init_beanie(
            database=cls.client[db_name],
            document_models=[
                UserModel,
                NotionTokenModel,
                GoogleTokenModel,
                CanvasTokenModel,
                ChatSessionModel,
                MessageModel,
            ],
        )
        print("✅ Connected to MongoDB")

    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("❌ Disconnected from MongoDB")


async def get_database():
    """Get MongoDB client"""
    return Database.client
