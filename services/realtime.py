from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channel_id: str):
        await ws.accept()
        self._connections.setdefault(channel_id, []).append(ws)

    def disconnect(self, ws: WebSocket, channel_id: str):
        channel_list = self._connections.get(channel_id, [])
        if ws in channel_list:
            channel_list.remove(ws)

    async def broadcast(self, channel_id: str, event: dict):
        dead: list[tuple[str, WebSocket]] = []
        for cid, ws_list in self._connections.items():
            for ws in ws_list:
                try:
                    await ws.send_json(event)
                except Exception:
                    dead.append((cid, ws))
        for cid, ws in dead:
            self.disconnect(ws, cid)


manager = ConnectionManager()
