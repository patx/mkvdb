# tests/test_mkvdb.py

import os
import uuid

import pytest
import pytest_asyncio

from mongokv import Mkv

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")


# ---------- Fixtures ----------

@pytest_asyncio.fixture
async def mkv():
    collection_name = f"test_kv_{uuid.uuid4().hex}"
    db = Mkv(MONGO_URI, db_name="test_mkvdb", collection_name=collection_name)

    try:
        await db.db.command("ping")
    except Exception:
        pytest.skip(f"MongoDB not available at {MONGO_URI}")

    await db.purge()

    try:
        yield db
    finally:
        # Best-effort cleanup; don't let errors fail the test
        try:
            await db.purge()
        except Exception:
            pass
        try:
            await db.close()
        except Exception:
            pass


@pytest.fixture
def mkv_sync():
    collection_name = f"test_kv_sync_{uuid.uuid4().hex}"
    db = Mkv(MONGO_URI, db_name="test_mkvdb", collection_name=collection_name)

    try:
        db.purge()
    except Exception:
        pass

    try:
        yield db
    finally:
        try:
            db.purge()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass


# ---------- Async tests ----------

@pytest.mark.asyncio
async def test_set_and_get_value_async(mkv: Mkv):
    await mkv.set("foo", "bar")
    value = await mkv.get("foo")
    assert value == "bar"


@pytest.mark.asyncio
async def test_get_missing_returns_default_async(mkv: Mkv):
    value = await mkv.get("missing", default=123)
    assert value == 123


@pytest.mark.asyncio
async def test_get_missing_default_none_async(mkv: Mkv):
    with pytest.raises(KeyError):
        await mkv.get("missing")


@pytest.mark.asyncio
async def test_overwrite_existing_key_async(mkv: Mkv):
    await mkv.set("counter", 1)
    await mkv.set("counter", 2)
    value = await mkv.get("counter")
    assert value == 2


@pytest.mark.asyncio
async def test_remove_existing_key_async(mkv: Mkv):
    await mkv.set("temp", "value")
    removed = await mkv.remove("temp")
    assert removed is True

    # Confirm it’s gone
    with pytest.raises(KeyError):
        await mkv.get("temp")


@pytest.mark.asyncio
async def test_remove_missing_key_returns_false_async(mkv: Mkv):
    removed = await mkv.remove("does-not-exist")
    assert removed is False


@pytest.mark.asyncio
async def test_all_returns_all_keys_async(mkv: Mkv):
    await mkv.set("k1", "v1")
    await mkv.set("k2", "v2")
    await mkv.set("k3", "v3")

    keys = await mkv.all()
    # Order is not guaranteed, so assert as a set
    assert set(keys) == {"k1", "k2", "k3"}


@pytest.mark.asyncio
async def test_all_on_empty_db_returns_empty_list_async(mkv: Mkv):
    keys = await mkv.all()
    assert keys == []


@pytest.mark.asyncio
async def test_purge_clears_all_keys_async(mkv: Mkv):
    await mkv.set("a", 1)
    await mkv.set("b", 2)

    keys_before = await mkv.all()
    assert set(keys_before) == {"a", "b"}

    result = await mkv.purge()
    assert result is True

    keys_after = await mkv.all()
    assert keys_after == []


@pytest.mark.asyncio
async def test_non_string_keys_are_cast_to_str_async(mkv: Mkv):
    await mkv.set(123, "number")
    await mkv.set(("tuple", 1), "tuple-value")

    # We expect them to be stored under str(key)
    keys = await mkv.all()
    assert set(keys) == {"123", "('tuple', 1)"}

    assert await mkv.get(123) == "number"
    assert await mkv.get(("tuple", 1)) == "tuple-value"


@pytest.mark.asyncio
async def test_close_does_not_throw_async(mkv: Mkv):
    # The fixture already closes in teardown, but we can call it early too.
    await mkv.set("k", "v")
    await mkv.close()  # Should not raise
    # Don't assert behavior after close (Motor generally allows it but it's not required)


@pytest.mark.asyncio
async def test_get_missing_default_none_explicit_async(mkv: Mkv):
    value = await mkv.get("missing", default=None)
    assert value is None


@pytest.mark.asyncio
async def test_get_missing_raises_keyerror_async(mkv: Mkv):
    with pytest.raises(KeyError):
        await mkv.get("missing")
        
        
# ---------- Sync tests (dualmethod behavior) ----------

def test_sync_get_missing_raises_keyerror(mkv_sync: Mkv):
    with pytest.raises(KeyError):
        mkv_sync.get("missing")

def test_sync_get_missing_default_none_explicit(mkv_sync: Mkv):
    value = mkv_sync.get("missing", default=None)
    assert value is None
    

def test_sync_set_and_get(mkv_sync: Mkv):
    mkv_sync.set("foo", "bar")
    value = mkv_sync.get("foo")
    assert value == "bar"


def test_sync_get_missing_returns_default(mkv_sync: Mkv):
    value = mkv_sync.get("nope", default="fallback")
    assert value == "fallback"


def test_sync_remove_and_purge(mkv_sync: Mkv):
    mkv_sync.set("a", 1)
    mkv_sync.set("b", 2)

    removed = mkv_sync.remove("a")
    assert removed is True

    with pytest.raises(KeyError):
        mkv_sync.get("a")

    assert mkv_sync.get("b") == 2

    purged = mkv_sync.purge()
    assert purged is True
    assert mkv_sync.all() == []


def test_sync_non_string_keys_cast_to_str(mkv_sync: Mkv):
    mkv_sync.set(10, "ten")
    mkv_sync.set(("x", "y"), {"ok": True})

    keys = mkv_sync.all()
    assert set(keys) == {"10", "('x', 'y')"}

    assert mkv_sync.get(10) == "ten"
    assert mkv_sync.get(("x", "y")) == {"ok": True}


def test_sync_close_does_not_raise(mkv_sync: Mkv):
    mkv_sync.set("k", "v")
    mkv_sync.close()  # Should not raise

