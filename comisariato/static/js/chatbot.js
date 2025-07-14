// Obtener cookie CSRF para Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Enviar mensaje al backend
async function sendMessage(message = null) {
    const userInput = document.getElementById("userInput");
    const userMessage = message || userInput.value.trim();

    if (!userMessage) {
        showMessage("Por favor escribe un mensaje", "error");
        return;
    }

    showMessage(userMessage, "user");
    const thinkingId = showThinkingIndicator();

    try {
        const response = await fetch("/api/chatbot/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ message: userMessage }),
        });

        removeThinkingIndicator(thinkingId);

        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${await response.text()}`);
        }

        const data = await response.json();

        if (data.respuesta_bot) {
            showMessage(data.respuesta_bot, "bot");
            if (data.sugerencias && Array.isArray(data.sugerencias)) {
                showSuggestions(data.sugerencias);
            }
        } else if (data.error) {
            showMessage(`⚠️ ${data.error}`, "error");
        } else {
            throw new Error("Respuesta inesperada del servidor");
        }

    } catch (error) {
        console.error("Error:", error);
        removeThinkingIndicator(thinkingId);
        showMessage(`Error de conexión: ${error.message}`, "error");
    } finally {
        userInput.value = "";
        userInput.focus();
    }
}

// Mostrar mensaje en pantalla
function showMessage(message, type) {
    const chatHistory = document.getElementById("chat-history");
    const div = document.createElement("div");

    div.className = `message ${type}`;
    const formatted = message.replace(/\n/g, "<br>");

    div.innerHTML = type === "user"
        ? `<strong>Tú:</strong> ${formatted}`
        : `<strong>Chatbot:</strong> ${formatted}`;

    chatHistory.appendChild(div);
    scrollChatToBottom();
}

// Mostrar "Pensando..."
function showThinkingIndicator() {
    const chatHistory = document.getElementById("chat-history");
    const div = document.createElement("div");
    const id = "thinking-" + Date.now();

    div.id = id;
    div.className = "message thinking";
    div.innerHTML = "<strong>Chatbot:</strong> <em>Pensando...</em>";

    chatHistory.appendChild(div);
    scrollChatToBottom();
    return id;
}

// Quitar "Pensando..."
function removeThinkingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Auto scroll
function scrollChatToBottom() {
    const chatHistory = document.getElementById("chat-history");
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Mostrar sugerencias después de la respuesta
function showSuggestions(suggestions) {
    const chatHistory = document.getElementById("chat-history");

    const container = document.createElement("div");
    container.className = "message bot";
    container.innerHTML = "<strong>¿También podrías preguntar?:</strong><ul style='padding-left: 20px;'>";

    suggestions.forEach(s => {
        container.innerHTML += `<li style="cursor:pointer; color:#1565c0;" onclick="sendMessage('${s.replace(/'/g, "\\'")}')">${s}</li>`;
    });

    container.innerHTML += "</ul>";
    chatHistory.appendChild(container);
    scrollChatToBottom();
}

// Mostrar chatbot flotante
function mostrarChatbot() {
    const chatbot = document.getElementById("chatbot-container");
    if(chatbot) chatbot.style.display = "flex";
}

// Ocultar chatbot flotante
function cerrarChatbot() {
    const chatbot = document.getElementById("chatbot-container");
    if(chatbot) chatbot.style.display = "none";
}

// Cargar preguntas de ejemplo iniciales
function showExampleQuestions() {
    const examples = [
        "¿Cuál es el último pedido?",
        "¿Qué productos tienen más stock?",
        "¿Cuántos pedidos se hicieron hoy?"
    ];

    const container = document.createElement("div");
    container.className = "message bot";
    container.innerHTML = "<strong>Ejemplos para comenzar:</strong><ul style='padding-left: 20px;'>";

    examples.forEach(q => {
        container.innerHTML += `<li style="cursor:pointer; color:#1565c0;" onclick="sendMessage('${q.replace(/'/g, "\\'")}')">${q}</li>`;
    });

    container.innerHTML += "</ul>";
    document.getElementById("chat-history").appendChild(container);
    scrollChatToBottom();
}

// Eventos cuando se carga la página
document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("userInput");
    if (input) {
        input.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    showExampleQuestions();
});
