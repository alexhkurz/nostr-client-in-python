from typing import List
import asyncio
import websockets
import json
import time
import uuid
import base64
import datetime
import pytz

class NostrClient:
    def __init__(self):
        self.potential_relays = [
            "wss://relay.damus.io",
            "wss://relay.nostr.bg",
            "wss://nostr-pub.wellorder.net",
            "wss://relay.nostr.info"
            # Add any other relays you want to check
        ]
        self.relay_url = "dummy_url" # Current relay URL

    async def connect(self):
        try:
            async with websockets.connect(self.relay_url) as websocket:
                # Send a request for the most recent event
                request_id = str(uuid.uuid4())
                request = ["REQ", request_id, {"kinds": [1], "limit": 1}]
                await websocket.send(json.dumps(request))
                print(f"Sent: {json.dumps(request)}")

                full_event = None
                while True:
                    response = await websocket.recv()
                    print(f"Received: {response[:100]}...")  # Print first 100 chars

                    if response.startswith('["EVENT",'):
                        event_data = json.loads(response)
                        if full_event is None:
                            full_event = event_data
                        else:
                            full_event[2]['content'] += event_data[2]['content']
                    elif response.startswith('["EOSE",'):
                        break

                if full_event:
                    print("\nReassembled event:")
                    event_content = full_event[2]['content']
                    try:
                        decoded_content = base64.b64decode(event_content.split('://', 1)[1]).decode('utf-8')
                        print(f"Decoded content: {decoded_content}")
                    except:
                        print(f"Raw content: {event_content}")
                    print(f"Event ID: {full_event[2]['id']}")
                    print(f"Event kind: {full_event[2]['kind']}")
                    print(f"Event pubkey: {full_event[2]['pubkey']}")

        except Exception as e:
            print(f"Failed to connect to {self.relay_url}: {e}")
            print("Please check if the relay URL is correct and reachable.")

    async def send_message(self, message):
        async with websockets.connect(self.relay_url) as websocket:
            event = {
                "type": "EVENT",
                "content": message
            }
            await websocket.send(json.dumps(event))
            print(f"Message sent: {message}")

    async def read_messages(self):
        async with websockets.connect(self.relay_url) as websocket:
            request_id = str(uuid.uuid4())
            request = ["REQ", request_id, {"kinds": [1], "limit": 10}]
            await websocket.send(json.dumps(request))
            print(f"Sent: {json.dumps(request)}")

            messages = []
            while True:
                response = await websocket.recv()
                print(f"Received: {response[:100]}...")  # Print first 100 chars

                if response.startswith('["EVENT",'):
                    event_data = json.loads(response)
                    created_at = event_data[2].get('created_at', int(time.time()))
                    if 'created_at' in event_data[2]:
                        created_at = event_data[2]['created_at']
                        messages.append({
                            'content': event_data[2]['content'],
                            'pubkey': event_data[2]['pubkey'],
                            'relay': self.relay_url,
                            'created_at': created_at
                        })
                    else:
                        received_at = int(time.time())
                        messages.append({
                            'content': event_data[2]['content'],
                            'pubkey': event_data[2]['pubkey'],
                            'relay': self.relay_url,
                            'received_at': received_at
                        })
                elif response.startswith('["EOSE",'):
                    break

            # Append new messages to a file without relay information
            with open('seen_messages.txt', 'a') as f:
                for message in messages:
                    f.write(f"{message['pubkey']}: {message['content']} (created_at: {message['created_at']})\n")

            return messages

    async def check_relay(self, relay):
        try:
            async with asyncio.timeout(5):  # 5 second timeout
                async with websockets.connect(relay) as ws:
                    await ws.send('["REQ", "test", {"kinds":[0],"limit":1}]')
                    response = await ws.recv()
                    return "EOSE" in response or "EVENT" in response
        except Exception:
            return False

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

def unix_to_pst(unix_time):
    utc_time = datetime.datetime.utcfromtimestamp(unix_time)
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    pst_time = utc_time.astimezone(pytz.timezone('America/Los_Angeles'))
    return pst_time.strftime('%Y-%m-%d %H:%M:%S %Z')

async def main():
    client = NostrClient()
    print("Checking relays...")
    alive_relays = await client.fetch_relays()
    print(f"\nSummary:")
    print(f"Total relays checked: {len(client.potential_relays)}")
    print(f"Alive relays: {len(alive_relays)}")
    print(f"Dead relays: {len(client.potential_relays) - len(alive_relays)}")
    
    if alive_relays:
        client.relay_url = alive_relays[0]  # Update the relay_url to the first alive relay
        print(f"Connected to relay: {client.relay_url}")  # Output the current relay URL
    else:
        print("No alive relays found. Exiting.")
        return

    while True:
        print("\nOptions:")
        print("1. Post a message")
        print("2. Read messages")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            message = input("Enter your message: ")
            await client.send_message(message)
        elif choice == "2":
            messages = await client.read_messages()
            print("\nMessages:")
            for msg in messages:
                print(f"- {msg}")
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
