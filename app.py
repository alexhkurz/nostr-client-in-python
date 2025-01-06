import time
import json
from flask import Flask, render_template, request, redirect, url_for
import asyncio
import click
from nostr_client import NostrClient, unix_to_pst
from generate_keys import generate_key_pair, save_keys_to_config
import logging
from langdetect import detect, LangDetectException

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nostr.log'),  # Log to this file
        logging.StreamHandler()            # Log to console
    ]
)

logger = logging.getLogger('nostr')

app = Flask(__name__)

@app.route('/')
def index():
    # Get filter preference from query parameter
    filter_languages = request.args.get('filter_languages', 'false') == 'true'
    
    # Get messages (reuse code from read_messages)
    messages = get_messages(filter_languages)
    
    return render_template('index.html', 
                         messages=messages[::-1], 
                         filter_languages=filter_languages)

def get_messages(filter_languages=False):
    logger.info("Reading messages...")
    seen_messages = []
    try:
        with open('seen_messages.txt', 'r') as f:
            for line in f:
                try:
                    # First, try to parse as JSON
                    msg = json.loads(line.strip())
                    if isinstance(msg, dict):
                        seen_messages.append({
                            'pubkey': shorten_pubkey(msg.get('pubkey', 'unknown')),
                            'content': convert_urls_to_links(msg.get('content', '')),
                            'relay': client.relay_url,
                            'created_at': unix_to_pst(int(msg.get('created_at', 0)))
                        })
                    else:
                        print(f"Skipping non-dictionary message: {line.strip()}")
                except json.JSONDecodeError:
                    # If not JSON, try the old format
                    try:
                        parts = line.strip().split(': ', 1)
                        if len(parts) == 2:
                            pubkey, content = parts
                            seen_messages.append({
                                'pubkey': shorten_pubkey(pubkey),
                                'content': convert_urls_to_links(content),
                                'relay': client.relay_url,
                                'created_at': 'unknown'
                            })
                    except Exception as e:
                        print(f"Skipping malformed line: {line.strip()}")
                except ValueError as e:
                    print(f"Error parsing line: {e}")
                continue
    except FileNotFoundError:
        pass

    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            private_key = config['private_key']
            public_key = config['public_key']
    except FileNotFoundError:
        private_key, public_key = generate_key_pair()
        save_keys_to_config(private_key, public_key)

    client = NostrClient(relay_url=None, private_key=private_key, public_key=public_key)
    alive_relays = asyncio.run(client.fetch_relays())
    if alive_relays:
        client.relay_url = alive_relays[0]
        messages = asyncio.run(read_messages_async())
    else:
        messages = []

    # Get your public key first
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            my_public_key = config['public_key']
    except FileNotFoundError:
        my_public_key = None

    # Use a dictionary to prevent duplicates
    unique_messages = {}
    
    # Add seen messages to dictionary
    for msg in seen_messages:
        key = f"{msg['pubkey']}:{msg['content']}"
        unique_messages[key] = msg
    
    # Add new messages, overwriting duplicates
    for msg in messages:
        formatted_msg = {
            'pubkey': shorten_pubkey(msg['pubkey']),
            'content': convert_urls_to_links(msg['content']),
            'relay': client.relay_url,
            'created_at': unix_to_pst(int(msg['created_at'])) if msg.get('created_at') else None,
            'received_at': unix_to_pst(int(msg['received_at'])) if msg.get('received_at') else None,
            'is_own': msg['pubkey'] == my_public_key
        }
        key = f"{msg['pubkey']}:{msg['content']}"
        unique_messages[key] = formatted_msg

    # Convert back to list
    all_messages = list(unique_messages.values())

    if filter_languages:
        all_messages = [msg for msg in all_messages if is_desired_language(msg['content'])]

    # Debug logging
    logger.info(f"My public key: {my_public_key}")
    for msg in all_messages:
        if msg['is_own']:
            logger.info(f"Found own message: {msg['content']}")

    return all_messages

@app.route('/post_message', methods=['POST'])
def post_message():
    message = request.form['message']
    asyncio.run(post_message_async(message))
    return redirect(url_for('index'))

