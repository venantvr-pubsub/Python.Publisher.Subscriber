import json
import logging
import sqlite3
import time
from os import path
from typing import Dict, Any, List

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "pubsub.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


def init_db() -> None:
    """Initialize the SQLite database and run migrations if necessary."""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # Check if messages table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not c.fetchone():
            logger.info("[INIT DB] Messages table missing, running migration script...")
            migration_script = "migrations/001_add_message_id_and_producer.sql"
            if path.exists(migration_script):
                with open(migration_script) as f:
                    conn.executescript(f.read())
                    logger.info("[INIT DB] Migration script executed successfully.")


init_db()


class Broker:
    def __init__(self, db_name: str):
        """
        Initialize the Broker with a database name.

        :param db_name: Name of the SQLite database file
        """
        self.db_name = db_name

    def register_subscription(self, sid: str, consumer: str, topic: str) -> None:
        """
        Register a client subscription to a topic.

        :param sid: Socket.IO session ID
        :param consumer: Consumer name
        :param topic: Topic to subscribe to
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO subscriptions (sid, consumer, topic, connected_at)
            VALUES (?, ?, ?, ?)
        """, (sid, consumer, topic, time.time()))
        conn.commit()
        conn.close()
        logger.info(f"Registered subscription: {consumer} to {topic} (SID: {sid})")

        socketio.emit("new_client", {
            "consumer": consumer,
            "topic": topic
        })

    def unregister_client(self, sid: str) -> None:
        """
        Unregister a client from all subscriptions.

        :param sid: Socket.IO session ID
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT consumer, topic FROM subscriptions WHERE sid = ?", (sid,))
        rows = c.fetchall()
        c.execute("DELETE FROM subscriptions WHERE sid = ?", (sid,))
        conn.commit()
        conn.close()

        for consumer, topic in rows:
            logger.info(f"Unregistered client: {consumer} from {topic} (SID: {sid})")
            socketio.emit("client_disconnected", {
                "consumer": consumer,
                "topic": topic
            })

    def save_message(self, topic: str, message_id: str, message: Any, producer: str) -> None:
        """
        Save a message to the database and notify all clients.

        :param topic: Topic of the message
        :param message_id: Unique message ID
        :param message: Message content
        :param producer: Producer name
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        timestamp = time.time()
        c.execute("""
            INSERT INTO messages (topic, message_id, message, producer, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            topic,
            message_id,
            json.dumps(message),
            producer,
            timestamp
        ))
        conn.commit()
        conn.close()
        logger.info(f"Saved message: {message_id} to topic {topic} by {producer}")

        # Notify all clients of the new message for UI updates
        socketio.emit("new_message", {
            "topic": topic,
            "message_id": message_id,
            "message": message,
            "producer": producer,
            "timestamp": timestamp
        })

    def save_consumption(self, consumer: str, topic: str, message_id: str, message: Any) -> None:
        """
        Save a consumption event to the database.

        :param consumer: Consumer name
        :param topic: Topic consumed
        :param message_id: Message ID
        :param message: Message content
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            INSERT INTO consumptions (consumer, topic, message_id, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (consumer, topic, message_id, json.dumps(message), time.time()))
        conn.commit()
        conn.close()
        logger.info(f"Saved consumption: {consumer} consumed {message_id} from {topic}")

        socketio.emit("new_consumption", {
            "consumer": consumer,
            "topic": topic,
            "message_id": message_id,
            "message": message,
            "timestamp": time.time()
        })

    # noinspection PyShadowingNames
    def get_clients(self) -> List[Dict[str, Any]]:
        """
        Retrieve the list of connected clients.

        :return: List of client dictionaries
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            SELECT consumer, topic, connected_at FROM subscriptions
        """)
        rows = c.fetchall()
        conn.close()
        clients = [{"consumer": r[0], "topic": r[1], "connected_at": r[2]} for r in rows]
        logger.info(f"Retrieved {len(clients)} connected clients")
        return clients

    # noinspection PyShadowingNames
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Retrieve the list of published messages.

        :return: List of message dictionaries
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            SELECT topic, message_id, message, producer, timestamp FROM messages
            WHERE message_id IS NOT NULL
            ORDER BY timestamp DESC
        """)
        rows = c.fetchall()
        conn.close()
        messages = [
            {
                "topic": r[0],
                "message_id": r[1],
                "message": json.loads(r[2]),
                "producer": r[3],
                "timestamp": r[4]
            }
            for r in rows
        ]
        logger.info(f"Retrieved {len(messages)} messages")
        return messages

    # noinspection PyShadowingNames
    def get_consumptions(self) -> List[Dict[str, Any]]:
        """
        Retrieve the list of consumption events.

        :return: List of consumption dictionaries
        """
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            SELECT consumer, topic, message_id, message, timestamp FROM consumptions
            WHERE message_id IS NOT NULL
            ORDER BY timestamp DESC
        """)
        rows = c.fetchall()
        conn.close()
        consumptions = [
            {
                "consumer": r[0],
                "topic": r[1],
                "message_id": r[2],
                "message": json.loads(r[3]),
                "timestamp": r[4]
            }
            for r in rows
        ]
        logger.info(f"Retrieved {len(consumptions)} consumption events")
        return consumptions


