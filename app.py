from flask import Flask, render_template, request, redirect, url_for
import asyncio
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
    return render_template('messages.html', messages=messages)

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
    app.run(host='0.0.0.0', port=5000, debug=True)
