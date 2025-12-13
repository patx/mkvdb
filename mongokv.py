"""
mongoKV - https://patx.github.io/mongokv
Harrison Erd - https://harrisonerd.com/
Licensed - BSD 3 Clause (see LICENSE)
"""

import asyncio
from typing import Any

from pymongo import MongoClient, AsyncMongoClient
from bson import ObjectId


MISSING = object()


def in_async() -> bool:
    """Return True if we're currently running inside an event loop."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


class Mkv:
    """
    A unified async/sync key-value store backed by MongoDB (PyMongo).
    AsyncMongoClient for async paths - MongoClient for sync paths
    Each key is stored as a document:
        { "_id": <str(key)>, "value": <BSON-serializable Python object> }
    """

    def __init__(self, mongo_uri: str, db_name: str = "mkv",
                 collection_name: str = "kv") -> None:
        self._async_client = AsyncMongoClient(mongo_uri)
        self.db = self._async_client[db_name]
        self.collection = self.db[collection_name]
        self._sync_client = MongoClient(mongo_uri)
        self._sync_db = self._sync_client[db_name]
        self._sync_collection = self._sync_db[collection_name]

    def set(self, key: str | None, value: Any) -> str:
        """Set a key-value pair."""
        if in_async():
            async def _aset() -> str:
                if key is None:
                    new_id = str(ObjectId())
                    await self.collection.insert_one({"_id": new_id,
                        "value": value})
                    return new_id
                await self.collection.update_one({"_id": str(key)},
                    {"$set": {"value": value}}, upsert=True,)
                return str(key)
            return _aset()
        if key is None:
            new_id = str(ObjectId())
            self._sync_collection.insert_one({"_id": new_id, "value": value})
            return new_id
        self._sync_collection.update_one({"_id": str(key)},
            {"$set": {"value": value}},upsert=True,)
        return str(key)

    def get(self, key: str, default: Any = MISSING) -> Any:
        """Get the value for a key."""
        if in_async():
            async def _aget() -> Any:
                doc = await self.collection.find_one({"_id": str(key)})
                if doc is None:
                    if default is MISSING:
                        raise KeyError(key)
                    return default
                return doc.get("value")
            return _aget()
        doc = self._sync_collection.find_one({"_id": str(key)})
        if doc is None:
            if default is MISSING:
                raise KeyError(key)
            return default
        return doc.get("value")

    def remove(self, key: str) -> bool:
        """
        Remove a key-value pair."""
        if in_async():
            async def _aremove() -> bool:
                result = await self.collection.delete_one({"_id": str(key)})
                return result.deleted_count > 0
            return _aremove()
        result = self._sync_collection.delete_one({"_id": str(key)})
        return result.deleted_count > 0

    def all(self) -> list[str]:
        """Return a list of all keys in the database."""
        if in_async():
            async def _aall() -> list[str]:
                keys: list[str] = []
                cursor = self.collection.find({}, {"_id": 1})
                async for doc in cursor:
                    keys.append(doc["_id"])
                return keys
            return _aall()
        keys: list[str] = []
        for doc in self._sync_collection.find({}, {"_id": 1}):
            keys.append(doc["_id"])
        return keys

    def purge(self) -> bool:
        """Remove all key-value pairs from the database."""
        if in_async():
            async def _apurge() -> bool:
                await self.collection.delete_many({})
                return True
            return _apurge()
        self._sync_collection.delete_many({})
        return True

    def close(self) -> None:
        """Close the underlying MongoDB clients."""
        if in_async():
            async def _aclose() -> None:
                await self._async_client.close()
                self._sync_client.close()
            return _aclose()
        asyncio.run(self._async_client.close())
        self._sync_client.close()

