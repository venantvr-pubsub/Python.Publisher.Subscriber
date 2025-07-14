// Génération d'un UUID v4
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    let r = Math.random() * 16 | 0,
      v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Classe de base pour les messages
class BaseMessage {
  constructor(producer, payload, message_id = null) {
    this.message_id = message_id || uuidv4();
    this.producer = producer;
    this.payload = payload;
  }

  toPayload(topic) {
    return {
      topic: topic,
      message_id: this.message_id,
      message: this.payload,
      producer: this.producer
    };
  }
}

// Exemple de classe métier spécifique
class TextMessage extends BaseMessage {
  constructor(text, producer) {
    super(producer, { text: text });
  }
}

let socket;

document.getElementById("connectBtn").addEventListener("click", () => {
  const consumer = document.getElementById("consumer").value;
  const topics = document.getElementById("topics").value
    .split(",").map(s => s.trim()).filter(s => s);

  socket = io({
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 2000
  });

  socket.on("connect", () => {
    console.log("Connected.");

    socket.emit("subscribe", {
      consumer,
      topics
    });

    console.log("Subscribed to topics:", topics);
  });

  socket.on("message", (data) => {
    console.log("Message received:", data);

    // Affichage plus complet :
    const item = document.createElement("li");
    item.className = "list-group-item";
    item.textContent = `[${data.topic}] [${data.message_id}] ${JSON.stringify(data.message)}`;
    document.getElementById("messages").appendChild(item);

    // Notify server of consumption
    socket.emit("consumed", {
      topic: data.topic,
      message_id: data.message_id,
      message: data.message,
      consumer: consumer
    });
  });

  // ADMIN EVENTS
  socket.on("new_client", (data) => {
    console.log("New client:", data);
    refreshClients();
  });

  socket.on("client_disconnected", (data) => {
    console.log("Client disconnected:", data);
    refreshClients();
  });

  socket.on("new_consumption", (data) => {
    console.log("New consumption:", data);
    refreshConsumptions();
  });
});

document.getElementById("pubBtn").addEventListener("click", () => {
  const topic = document.getElementById("pubTopic").value;
  const messageText = document.getElementById("pubMessage").value;
  const producer = document.getElementById("pubProducer").value || "frontend";

  // Utilise la classe métier
  const msg = new TextMessage(messageText, producer);

  const payload = msg.toPayload(topic);

  fetch("/publish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(r => r.json())
    .then(data => {
      console.log("Published:", data);
    });
});

function refreshClients() {
  fetch("/clients")
    .then(r => r.json())
    .then(clients => {
      const tbody = document.querySelector("#clientsTable tbody");
      tbody.innerHTML = "";
      clients.forEach(c => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${c.consumer}</td>
                          <td>${c.topic}</td>
                          <td>${new Date(c.connected_at * 1000).toLocaleString()}</td>`;
        tbody.appendChild(tr);
      });
    });
}

function refreshConsumptions() {
  fetch("/consumptions")
    .then(r => r.json())
    .then(consumptions => {
      const tbody = document.querySelector("#consTable tbody");
      tbody.innerHTML = "";
      consumptions.forEach(c => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${c.consumer}</td>
                          <td>${c.topic}</td>
                          <td>${JSON.stringify(c.message)}</td>
                          <td>${new Date(c.timestamp * 1000).toLocaleString()}</td>`;
        tbody.appendChild(tr);
      });
    });
}
