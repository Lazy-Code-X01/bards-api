from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._by_channel: dict[str, list[WebSocket]] = {}
        self._by_user: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channel_id: str, user_id: str):
        await ws.accept()
        self._by_channel.setdefault(channel_id, []).append(ws)
        self._by_user.setdefault(user_id, []).append(ws)

    def disconnect(self, ws: WebSocket, channel_id: str, user_id: str):
        for bucket in (self._by_channel.get(channel_id, []), self._by_user.get(user_id, [])):
            if ws in bucket:
                bucket.remove(ws)

    async def broadcast(self, channel_id: str, event: dict):
        await self._send_to(self._by_channel.get(channel_id, []), event)

    async def broadcast_to_user(self, user_id: str, event: dict):
        await self._send_to(self._by_user.get(user_id, []), event)

    async def _send_to(self, ws_list: list[WebSocket], event: dict):
        dead: list[WebSocket] = []
        for ws in ws_list:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            ws_list.remove(ws)


manager = ConnectionManager()
