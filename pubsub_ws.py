import json
import sqlite3
import time
from os import path

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room

DB_NAME = "pubsub.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


# --- Database init
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # Check if messages table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not c.fetchone():
            print("[INIT DB] messages table missing, running migration script...")
            migration_script = "migrations/001_add_message_id_and_producer.sql"
            if path.exists(migration_script):
                with open(migration_script) as f:
                    conn.executescript(f.read())

init_db()


# --- Broker class
class Broker:
    def __init__(self, db_name):
        self.db_name = db_name

    def register_subscription(self, sid, consumer, topic):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO subscriptions (sid, consumer, topic, connected_at)
            VALUES (?, ?, ?, ?)
        """, (sid, consumer, topic, time.time()))
        conn.commit()
        conn.close()

        socketio.emit("new_client", {
            "consumer": consumer,
            "topic": topic
        })

    def unregister_client(self, sid):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT consumer, topic FROM subscriptions WHERE sid = ?", (sid,))
        rows = c.fetchall()
        c.execute("DELETE FROM subscriptions WHERE sid = ?", (sid,))
        conn.commit()
        conn.close()

        for consumer, topic in rows:
            socketio.emit("client_disconnected", {
                "consumer": consumer,
                "topic": topic
            })

    def save_message(self, topic, message_id, message, producer):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            INSERT INTO messages (topic, message_id, message, producer, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            topic,
            message_id,
            json.dumps(message),
            producer,
            time.time()
        ))
        conn.commit()
        conn.close()

    def save_consumption(self, consumer, topic, message_id, message):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            INSERT INTO consumptions (consumer, topic, message_id, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (consumer, topic, message_id, json.dumps(message), time.time()))
        conn.commit()
        conn.close()

        socketio.emit("new_consumption", {
            "consumer": consumer,
            "topic": topic,
            "message_id": message_id,
            "message": message,
            "timestamp": time.time()
        })

    def get_clients(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            SELECT consumer, topic, connected_at FROM subscriptions
        """)
        rows = c.fetchall()
        conn.close()
        return [
            {"consumer": r[0], "topic": r[1], "connected_at": r[2]}
            for r in rows
        ]

    def get_consumptions(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            SELECT consumer, topic, message_id, message, timestamp FROM consumptions
            ORDER BY timestamp DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [
            {
                "consumer": r[0],
                "topic": r[1],
                "message_id": r[2],
                "message": json.loads(r[3]),
                "timestamp": r[4]
            }
            for r in rows
        ]


broker = Broker(DB_NAME)


# --- HTTP Routes

@app.route("/publish", methods=["POST"])
def publish():
    data = request.json
    topic = data.get("topic")
    message_id = data.get("message_id")
    message = data.get("message")
    producer = data.get("producer")

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
    return jsonify(broker.get_clients())


@app.route("/consumptions")
def consumptions():
    return jsonify(broker.get_consumptions())


@app.route("/client.html")
def serve_client():
    return send_from_directory(".", "client.html")


# --- WebSocket events

@socketio.on("subscribe")
def handle_subscribe(data):
    consumer = data.get("consumer")
    topics = data.get("topics", [])

    # noinspection PyUnresolvedReferences
    sid = request.sid

    for topic in topics:
        join_room(topic)
        broker.register_subscription(sid, consumer, topic)
        emit("message", {
            "topic": topic,
            "message": f"Subscribed to {topic}"
        }, to=sid)


@socketio.on("consumed")
def handle_consumed(data):
    consumer = data.get("consumer")
    topic = data.get("topic")
    message_id = data.get("message_id")
    message = data.get("message")

    broker.save_consumption(consumer, topic, message_id, message)


@socketio.on("disconnect")
def handle_disconnect():
    # noinspection PyUnresolvedReferences
    sid = request.sid
    broker.unregister_client(sid)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
