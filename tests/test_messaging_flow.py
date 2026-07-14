from urllib.parse import quote


def test_messaging_flow(client):
    r = client.get("/channels")
    assert r.status_code == 200
    data = r.json()
    assert any(ch["id"] == "alpha-general" for ch in data["team"])

    r = client.post("/channels/alpha-general/messages", json={"content": "e2e test message"})
    assert r.status_code == 200
    msg = r.json()
    msg_id = msg["id"]
    assert msg["content"] == "e2e test message"
    assert msg["sender"]["id"] == "demo-org-a"

    r = client.get("/channels/alpha-general/messages")
    assert r.status_code == 200
    assert any(m["id"] == msg_id for m in r.json()["messages"])

    r = client.post(f"/messages/{msg_id}/reactions", json={"emoji": "🔥"})
    assert r.status_code == 200
    fire = next((rx for rx in r.json() if rx["emoji"] == "🔥"), None)
    assert fire is not None
    assert fire["count"] == 1
    assert fire["reacted"] is True

    r = client.get("/channels/alpha-general/messages")
    msg_data = next(m for m in r.json()["messages"] if m["id"] == msg_id)
    assert any(rx["emoji"] == "🔥" for rx in msg_data["reactions"])

    r = client.delete(f"/messages/{msg_id}/reactions/{quote('🔥')}")
    assert r.status_code == 200
    assert not any(rx["emoji"] == "🔥" for rx in r.json())

    client.delete(f"/messages/{msg_id}")
