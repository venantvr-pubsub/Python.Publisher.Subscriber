# pubsub_ws.py

import sqlite3
import time

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room

DB_NAME = "pubsub.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


# --- Database init
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            message TEXT,
            timestamp REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            sid TEXT,
            consumer TEXT,
            topic TEXT,
            connected_at REAL,
            PRIMARY KEY (sid, topic)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS consumptions (
            consumer TEXT,
            topic TEXT,
            message TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()


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

    def save_message(self, topic, message):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            INSERT INTO messages (topic, message, timestamp)
            VALUES (?, ?, ?)
        """, (topic, message, time.time()))
        conn.commit()
        conn.close()

    def save_consumption(self, consumer, topic, message):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("""
            INSERT INTO consumptions (consumer, topic, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (consumer, topic, message, time.time()))
        conn.commit()
        conn.close()

        socketio.emit("new_consumption", {
            "consumer": consumer,
            "topic": topic,
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
            SELECT consumer, topic, message, timestamp FROM consumptions
            ORDER BY timestamp DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [
            {
                "consumer": r[0],
                "topic": r[1],
                "message": r[2],
                "timestamp": r[3]
            }
            for r in rows
        ]


broker = Broker(DB_NAME)


# --- HTTP Routes

@app.route("/publish", methods=["POST"])
def publish():
    data = request.json
    topic = data.get("topic")
    message = data.get("message")

    broker.save_message(topic, message)

    # Broadcast to topic room
    socketio.emit("message", {
        "topic": topic,
        "message": message
    }, to=topic)

    # Also send to wildcard room
    socketio.emit("message", {
        "topic": topic,
        "message": message
    }, to="*")

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


@socketio.on("disconnect")
def handle_disconnect():
    # noinspection PyUnresolvedReferences
    sid = request.sid
    broker.unregister_client(sid)


@socketio.on("consumed")
def handle_consumed(data):
    consumer = data.get("consumer")
    topic = data.get("topic")
    message = data.get("message")
    if consumer and topic and message:
        broker.save_consumption(consumer, topic, message)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
