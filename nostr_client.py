import asyncio
import websockets
import json

class NostrClient:
    def __init__(self, relay_url):
        self.relay_url = relay_url

    async def connect(self):
        try:
            async with websockets.connect(self.relay_url) as websocket:
                await self.send_message(websocket, "Hello, Nostr!")
                response = await websocket.recv()
                print(f"Received: {response}")
        except Exception as e:
            print(f"Failed to connect to {self.relay_url}: {e}")
            print("Please check if the relay URL is correct and reachable.")

    async def send_message(self, websocket, message):
        event = {
            "type": "EVENT",
            "content": message
        }
        await websocket.send(json.dumps(event))

    async def fetch_relays(self):
        # In a real-world scenario, this list might be fetched from a trusted source or configuration file.
        return [
            "wss://relay.example.com",
            "wss://another-relay.example.com"
        ]
async def main():
    client = NostrClient("")
    relays = await client.fetch_relays()
    for relay in relays:
        client.relay_url = relay
        try:
            await client.connect()
            break  # Stop after the first successful connection
        except Exception as e:
            print(f"Failed to connect to {relay}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
