import requests
import socketio

from lib.pubsub_message import PubSubMessage


class PubSubClient:
    def __init__(self, url, consumer, topics):
        """
        :param url: URL of the Socket.IO server, e.g. http://localhost:5000
        :param consumer: Consumer name (e.g. 'alice')
        :param topics: List of topics to subscribe to
        """
        self.url = url.rstrip("/")
        self.consumer = consumer
        self.topics = topics
        self.handlers = {}  # topic → function

        # Create Socket.IO client
        self.sio = socketio.Client()

        # Register generic events
        self.sio.on("connect", self.on_connect)
        self.sio.on("message", self.on_message)
        self.sio.on("disconnect", self.on_disconnect)

    def register_handler(self, topic, handler_func):
        """
        Register a custom handler for a given topic.
        """
        self.handlers[topic] = handler_func

    def on_connect(self):
        print(f"[{self.consumer}] Connected to server.")
        self.sio.emit("subscribe", {
            "consumer": self.consumer,
            "topics": self.topics
        })

    def on_message(self, data):
        topic = data["topic"]
        message_id = data.get("message_id")
        message = data["message"]
        producer = data.get("producer")

        print(f"[{self.consumer}] Received on topic [{topic}]: {message} (from {producer}, ID={message_id})")

        if topic in self.handlers:
            self.handlers[topic](message)
        else:
            print(f"[{self.consumer}] No handler for topic {topic}.")

        # Notify consumption
        self.sio.emit("consumed", {
            "consumer": self.consumer,
            "topic": topic,
            "message_id": message_id,
            "message": message
        })

    def on_disconnect(self):
        print(f"[{self.consumer}] Disconnected.")

    def publish(self, topic, message, producer):
        """
        Publish a message via HTTP POST to the pubsub backend.
        """
        msg = PubSubMessage.new(topic, message, producer)
        url = f"{self.url}/publish"
        resp = requests.post(url, json=msg.to_dict())
        print(f"[{self.consumer}] Published to {topic}: {resp.json()}")

    def start(self):
        self.sio.connect(self.url)
        self.sio.wait()
