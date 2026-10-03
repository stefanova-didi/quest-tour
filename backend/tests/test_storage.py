import pytest

from questtour.storage import BlobExists, LocalBlobStore


@pytest.fixture
def store(tmp_path):
    s = LocalBlobStore(tmp_path)
    s.ensure_container("photos")
    return s


def test_put_then_get_round_trips_bytes_and_content_type(store):
    store.put("photos", "a.jpg", b"data", "image/jpeg", overwrite=False)
    assert store.get("photos", "a.jpg") == (b"data", "image/jpeg")


def test_second_put_without_overwrite_raises(store):
    store.put("photos", "a.jpg", b"one", "image/jpeg", overwrite=False)
    with pytest.raises(BlobExists):
        store.put("photos", "a.jpg", b"two", "image/jpeg", overwrite=False)
    assert store.get("photos", "a.jpg") == (b"one", "image/jpeg")


def test_put_with_overwrite_replaces(store):
    store.put("photos", "a.jpg", b"one", "image/jpeg", overwrite=False)
    store.put("photos", "a.jpg", b"two", "image/png", overwrite=True)
    assert store.get("photos", "a.jpg") == (b"two", "image/png")


def test_exists_reflects_state(store):
    assert not store.exists("photos", "a.jpg")
    store.put("photos", "a.jpg", b"x", "image/jpeg", overwrite=False)
    assert store.exists("photos", "a.jpg")


def test_get_missing_returns_none(store):
    assert store.get("photos", "nope.jpg") is None


def test_nested_names_work(store):
    store.put("photos", "a/b/c.jpg", b"deep", "image/jpeg", overwrite=False)
    assert store.exists("photos", "a/b/c.jpg")
    assert store.get("photos", "a/b/c.jpg") == (b"deep", "image/jpeg")