@app.route('/read_messages')
def read_messages():
    # Get filter preference from query parameter
    filter_languages = request.args.get('filter_languages', 'false') == 'true'
    
    logger.info("Reading messages...")
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            private_key = config['private_key']
            public_key = config['public_key']
    except ValueError:
        print(f"Skipping malformed line: {line.strip()}")
    except FileNotFoundError:
        private_key, public_key = generate_key_pair()
        save_keys_to_config(private_key, public_key)
    client = NostrClient(relay_url=None, private_key=private_key, public_key=public_key)
    alive_relays = asyncio.run(client.fetch_relays())
    if alive_relays:
        client.relay_url = alive_relays[0]
    messages = asyncio.run(read_messages_async())
    # Read previously seen messages from the file
    seen_messages = []
    try:
        with open('seen_messages.txt', 'r') as f:
            for line in f:
                try:
                    # First, try to parse as JSON
                    msg = json.loads(line.strip())
                    if isinstance(msg, dict):  # Make sure we have a dictionary
                        seen_messages.append({
                            'pubkey': shorten_pubkey(msg.get('pubkey', 'unknown')),
                            'content': convert_urls_to_links(msg.get('content', '')),
                            'relay': client.relay_url,
                            'created_at': unix_to_pst(int(msg.get('created_at', 0)))
                        })
                    else:
                        print(f"Skipping non-dictionary message: {line.strip()}")
                except json.JSONDecodeError:
                    # If not JSON, try the old format
                    try:
                        parts = line.strip().split(': ', 1)
                        if len(parts) == 2:
                            pubkey, content = parts
                            seen_messages.append({
                                'pubkey': shorten_pubkey(pubkey),
                                'content': convert_urls_to_links(content),
                                'relay': client.relay_url,
                                'created_at': 'unknown'
                            })
                    except Exception as e:
                        print(f"Skipping malformed line: {line.strip()}")
                except ValueError as e:
                    print(f"Error parsing line: {e}")
                continue
    except FileNotFoundError:
        pass

    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            private_key = config['private_key']
            public_key = config['public_key']
    except FileNotFoundError:
        private_key, public_key = generate_key_pair()
        save_keys_to_config(private_key, public_key)
    client = NostrClient(relay_url=None, private_key=private_key, public_key=public_key)
    alive_relays = asyncio.run(client.fetch_relays())
    if alive_relays:
        client.relay_url = alive_relays[0]
        # Combine new messages with previously seen messages
    all_messages = seen_messages + [
        {
            'pubkey': shorten_pubkey(msg['pubkey']),
            'content': convert_urls_to_links(msg['content']),
            'relay': client.relay_url,
            'created_at': unix_to_pst(int(msg['created_at'])) if 'created_at' in msg else None,
            'received_at': unix_to_pst(int(msg['received_at'])) if 'received_at' in msg else None
        } for msg in messages
    ]

    # Use a dictionary to prevent duplicates
    unique_messages = {}
    
    # Add seen messages to dictionary
    for msg in seen_messages:
        key = f"{msg['pubkey']}:{msg['content']}"  # Create unique key
        unique_messages[key] = msg
    
    # Add new messages, overwriting duplicates
    for msg in messages:
        formatted_msg = {
            'pubkey': shorten_pubkey(msg['pubkey']),
            'content': convert_urls_to_links(msg['content']),
            'relay': client.relay_url,
            'created_at': unix_to_pst(int(msg['created_at'])) if 'created_at' in msg else None,
            'received_at': unix_to_pst(int(msg['received_at'])) if 'received_at' in msg else None
        }
        key = f"{msg['pubkey']}:{msg['content']}"
        unique_messages[key] = formatted_msg

    # Convert back to list for template
    all_messages = list(unique_messages.values())

    logger.debug(f"Found {len(all_messages)} unique messages")

    if filter_languages:
        all_messages = [msg for msg in all_messages if is_desired_language(msg['content'])]

    return render_template('messages.html', 
                         messages=all_messages[::-1], 
                         filter_languages=filter_languages)

def convert_urls_to_links(text):
    import re
    url_pattern = re.compile(r'(https?://\S+)')
    return url_pattern.sub(r'<a href="\1" target="_blank">\1</a>', text)

async def post_message_async(message):
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            private_key = config['private_key']
            public_key = config['public_key']
    except FileNotFoundError:
        private_key, public_key = generate_key_pair()
        save_keys_to_config(private_key, public_key)
    client = NostrClient(relay_url=None, private_key=private_key, public_key=public_key)
    alive_relays = await client.fetch_relays()
    if alive_relays:
        client.relay_url = alive_relays[0]
        await client.send_message(message)

async def read_messages_async():
    # Use existing keys instead of generating new ones
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            private_key = config['private_key']
            public_key = config['public_key']
    except FileNotFoundError:
        private_key, public_key = generate_key_pair()
        save_keys_to_config(private_key, public_key)

    client = NostrClient(relay_url=None, private_key=private_key, public_key=public_key)
    alive_relays = await client.fetch_relays()
    if alive_relays:
        client.relay_url = alive_relays[0]
        messages = await client.read_messages()
        return [{'content': msg['content'], 
                'pubkey': msg['pubkey'], 
                'relay': client.relay_url,
                'created_at': msg.get('created_at'),
                'received_at': msg.get('received_at')} for msg in messages]
    return []

def shorten_pubkey(pubkey, length=8):
    """Shorten a public key to first/last n characters."""
    if not pubkey or len(pubkey) < length * 2:
        return pubkey
    return f"{pubkey[:length]}...{pubkey[-length:]}"

@app.route('/clear_messages', methods=['POST'])
def clear_messages():
    try:
        logger.info("Attempting to clear messages...")
        with open('seen_messages.txt', 'w') as f:
            f.write('')
        logger.info("Messages cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing messages: {str(e)}")
        return f"Error: {str(e)}", 500
    
    return redirect(url_for('index'))

def is_desired_language(text):
    try:
        lang = detect(text)
        return lang in ['en', 'de', 'nl', 'fr', 'es', 'it']
    except LangDetectException:
        return False

if __name__ == '__main__':
    port = 5001  # Changed port to 5001
    click.echo(f"\nServer starting. Click the link below to open the app:")
    click.echo(click.style(f"http://127.0.0.1:{port}", underline=True, fg="cyan"))
    app.run(debug=True, port=port)
