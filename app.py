from flask import Flask, render_template, request, redirect, url_for
import asyncio
import click
from nostr_client import NostrClient, unix_to_pst

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
    client = NostrClient()
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
                    seen_messages.append({'pubkey': pubkey, 'content': convert_urls_to_links(content), 'relay': client.relay_url, 'created_at': unix_to_pst(int(created_at)) if created_at != 'unknown' else 'unknown'})
                except ValueError:
                    print(f"Skipping malformed line: {line.strip()}")
    except FileNotFoundError:
        pass

    client = NostrClient()
    alive_relays = asyncio.run(client.fetch_relays())
    if alive_relays:
        client.relay_url = alive_relays[0]
        # Combine new messages with previously seen messages
    all_messages = seen_messages + [{'pubkey': msg['pubkey'], 'content': convert_urls_to_links(msg['content']), 'relay': client.relay_url, 'created_at': unix_to_pst(int(msg.get('created_at', 'unknown'))) if msg.get('created_at', 'unknown') != 'unknown' else 'unknown'} for msg in messages]

    return render_template('messages.html', messages=all_messages[::-1])

def convert_urls_to_links(text):
    import re
    url_pattern = re.compile(r'(https?://\S+)')
    return url_pattern.sub(r'<a href="\1" target="_blank">\1</a>', text)

async def post_message_async(message):
    client = NostrClient()
    alive_relays = await client.fetch_relays()
    if alive_relays:
        client.relay_url = alive_relays[0]
        await client.send_message(message)

async def read_messages_async():
    client = NostrClient()
    alive_relays = await client.fetch_relays()
    if alive_relays:
        client.relay_url = alive_relays[0]
        messages = await client.read_messages()
        return [{'content': msg['content'], 'pubkey': msg['pubkey'], 'relay': client.relay_url} for msg in messages]
    return []

if __name__ == '__main__':
    port = 5000  # You can change this if needed
    click.echo(f"\nServer starting. Click the link below to open the app:")
    click.echo(click.style(f"http://127.0.0.1:{port}", underline=True, fg="cyan"))
    app.run(debug=True, port=port)
