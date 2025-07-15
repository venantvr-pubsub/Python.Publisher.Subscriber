# client.py

import logging
from typing import List, Dict, Any

import requests
import socketio
from socketio import exceptions

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"


# noinspection PyMethodMayBeStatic
class PubSubClient:
    def __init__(self, consumer_name: str, topics: List[str]):
        """
        Initialize the PubSub client.

        :param consumer_name: Name of the consumer (e.g., 'alice')
        :param topics: List of topics to subscribe to
        """
        self.sio = socketio.Client(reconnection=True)
        self.consumer_name = consumer_name
        self.topics = topics

        # Register event handlers
        self.sio.on("message", self.on_message)
        self.sio.on("new_client", self.on_new_client)
        self.sio.on("client_disconnected", self.on_client_disconnected)
        self.sio.on("new_consumption", self.on_new_consumption)
        self.sio.on("new_message", self.on_new_message)

    def connect(self) -> None:
        logger.info(f"Attempting to connect as {self.consumer_name} to {BASE_URL}")
        try:
            self.sio.connect(BASE_URL)
            self.sio.emit("subscribe", {
                "consumer": self.consumer_name,
                "topics": self.topics
            })
            logger.info(f"Connected as {self.consumer_name}, subscribed to {self.topics}")
        except exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to server: {e}")
            # Optionally, implement retry logic or exit
        except Exception as e:
            logger.error(f"An unexpected error occurred during connection: {e}")

    def on_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming messages."""
        logger.info(f"[MESSAGE] [{data['topic']}] {data['message']}")

    def on_new_client(self, data: Dict[str, Any]) -> None:
        """Handle new client connections."""
        logger.info(f"[NEW CLIENT] {data}")

    def on_client_disconnected(self, data: Dict[str, Any]) -> None:
        """Handle client disconnections."""
        logger.info(f"[CLIENT DISCONNECTED] {data}")

    def on_new_consumption(self, data: Dict[str, Any]) -> None:
        """Handle new consumption events."""
        logger.info(f"[NEW CONSUMPTION] {data}")

    def on_new_message(self, data: Dict[str, Any]) -> None:
        """Handle new message events."""
        logger.info(f"[NEW MESSAGE] {data}")

    def publish(self, topic: str, message: Any, message_id: str) -> Dict[str, Any]:
        """
        Publish a message to a topic via HTTP POST.

        :param topic: Topic to publish to
        :param message: Message content
        :param message_id: Unique message ID
        :return: Server response
        """
        logger.info(f"Publishing to topic {topic}: {message} with ID {message_id}")
        resp = requests.post(f"{BASE_URL}/publish", json={
            "topic": topic,
            "message": message,
            "producer": self.consumer_name,
            "message_id": message_id
        })
        logger.info(f"Publish response: {resp.json()}")
        return resp.json()

    def run_forever(self) -> None:
        """Keep the client running indefinitely."""
        self.sio.wait()

    def disconnect(self) -> None:
        """Disconnect from the Socket.IO server."""
        if self.sio.connected:
            self.sio.disconnect()
            logger.info(f"Disconnected {self.consumer_name} from server.")
