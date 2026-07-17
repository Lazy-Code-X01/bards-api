import httpx

BASE_URL = "http://localhost:8001/api/v1"


def test_wrong_org_header_rejected():
    """Valid user + wrong x-organization-id must return 403, not 200 or 404."""
    with httpx.Client(
        base_url=BASE_URL,
        headers={"x-user-id": "u1", "x-organization-id": "org-beta"},
        timeout=10.0,
    ) as c:
        r = c.get("/channels")
        assert r.status_code == 403
        assert r.json()["detail"] == "Invalid user/organization pair"


def test_org_a_sees_own_channels(client):
    r = client.get("/channels")
    assert r.status_code == 200
    all_ids = (
        [ch["id"] for ch in r.json()["team"]]
        + [ch["id"] for ch in r.json()["system"]]
        + [ch["id"] for ch in r.json()["envoy"]]
        + [ch["id"] for ch in r.json()["dms"]]
    )
    assert any(cid.startswith("alpha-") for cid in all_ids)
    assert not any(cid.startswith("beta-") for cid in all_ids)


def test_org_b_sees_own_channels(org_b_client):
    r = org_b_client.get("/channels")
    assert r.status_code == 200
    all_ids = (
        [ch["id"] for ch in r.json()["team"]]
        + [ch["id"] for ch in r.json()["system"]]
        + [ch["id"] for ch in r.json()["dms"]]
    )
    assert any(cid.startswith("beta-") for cid in all_ids)
    assert not any(cid.startswith("alpha-") for cid in all_ids)


def test_org_a_blocked_from_beta_channel(client):
    r = client.get("/channels/beta-general/messages")
    assert r.status_code == 404


def test_org_b_blocked_from_alpha_channel(org_b_client):
    r = org_b_client.get("/channels/alpha-general/messages")
    assert r.status_code == 404


def test_org_a_cannot_post_to_beta_channel(client):
    r = client.post("/channels/beta-general/messages", json={"content": "cross-org attempt"})
    assert r.status_code == 404


def test_org_b_cannot_post_to_alpha_channel(org_b_client):
    r = org_b_client.post("/channels/alpha-general/messages", json={"content": "cross-org attempt"})
    assert r.status_code == 404


def test_org_a_users_scoped_to_org(client):
    r = client.get("/users")
    assert r.status_code == 200
    ids = [u["id"] for u in r.json()]
    assert "demo-org-b" not in ids
    assert "demo-org-a" in ids


def test_org_b_users_scoped_to_org(org_b_client):
    r = org_b_client.get("/users")
    assert r.status_code == 200
    ids = [u["id"] for u in r.json()]
    assert "demo-org-a" not in ids
    assert "demo-org-b" in ids


def test_cross_org_message_access_blocked(client, org_b_client):
    r = org_b_client.post("/channels/beta-general/messages", json={"content": "beta message"})
    assert r.status_code == 200
    msg_id = r.json()["id"]

    r = client.post(f"/messages/{msg_id}/reactions", json={"emoji": "👍"})
    assert r.status_code == 404

    org_b_client.delete(f"/messages/{msg_id}")
