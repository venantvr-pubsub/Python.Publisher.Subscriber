import uuid


class BaseMessage:
    def __init__(self, producer, payload, message_id=None):
        self.message_id = message_id or str(uuid.uuid4())
        self.producer = producer
        self.payload = payload

    def as_dict(self):
        return {
            "message_id": self.message_id,
            "producer": self.producer,
            "message": self.payload
        }


class OrderCreated(BaseMessage):
    def __init__(self, order_id, amount, producer):
        payload = {
            "order_id": order_id,
            "amount": amount
        }
        super().__init__(producer, payload)


class PaymentProcessed(BaseMessage):
    def __init__(self, payment_id, status, producer):
        payload = {
            "payment_id": payment_id,
            "status": status
        }
        super().__init__(producer, payload)
