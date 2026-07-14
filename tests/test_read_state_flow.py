def test_read_state_flow(client, u1_client):
    client.post("/channels/alpha-general/read")

    r = u1_client.post("/channels/alpha-general/messages", json={"content": "message from u1"})
    assert r.status_code == 200
    msg_id = r.json()["id"]

    r = client.get("/channels")
    general = next(ch for ch in r.json()["team"] if ch["id"] == "alpha-general")
    assert general["unread"] >= 1

    r = client.post("/channels/alpha-general/read")
    assert r.status_code == 204

    r = client.get("/channels")
    general = next(ch for ch in r.json()["team"] if ch["id"] == "alpha-general")
    assert general["unread"] == 0

    u1_client.delete(f"/messages/{msg_id}")
