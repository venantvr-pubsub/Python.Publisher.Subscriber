import logging
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from socketio import exceptions

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from client import PubSubClient, BASE_URL


# Mock du socketio.Client
# On va mocker la classe socketio.Client elle-même, pas son instance directement
# Ensuite, on accède à mock_sio_client.return_value pour mocker les méthodes de l'instance
@pytest.fixture
def mock_sio_client():
    """Mocke l'instance de socketio.Client utilisée par PubSubClient."""
    with patch('client.socketio.Client') as MockClient:  # <-- Patch la classe directement dans le module client
        instance = MockClient.return_value  # Ceci est le mock de l'instance qui sera créée
        instance.connected = False  # Simule l'état initial déconnecté
        yield MockClient  # On yield le Mock de la CLASSE Client elle-même, pas son instance


# Mock de requests.post
@pytest.fixture
def mock_requests_post():
    """Mocke requests.post pour les appels de publication HTTP."""
    # Patch requests.post dans le module client où il est utilisé
    with patch('client.requests.post') as mock_post:  # <-- Patch requests.post dans le module client
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "message_id": "test_id_returned"}
        mock_response.raise_for_status.return_value = None  # Pas d'erreurs HTTP par défaut
        mock_post.return_value = mock_response
        yield mock_post


# --- Tests pour la classe PubSubClient (du fichier client.py) ---

def test_pubsub_client_init(mock_sio_client):
    """Vérifie l'initialisation du client et l'enregistrement des gestionnaires."""
    consumer = "test_alice"
    topics = ["sport", "finance"]
    client = PubSubClient(consumer, topics)

    assert client.consumer_name == consumer
    assert client.topics == topics

    # Vérifiez que socketio.Client a été appelé une fois avec le bon argument
    mock_sio_client.assert_called_once_with(reconnection=True)

    # Vérifiez que les gestionnaires d'événements sont enregistrés sur l'instance mockée
    mock_sio_client.return_value.on.assert_any_call("message", client.on_message)
    mock_sio_client.return_value.on.assert_any_call("new_client", client.on_new_client)
    mock_sio_client.return_value.on.assert_any_call("client_disconnected", client.on_client_disconnected)
    mock_sio_client.return_value.on.assert_any_call("new_consumption", client.on_new_consumption)
    mock_sio_client.return_value.on.assert_any_call("new_message", client.on_new_message)


def test_pubsub_client_connect_success(mock_sio_client):
    """Teste la méthode connect en cas de succès."""
    consumer = "test_bob"
    topics = ["tech"]
    client = PubSubClient(consumer, topics)

    # Obtenez le mock de l'instance client qui a été créée
    mock_instance = mock_sio_client.return_value
    mock_instance.connected = True  # Simule une connexion réussie

    client.connect()

    # Vérifiez que connect a été appelé sur l'instance mockée avec la bonne URL
    mock_instance.connect.assert_called_once_with(BASE_URL)

    # Vérifiez que l'événement "subscribe" a été émis sur l'instance mockée
    mock_instance.emit.assert_called_once_with(
        "subscribe", {"consumer": consumer, "topics": topics}
    )


def test_pubsub_client_connect_failure(mock_sio_client, caplog):
    """Teste la méthode connect en cas d'échec de connexion."""
    consumer = "test_charlie"
    topics = ["music"]
    client = PubSubClient(consumer, topics)

    # Obtenez le mock de l'instance client
    mock_instance = mock_sio_client.return_value
    # Simule une ConnectionError lors de la connexion
    mock_instance.connect.side_effect = exceptions.ConnectionError("Connection refused")

    with caplog.at_level(logging.ERROR):  # Capture les logs d'erreur
        client.connect()

    # Le message d'erreur doit être dans les logs
    assert "Failed to connect to server: Connection refused" in caplog.text
    # Vérifiez que connect a été appelé même s'il a levé une exception
    mock_instance.connect.assert_called_once()


def test_pubsub_client_on_message(caplog):
    """Teste le gestionnaire on_message."""
    consumer = "test_diana"
    topics = ["food"]
    client = PubSubClient(consumer, topics)

    test_data = {"topic": "pizza", "message": {"type": "text", "content": "Hello pizza!"}}
    with caplog.at_level(logging.INFO):
        client.on_message(test_data)
    assert "[MESSAGE] [pizza] {'type': 'text', 'content': 'Hello pizza!'}" in caplog.text


def test_pubsub_client_publish(mock_requests_post):
    """Teste la méthode publish."""
    consumer = "test_eve"
    topics = ["travel"]
    client = PubSubClient(consumer, topics)

    topic_to_publish = "destinations"
    message_content = {"city": "Paris", "country": "France"}
    message_id = "uuid-1234"

    response = client.publish(topic_to_publish, message_content, message_id)

    # Vérifiez que requests.post a été appelé avec les bonnes données
    expected_url = f"{BASE_URL}/publish"
    expected_json = {
        "topic": topic_to_publish,
        "message": message_content,
        "producer": consumer,
        "message_id": message_id
    }
    mock_requests_post.assert_called_once_with(expected_url, json=expected_json)

    # Vérifiez la réponse renvoyée par la méthode publish
    assert response == {"status": "ok", "message_id": "test_id_returned"}


def test_pubsub_client_disconnect_connected(mock_sio_client, caplog):
    """Teste la déconnexion quand le client est connecté."""
    consumer = "test_frank"
    topics = ["sports"]
    client = PubSubClient(consumer, topics)

    # Obtenez le mock de l'instance client
    mock_instance = mock_sio_client.return_value
    mock_instance.connected = True  # Simule un état connecté

    with caplog.at_level(logging.INFO):
        client.disconnect()

    # Vérifiez que disconnect a été appelé sur l'instance mockée
    mock_instance.disconnect.assert_called_once()
    assert f"Disconnected {consumer} from server." in caplog.text


def test_pubsub_client_disconnect_not_connected(mock_sio_client, caplog):
    """Teste la déconnexion quand le client n'est pas connecté."""
    consumer = "test_grace"
    topics = ["art"]
    client = PubSubClient(consumer, topics)

    # Obtenez le mock de l'instance client
    mock_instance = mock_sio_client.return_value
    mock_instance.connected = False  # Simule un état non connecté

    with caplog.at_level(logging.INFO):
        client.disconnect()

    # Vérifiez que disconnect n'a PAS été appelé sur l'instance mockée
    mock_instance.disconnect.assert_not_called()
    assert f"Disconnected {consumer} from server." not in caplog.text
