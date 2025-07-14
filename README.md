# PubSub WebSocket Server

This is a simple Pub/Sub broker built with Flask + Flask-SocketIO and SQLite.

It supports:

- publishing messages to topics
- subscribing clients to multiple topics
- live monitoring of:
    - connected clients
    - message consumptions

## How to Run

### Install dependencies

    pip install -r requirements.txt

If you use eventlet:

    pip install eventlet

### Run the server

    python pubsub_ws.py

By default, the server runs on http://localhost:5000

## Publish messages

Example with curl:

    curl -X POST http://localhost:5000/publish \
         -H "Content-Type: application/json" \
         -d '{"topic": "sport", "message": "Hello sports fans!"}'

## Web Interface

Open your browser at:

    http://localhost:5000/client.html

This page allows:

- connecting as a consumer
- subscribing to multiple topics
- publishing messages
- monitoring connected clients
- monitoring consumed messages

## Python Client Example

Here’s how to connect as a Python client, subscribe to topics, and handle messages:

```python
from python_client import PubSubClient


def sport_handler(message):
    print("SPORT handler received:", message)


def finance_handler(message):
    print("FINANCE handler received:", message)


client = PubSubClient(
    url="http://localhost:5000",
    consumer="alice",
    topics=["sport", "finance"]
)

client.register_handler("sport", sport_handler)
client.register_handler("finance", finance_handler)

client.start()
````

## Database

Data is stored in SQLite:

* `messages` → published messages
* `subscriptions` → who is subscribed to which topic
* `consumptions` → who consumed which message and when

You can inspect the DB file:

```
sqlite3 pubsub.db
```
