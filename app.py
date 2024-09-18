from flask import Flask, render_template, request, redirect, url_for
import asyncio
import click
from nostr_client import NostrClient

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
    messages = asyncio.run(read_messages_async())
    # Read previously seen messages from the file
    seen_messages = []
    try:
        with open('seen_messages.txt', 'r') as f:
            for line in f:
                pubkey, content = line.strip().split(': ', 1)
                seen_messages.append({'pubkey': pubkey, 'content': content})
    except FileNotFoundError:
        pass

    # Combine new messages with previously seen messages
    all_messages = seen_messages + messages

    return render_template('messages.html', messages=all_messages)

async def post_message_async(message):
    client = NostrClient("dummy_url")
    alive_relays = await client.fetch_relays()
    if alive_relays:
        client.relay_url = alive_relays[0]
        await client.send_message(message)

async def read_messages_async():
    client = NostrClient("dummy_url")
    alive_relays = await client.fetch_relays()
    if alive_relays:
        client.relay_url = alive_relays[0]
        messages = await client.read_messages()
        return messages
    return []

if __name__ == '__main__':
    port = 5000  # You can change this if needed
    click.echo(f"\nServer starting. Click the link below to open the app:")
    click.echo(click.style(f"http://127.0.0.1:{port}", underline=True, fg="cyan"))
    app.run(debug=True, port=port)
