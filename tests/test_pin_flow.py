def test_pin_flow(client):
    r = client.post("/channels/alpha-general/messages", json={"content": "pin test message"})
    assert r.status_code == 200
    msg_id = r.json()["id"]

    r = client.patch(f"/messages/{msg_id}/pin")
    assert r.status_code == 200
    assert r.json()["pinned"] is True

    r = client.get("/channels/alpha-general/pins")
    assert r.status_code == 200
    assert any(m["id"] == msg_id for m in r.json())

    r = client.patch(f"/messages/{msg_id}/pin")
    assert r.status_code == 200
    assert r.json()["pinned"] is False

    r = client.get("/channels/alpha-general/pins")
    assert not any(m["id"] == msg_id for m in r.json())

    client.delete(f"/messages/{msg_id}")
