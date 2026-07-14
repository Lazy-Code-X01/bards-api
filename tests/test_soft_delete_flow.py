def test_soft_delete_flow(client):
    r = client.post("/channels/alpha-general/messages", json={"content": "delete me"})
    assert r.status_code == 200
    msg_id = r.json()["id"]

    r = client.get("/channels/alpha-general/messages")
    assert any(m["id"] == msg_id for m in r.json()["messages"])

    r = client.delete(f"/messages/{msg_id}")
    assert r.status_code == 204

    r = client.get("/channels/alpha-general/messages")
    assert not any(m["id"] == msg_id for m in r.json()["messages"])
