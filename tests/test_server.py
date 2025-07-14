from pubsub_ws import app, socketio


def test_subscribe_event():
    test_client = socketio.test_client(app)
    test_client.emit("subscribe", {
        "consumer": "alice",
        "topics": ["sport"]
    })

    received = test_client.get_received()
    topics = [r["args"]["topic"] for r in received if r["name"] == "message"]

    assert "sport" in topics
