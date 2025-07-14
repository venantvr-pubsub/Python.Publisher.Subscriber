from lib.pubsub_client import PubSubClient


def sport_handler(message):
    if "goal" in message.lower():
        print("[sport handler] GO TEAM!")
    else:
        print(f"[sport handler] Just another message: {message}")


def finance_handler(message):
    if "stock" in message.lower():
        fake_price = 100 * 1.1
        print(f"[finance handler] Calculating new stock price... {fake_price}")
    else:
        print(f"[finance handler] Finance info: {message}")


if __name__ == "__main__":
    client = PubSubClient(
        url="http://localhost:5000",
        consumer="alice",
        topics=["sport", "finance"]
    )

    client.register_handler("sport", sport_handler)
    client.register_handler("finance", finance_handler)

    client.start()
