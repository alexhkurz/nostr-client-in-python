import asyncio
import websockets
import json

class NostrClient:
    def __init__(self, relay_url):
        self.relay_url = relay_url

    async def connect(self):
        async with websockets.connect(self.relay_url) as websocket:
            await self.send_message(websocket, "Hello, Nostr!")
            response = await websocket.recv()
            print(f"Received: {response}")

    async def send_message(self, websocket, message):
        event = {
            "type": "EVENT",
            "content": message
        }
        await websocket.send(json.dumps(event))

if __name__ == "__main__":
    relay_url = "wss://relay.example.com"
    client = NostrClient(relay_url)
    asyncio.run(client.connect())
