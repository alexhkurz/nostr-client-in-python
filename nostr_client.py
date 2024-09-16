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

    async def fetch_relays(self) -> List[str]:
        # This list could come from a config file or external source
        potential_relays = [
            "wss://relay.damus.io",
            "wss://relay.nostr.bg",
            "wss://nostr-pub.wellorder.net",
            "wss://relay.nostr.info",
            # Add more relay URLs here
        ]
        
        alive_relays = []
        for relay in potential_relays:
            if await self.check_relay(relay):
                print(f"✅ Relay alive: {relay}")
                alive_relays.append(relay)
            else:
                print(f"❌ Relay dead: {relay}")
        
        self.relays = alive_relays
        return self.relays

async def main():
    client = NostrClient()
    print("Checking relays...")
    alive_relays = await client.fetch_relays()
    print(f"\nSummary:")
    print(f"Total relays checked: {len(potential_relays)}")
    print(f"Alive relays: {len(alive_relays)}")
    print(f"Dead relays: {len(potential_relays) - len(alive_relays)}")
    
    # Attempt to connect to the first alive relay
    if alive_relays:
        print(f"\nAttempting to connect to: {alive_relays[0]}")
        await client.connect(alive_relays[0])
    else:
        print("\nNo alive relays found.")

if __name__ == "__main__":
    asyncio.run(main())
