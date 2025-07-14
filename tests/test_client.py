# tests/test_client.py

import client


def test_connect_emits_subscribe(mocker):
    mock_client = mocker.MagicMock()
    mock_sio = mocker.patch("client.socketio.Client", return_value=mock_client)

    pubsub = client.PubSubClient("alice", ["sport", "finance"])
    pubsub.connect()

    mock_client.connect.assert_called_once_with("http://localhost:5000")
    mock_client.emit.assert_called_once_with(
        "subscribe",
        {
            "consumer": "alice",
            "topics": ["sport", "finance"]
        }
    )


def test_publish_calls_http(mocker):
    mock_post = mocker.patch("client.requests.post")
    mock_post.return_value.json.return_value = {"status": "ok"}

    pubsub = client.PubSubClient("bob", ["finance"])
    result = pubsub.publish("finance", "Hello!")

    mock_post.assert_called_once_with(
        "http://localhost:5000/publish",
        json={"topic": "finance", "message": "Hello!"}
    )
    assert result == {"status": "ok"}
