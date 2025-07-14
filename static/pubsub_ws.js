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
        const item = document.createElement("li");
        item.className = "list-group-item";
        item.textContent = `[${data.topic}] ${data.message}`;
        document.getElementById("messages").appendChild(item);

        // Notify server of consumption
        socket.emit("consumed", {
          topic: data.topic,
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
      const message = document.getElementById("pubMessage").value;

      fetch("/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, message })
      }).then(r => r.json())
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
                            <td>${c.message}</td>
                            <td>${new Date(c.timestamp * 1000).toLocaleString()}</td>`;
            tbody.appendChild(tr);
          });
        });
    }