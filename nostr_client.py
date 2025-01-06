from typing import List
import asyncio
import json
import websockets
import json
import time
import uuid
import base64
import datetime
import pytz
import hashlib
import hmac
from ecdsa import SigningKey, SECP256k1
from secp256k1 import PrivateKey
import logging

# Set up logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger('nostr')

# Define the configuration file name as a constant
CONFIG_FILE_NAME = 'config.json'

class NostrClient:
    def __init__(self, relay_url, private_key, public_key):
        self.relay_url = relay_url
        self.private_key = private_key
        self.public_key = public_key
        self.potential_relays = [
            "wss://relay.damus.io",
            "wss://relay.nostr.bg",
            "wss://nostr-pub.wellorder.net",
            "wss://relay.nostr.info"
            # Add any other relays you want to check
        ]

    def sign_event(self, event):
        # Convert the private key from hex to bytes
        private_key_bytes = bytes.fromhex(self.private_key)
        signing_key = PrivateKey(private_key_bytes)
        
        # Create the event hash
        event_hash = bytes.fromhex(event["id"])
        
        # Sign using Schnorr
        sig = signing_key.schnorr_sign(event_hash, None, raw=True)
        return sig.hex()

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
        created_at = int(time.time())
        event = {
            "pubkey": self.public_key,
            "created_at": created_at,
            "kind": 1,
            "tags": [],
            "content": message,
            "sig": ""  # Will be calculated
        }

        # Calculate the event ID first (without the sig field)
        serialized = json.dumps([
            0,  # Reserved for future use
            event["pubkey"],
            event["created_at"],
            event["kind"],
            event["tags"],
            event["content"]
        ], separators=(',', ':'))
        
        event_id = hashlib.sha256(serialized.encode()).hexdigest()
        event["id"] = event_id
        event["sig"] = self.sign_event(event)

        # Prepare the message according to NIP-01
        message_array = ["EVENT", event]

        print(f"Public key in event: {event['pubkey']} (length: {len(event['pubkey'])})")
        print(f"Event data before sending: {json.dumps(event, indent=2)}")

        try:
            async with websockets.connect(self.relay_url) as websocket:
                await websocket.send(json.dumps(message_array))
                print(f"Message sent: {message}")

                # Wait for acknowledgment
                try:
                    response = await websocket.recv()
                    print(f"Server response: {response}")
                except asyncio.TimeoutError:
                    print("No acknowledgment received from server.")
        except Exception as e:
            print(f"An error occurred: {e}")

    async def read_messages(self):
        logger.info("Fetching recent messages...")
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
                        received_at = unix_to_pst(int(time.time()))
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

            print("\nMessages:")
            for msg in messages:
                is_my_message = msg['pubkey'] == self.public_key
                prefix = "🟢 (YOU)" if is_my_message else "-"
                print(f"{prefix} {msg['content']}")
                print(f"   From: {msg['pubkey'][:8]}...{msg['pubkey'][-8:]}")
                print(f"   Time: {unix_to_pst(msg['created_at'])}\n")

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
    try:
        # Load keys from config.json
        with open(CONFIG_FILE_NAME, 'r') as config_file:
            config = json.load(config_file)
        
        private_key = config['private_key']
        public_key = config['public_key']

        print(f"Loaded public key: {public_key} (length: {len(public_key)})")
        if len(public_key) != 66:
            print("Warning: Public key length is not 66 characters. Please check the key format.")
        client = NostrClient(relay_url=None, private_key=private_key, public_key=public_key)
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
            try:
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
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("\nClosing Nostr client...")

if __name__ == "__main__":
    asyncio.run(main())
