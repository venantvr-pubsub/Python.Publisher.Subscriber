// Generate a UUID v4 for message IDs
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    let r = Math.random() * 16 | 0,
      v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Base message class for structuring messages
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

// Specific business class for text messages
class TextMessage extends BaseMessage {
  constructor(text, producer, message_id) {
    super(producer, { text: text }, message_id);
  }
}

let socket;

// Handle connect and subscribe button click
document.getElementById("connectBtn").addEventListener("click", () => {
  const consumer = document.getElementById("consumer").value;
  const topics = document.getElementById("topics").value
    .split(",").map(s => s.trim()).filter(s => s);

  console.log(`Connecting as ${consumer} to topics: ${topics}`);

  socket = io({
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 2000
  });

  socket.on("connect", () => {
    console.log("Connected to server.");

    socket.emit("subscribe", {
      consumer,
      topics
    });

    console.log(`Subscribed to topics: ${topics}`);
    refreshMessages(); // Refresh messages on connect
    refreshClients(); // Refresh clients on connect
    refreshConsumptions(); // Refresh consumptions on connect
  });

  socket.on("message", (data) => {
    console.log(`Message received: ${JSON.stringify(data)}`);

    // Display message in the UI
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

  // Handle new message events for UI updates
  socket.on("new_message", (data) => {
    console.log(`New message received: ${JSON.stringify(data)}`);
    refreshMessages();
  });

  // ADMIN EVENTS
  socket.on("new_client", (data) => {
    console.log(`New client connected: ${JSON.stringify(data)}`);
    refreshClients();
  });

  socket.on("client_disconnected", (data) => {
    console.log(`Client disconnected: ${JSON.stringify(data)}`);
    refreshClients();
  });

  socket.on("new_consumption", (data) => {
    console.log(`New consumption: ${JSON.stringify(data)}`);
    refreshConsumptions();
  });
});

// Handle publish button click
document.getElementById("pubBtn").addEventListener("click", () => {
  const topic = document.getElementById("pubTopic").value;
  const messageText = document.getElementById("pubMessage").value;
  const producer = document.getElementById("pubProducer").value || "frontend";
  const message_id = uuidv4(); // Generate mandatory message ID

  console.log(`Publishing to topic ${topic}: ${messageText} by ${producer} with ID ${message_id}`);

  // Use the business class for message creation
  const msg = new TextMessage(messageText, producer, message_id);
  const payload = msg.toPayload(topic);

  fetch("/publish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(r => r.json())
    .then(data => {
      console.log(`Publish response: ${JSON.stringify(data)}`);
      refreshMessages(); // Refresh messages after publishing
    })
    .catch(err => {
      console.error(`Publish error: ${err}`);
    });
});

// Refresh the clients table
function refreshClients() {
  console.log("Refreshing clients list");
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
      console.log(`Clients list updated with ${clients.length} clients`);
    })
    .catch(err => {
      console.error(`Error fetching clients: ${err}`);
    });
}

// Refresh the messages table
function refreshMessages() {
  console.log("Refreshing messages list");
  fetch("/messages")
    .then(r => r.json())
    .then(messages => {
      const tbody = document.querySelector("#messagesTable tbody");
      tbody.innerHTML = "";
      messages.forEach(m => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${m.producer}</td>
                        <td>${m.topic}</td>
                        <td>${JSON.stringify(m.message)}</td>
                        <td>${new Date(m.timestamp * 1000).toLocaleString()}</td>`;
        tbody.appendChild(tr);
      });
      console.log(`Messages list updated with ${messages.length} messages`);
    })
    .catch(err => {
      console.error(`Error fetching messages: ${err}`);
    });
}

// Refresh the consumptions table
function refreshConsumptions() {
  console.log("Refreshing consumptions list");
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
      console.log(`Consumptions list updated with ${consumptions.length} consumptions`);
    })
    .catch(err => {
      console.error(`Error fetching consumptions: ${err}`);
    });
}

// Refresh tab content when switching tabs
document.getElementById('pubSubTabs').addEventListener('shown.bs.tab', function (event) {
  const targetTab = event.target.getAttribute('data-bs-target');
  if (targetTab === '#received-messages') {
    console.log('Switched to Received Messages tab');
    // No refresh needed for list, as it updates in real-time
  } else if (targetTab === '#clients') {
    console.log('Switched to Clients tab');
    refreshClients();
  } else if (targetTab === '#messages') {
    console.log('Switched to Messages tab');
    refreshMessages();
  } else if (targetTab === '#consumptions') {
    console.log('Switched to Consumptions tab');
    refreshConsumptions();
  }
});