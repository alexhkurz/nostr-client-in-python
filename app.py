import time
import json
from flask import Flask, render_template, request, redirect, url_for
import asyncio
import click
from nostr_client import NostrClient, unix_to_pst
from generate_keys import generate_key_pair, save_keys_to_config

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/post_message', methods=['POST'])
def post_message():
    message = request.form['message']
    asyncio.run(post_message_async(message))
    return redirect(url_for('index'))

@app.route('/read_messages')
def read_messages():
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
    # Read previously seen messages from the file
    seen_messages = []
    try:
        with open('seen_messages.txt', 'r') as f:
            for line in f:
                try:
                    pubkey, rest = line.strip().split(': ', 1)
                    content, created_at = rest.rsplit(' (created_at: ', 1)
                    created_at = created_at.rstrip(')')
                    if 'created_at' in rest:
                        seen_messages.append({'pubkey': pubkey, 'content': convert_urls_to_links(content), 'relay': client.relay_url, 'created_at': unix_to_pst(int(created_at))})
                    else:
                        seen_messages.append({'pubkey': pubkey, 'content': convert_urls_to_links(content), 'relay': client.relay_url, 'received_at': unix_to_pst(int(time.time()))})
                except ValueError:
                    print(f"Skipping malformed line: {line.strip()}")
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
            'pubkey': msg['pubkey'],
            'content': convert_urls_to_links(msg['content']),
            'relay': client.relay_url,
            'created_at': unix_to_pst(int(msg['created_at'])) if 'created_at' in msg else None,
            'received_at': unix_to_pst(int(msg['received_at'])) if 'received_at' in msg else None
        } for msg in messages
    ]

    return render_template('messages.html', messages=all_messages[::-1])

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
    private_key, public_key = generate_key_pair()
    save_keys_to_config(private_key, public_key)
    client = NostrClient(relay_url=None, private_key=private_key, public_key=public_key)
    alive_relays = await client.fetch_relays()
    if alive_relays:
        client.relay_url = alive_relays[0]
        messages = await client.read_messages()
        return [{'content': msg['content'], 'pubkey': msg['pubkey'], 'relay': client.relay_url} for msg in messages]
    return []

if __name__ == '__main__':
    port = 5001  # Changed port to 5001
    click.echo(f"\nServer starting. Click the link below to open the app:")
    click.echo(click.style(f"http://127.0.0.1:{port}", underline=True, fg="cyan"))
    app.run(debug=True, port=port)
