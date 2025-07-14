from dataclasses import dataclass, asdict
from uuid import uuid4


@dataclass
class PubSubMessage:
    topic: str
    message_id: str
    message: dict
    producer: str

    @staticmethod
    def new(topic: str, message: dict, producer: str) -> "PubSubMessage":
        return PubSubMessage(
            topic=topic,
            message_id=str(uuid4()),
            message=message,
            producer=producer
        )

    def to_dict(self) -> dict:
        return asdict(self)
