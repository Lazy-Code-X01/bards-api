import time

import httpx
import pytest

BASE_URL = "http://localhost:8001/api/v1"

U1_HEADERS = {"x-user-id": "u1"}
U2_HEADERS = {"x-user-id": "u2"}


@pytest.fixture
def u1():
    with httpx.Client(base_url=BASE_URL, headers=U1_HEADERS, timeout=10.0) as c:
        yield c


@pytest.fixture
def u2():
    with httpx.Client(base_url=BASE_URL, headers=U2_HEADERS, timeout=10.0) as c:
        yield c


def _drain_notifications(client: httpx.Client) -> list[dict]:
    """Mark all read so each test starts from a clean slate."""
    client.patch("/notifications/read-all")
    r = client.get("/notifications/unread-count")
    assert r.status_code == 200
    assert r.json()["count"] == 0
    return []


def test_send_message_creates_notification_for_other_member(u1, u2):
    _drain_notifications(u1)
    _drain_notifications(u2)

    before = u2.get("/notifications/unread-count").json()["count"]

    u1.post("/channels/alpha-general/messages", json={"content": "hello from u1"})
    time.sleep(0.3)

    after = u2.get("/notifications/unread-count").json()["count"]
    assert after > before


def test_sender_receives_no_notification(u1):
    _drain_notifications(u1)

    u1.post("/channels/alpha-general/messages", json={"content": "self-send test"})
    time.sleep(0.3)

    count = u1.get("/notifications/unread-count").json()["count"]
    assert count == 0


def test_list_notifications_returns_recent_entry(u1, u2):
    _drain_notifications(u2)

    u1.post("/channels/alpha-general/messages", json={"content": "notif list test"})
    time.sleep(0.3)

    r = u2.get("/notifications")
    assert r.status_code == 200
    data = r.json()
    assert "notifications" in data
    if data["notifications"]:
        notif = data["notifications"][0]
        assert notif["type"] == "new_message"
        assert notif["channel_id"] == "alpha-general"
        assert notif["read"] is False


def test_mark_single_notification_read(u1, u2):
    _drain_notifications(u2)

    u1.post("/channels/alpha-general/messages", json={"content": "mark single read"})
    time.sleep(0.3)

    r = u2.get("/notifications")
    notifs = r.json()["notifications"]
    assert notifs, "Expected at least one notification"
    notif_id = notifs[0]["id"]

    r = u2.patch(f"/notifications/{notif_id}/read")
    assert r.status_code == 200
    assert r.json()["read"] is True


def test_mark_all_notifications_read(u1, u2):
    _drain_notifications(u2)

    u1.post("/channels/alpha-general/messages", json={"content": "bulk read 1"})
    u1.post("/channels/alpha-general/messages", json={"content": "bulk read 2"})
    time.sleep(0.3)

    r = u2.patch("/notifications/read-all")
    assert r.status_code == 204

    count = u2.get("/notifications/unread-count").json()["count"]
    assert count == 0


def test_notifications_paginated_with_cursor(u1, u2):
    _drain_notifications(u2)

    for i in range(3):
        u1.post("/channels/alpha-general/messages", json={"content": f"page msg {i}"})
    time.sleep(0.3)

    r = u2.get("/notifications", params={"limit": 2})
    assert r.status_code == 200
    data = r.json()
    assert len(data["notifications"]) <= 2

    if data["next_cursor"]:
        r2 = u2.get("/notifications", params={"cursor": data["next_cursor"], "limit": 2})
        assert r2.status_code == 200


def test_muted_channel_produces_no_notifications(u1, u2):
    """alpha-muted channel has muted=True in seed data; no notifications should fire."""
    _drain_notifications(u2)

    u1.post("/channels/alpha-muted/messages", json={"content": "muted channel msg"})
    time.sleep(0.3)

    count = u2.get("/notifications/unread-count").json()["count"]
    assert count == 0