broker = Broker(DB_NAME)


@app.route("/publish", methods=["POST"])
def publish():
    """Handle message publishing, requiring a message_id."""
    data = request.json
    topic = data.get("topic")
    message_id = data.get("message_id")
    message = data.get("message")
    producer = data.get("producer")

    if not all([topic, message_id, message, producer]):
        logger.error("Publish failed: Missing topic, message_id, message, or producer")
        return jsonify({"status": "error", "message": "Missing topic, message_id, message, or producer"}), 400

    logger.info(f"Publishing message {message_id} to topic {topic} by {producer}")
    broker.save_message(
        topic=topic,
        message_id=message_id,
        message=message,
        producer=producer
    )

    payload = {
        "topic": topic,
        "message_id": message_id,
        "message": message,
        "producer": producer
    }

    socketio.emit("message", payload, to=topic)
    socketio.emit("message", payload, to="*")

    return jsonify({"status": "ok"})


@app.route("/clients")
def clients():
    """Return the list of connected clients."""
    logger.info("Fetching connected clients")
    return jsonify(broker.get_clients())


@app.route("/messages")
def messages():
    """Return the list of published messages."""
    logger.info("Fetching published messages")
    return jsonify(broker.get_messages())


@app.route("/consumptions")
def consumptions():
    """Return the list of consumption events."""
    logger.info("Fetching consumption events")
    return jsonify(broker.get_consumptions())


@app.route("/client.html")
def serve_client():
    """Serve the client HTML page."""
    logger.info("Serving client.html")
    return send_from_directory(".", "client.html")


@socketio.on("subscribe")
def handle_subscribe(data: Dict[str, Any]) -> None:
    """
    Handle client subscription to topics.

    :param data: Subscription data containing consumer and topics
    """
    consumer = data.get("consumer")
    topics = data.get("topics", [])

    # noinspection PyUnresolvedReferences
    sid = request.sid

    logger.info(f"Subscribing {consumer} to topics {topics} (SID: {sid})")
    for topic in topics:
        join_room(topic)
        broker.register_subscription(sid, consumer, topic)
        emit("message", {
            "topic": topic,
            "message": f"Subscribed to {topic}"
        }, to=sid)


@socketio.on("consumed")
def handle_consumed(data: Dict[str, Any]) -> None:
    """
    Handle message consumption events.

    :param data: Consumption data containing consumer, topic, message_id, and message
    """
    consumer = data.get("consumer")
    topic = data.get("topic")
    message_id = data.get("message_id")
    message = data.get("message")

    logger.info(f"Handling consumption by {consumer} for message {message_id} in topic {topic}")
    broker.save_consumption(consumer, topic, message_id, message)


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle client disconnection."""
    # noinspection PyUnresolvedReferences
    sid = request.sid
    logger.info(f"Client disconnected (SID: {sid})")
    broker.unregister_client(sid)


if __name__ == "__main__":
    logger.info("Starting Flask-SocketIO server on port 5000")
    socketio.run(app, host="0.0.0.0", port=5000)