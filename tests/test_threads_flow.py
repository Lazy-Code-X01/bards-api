def test_threads_flow(client):
    r = client.post("/channels/alpha-general/messages", json={"content": "parent message"})
    assert r.status_code == 200
    parent_id = r.json()["id"]

    r = client.post("/channels/alpha-general/messages", json={"content": "reply message", "parent_id": parent_id})
    assert r.status_code == 200
    reply = r.json()
    assert reply["parent_id"] == parent_id

    r = client.get(f"/messages/{parent_id}/replies")
    assert r.status_code == 200
    assert any(rep["id"] == reply["id"] for rep in r.json())

    r = client.get("/channels/alpha-general/messages")
    parent_data = next((m for m in r.json()["messages"] if m["id"] == parent_id), None)
    assert parent_data is not None
    assert parent_data["reply_count"] >= 1

    client.delete(f"/messages/{reply['id']}")
    client.delete(f"/messages/{parent_id}")
