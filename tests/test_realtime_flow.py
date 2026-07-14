import asyncio
import json

import httpx
import websockets


def test_realtime_flow():
    async def _run():
        ws_url = "ws://localhost:8001/ws?channel_id=alpha-general&user_id=demo-org-a"
        async with websockets.connect(ws_url) as ws:
            async with httpx.AsyncClient(
                base_url="http://localhost:8001/api/v1",
                headers={"x-user-id": "demo-org-a"},
                timeout=10.0,
            ) as ac:
                r = await ac.post("/channels/alpha-general/messages", json={"content": "realtime test"})
                assert r.status_code == 200
                msg_id = r.json()["id"]

            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
            event = json.loads(raw)

            assert event["event"] == "message.new"
            assert event["channel_id"] == "alpha-general"
            assert event["data"]["content"] == "realtime test"

            async with httpx.AsyncClient(
                base_url="http://localhost:8001/api/v1",
                headers={"x-user-id": "demo-org-a"},
                timeout=10.0,
            ) as ac:
                await ac.delete(f"/messages/{msg_id}")

    asyncio.run(_run())
