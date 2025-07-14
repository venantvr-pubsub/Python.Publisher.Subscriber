# client.py

import requests
import socketio

BASE_URL = "http://localhost:5000"


# noinspection PyMethodMayBeStatic
class PubSubClient:
    def __init__(self, consumer_name, topics):
        self.sio = socketio.Client(reconnection=True)
        self.consumer_name = consumer_name
        self.topics = topics

        self.sio.on("message", self.on_message)
        self.sio.on("new_client", self.on_new_client)
        self.sio.on("client_disconnected", self.on_client_disconnected)
        self.sio.on("new_consumption", self.on_new_consumption)

    def connect(self):
        self.sio.connect(BASE_URL)
        self.sio.emit("subscribe", {
            "consumer": self.consumer_name,
            "topics": self.topics
        })
        print(f"Connected as {self.consumer_name}, subscribed to {self.topics}")

    def on_message(self, data):
        print(f"[MESSAGE] [{data['topic']}] {data['message']}")

    def on_new_client(self, data):
        print("[NEW CLIENT]", data)

    def on_client_disconnected(self, data):
        print("[CLIENT DISCONNECTED]", data)

    def on_new_consumption(self, data):
        print("[NEW CONSUMPTION]", data)

    def publish(self, topic, message):
        resp = requests.post(f"{BASE_URL}/publish", json={
            "topic": topic,
            "message": message
        })
        return resp.json()

    def run_forever(self):
        self.sio.wait()
