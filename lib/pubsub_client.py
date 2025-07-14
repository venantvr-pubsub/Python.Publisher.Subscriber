import logging
from typing import List, Dict, Any, Callable

import requests
import socketio

from lib.pubsub_message import PubSubMessage

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PubSubClient:
    def __init__(self, url: str, consumer: str, topics: List[str]):
        """
        Initialize the PubSub client.

        :param url: URL of the Socket.IO server, e.g., http://localhost:5000
        :param consumer: Consumer name (e.g., 'alice')
        :param topics: List of topics to subscribe to
        """
        self.url = url.rstrip("/")
        self.consumer = consumer
        self.topics = topics
        self.handlers: Dict[str, Callable] = {}  # topic → function

        # Create Socket.IO client
        self.sio = socketio.Client()

        # Register generic events
        self.sio.on("connect", self.on_connect)
        self.sio.on("message", self.on_message)
        self.sio.on("disconnect", self.on_disconnect)
        self.sio.on("new_message", self.on_new_message)

    def register_handler(self, topic: str, handler_func: Callable[[Any], None]) -> None:
        """
        Register a custom handler for a given topic.

        :param topic: Topic to handle
        :param handler_func: Function to call when a message is received
        """
        self.handlers[topic] = handler_func

    def on_connect(self) -> None:
        """Handle connection to the server."""
        logger.info(f"[{self.consumer}] Connected to server {self.url}")
        self.sio.emit("subscribe", {
            "consumer": self.consumer,
            "topics": self.topics
        })

    def on_message(self, data: Dict[str, Any]) -> None:
        """
        Handle incoming messages.

        :param data: Message data containing topic, message_id, message, and producer
        """
        topic = data["topic"]
        message_id = data.get("message_id")
        message = data["message"]
        producer = data.get("producer")

        logger.info(f"[{self.consumer}] Received on topic [{topic}]: {message} (from {producer}, ID={message_id})")

        if topic in self.handlers:
            self.handlers[topic](message)
        else:
            logger.warning(f"[{self.consumer}] No handler for topic {topic}.")

        # Notify consumption
        self.sio.emit("consumed", {
            "consumer": self.consumer,
            "topic": topic,
            "message_id": message_id,
            "message": message
        })

    def on_disconnect(self) -> None:
        """Handle disconnection from the server."""
        logger.info(f"[{self.consumer}] Disconnected from server.")

    def on_new_message(self, data: Dict[str, Any]) -> None:
        """Handle new message events."""
        logger.info(f"[{self.consumer}] New message: {data}")

    def publish(self, topic: str, message: Any, producer: str, message_id: str) -> None:
        """
        Publish a message via HTTP POST to the pubsub backend.

        :param topic: Topic to publish to
        :param message: Message content
        :param producer: Name of the producer
        :param message_id: Unique message ID
        """
        msg = PubSubMessage.new(topic, message, producer, message_id)
        url = f"{self.url}/publish"
        logger.info(f"[{self.consumer}] Publishing to {topic}: {msg.to_dict()}")
        resp = requests.post(url, json=msg.to_dict())
        logger.info(f"[{self.consumer}] Publish response: {resp.json()}")

    def start(self) -> None:
        """Start the client and connect to the server."""
        logger.info(f"Starting client {self.consumer} with topics {self.topics}")
        self.sio.connect(self.url)
        self.sio.wait()