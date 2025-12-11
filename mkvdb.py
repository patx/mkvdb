"""
mkvDB - https://patx.github.io/mkvDB
Harrison Erd - https://harrisonerd.com/
Licensed - BSD 3 Clause (see LICENSE)
"""

import asyncio
from typing import Any, Optional, List

import motor.motor_asyncio


def in_async() -> bool:
    """Check if running inside an active event loop."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def dualmethod(func):
    """Allows async methods to also be called synchronously."""
    def wrapper(self, *args, **kwargs):
        coro = func(self, *args, **kwargs)
        if in_async():
            return coro
        return asyncio.run(coro)
    return wrapper


class Mkv:
    """
    A unified async/sync key-value store backed by MongoDB (Motor).
    Each key is stored as a document:
        { "_id": <str(key)>, "value": <BSON-serializable Python object> }
    """

    def __init__(self, mongo_uri: str, db_name: str = "mkv",
                 collection_name: str = "kv"):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    @dualmethod
    async def set(self, key: Any, value: Any) -> bool:
        """Set a key-value pair. Overwrites if the key already exists."""
        await self.collection.update_one(
            {"_id": str(key)}, {"$set": {"value": value}}, upsert=True)
        return True

    @dualmethod
    async def get(self, key: Any, default: Optional[Any] = None) -> Any:
        """
        Get the value for a key. Returns `default` if the key does not exist.
        """
        key_str = str(key)
        doc = await self.collection.find_one({"_id": key_str})
        if doc is None:
            return default
        return doc.get("value", default)

    @dualmethod
    async def remove(self, key: Any) -> bool:
        """
        Remove a key-value pair. Returns True if a document was 
        deleted, False otherwise.
        """
        result = await self.collection.delete_one({"_id": str(key)})
        return result.deleted_count > 0

    @dualmethod
    async def all(self) -> List[str]:
        """Return a list of all keys in the database."""
        keys: List[str] = []
        cursor = self.collection.find({}, {"_id": 1})
        async for doc in cursor:
            keys.append(doc["_id"])
        return keys

    @dualmethod
    async def purge(self) -> bool:
        """Remove all key-value pairs from the database."""
        await self.collection.delete_many({})
        return True

    @dualmethod
    async def close(self) -> None:
        """Close the underlying MongoDB client."""
        self.client.close()

