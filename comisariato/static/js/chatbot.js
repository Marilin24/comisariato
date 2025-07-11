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
async function sendMessage() {
    const userInput = document.getElementById("userInput");
    const userMessage = userInput.value.trim();

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

        // CORREGIDO: antes decía data.response, ahora es data.respuesta_bot
        if (data.respuesta_bot) {
            showMessage(data.respuesta_bot, "bot");
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

// Insertar ejemplos
function showExampleQuestions() {
    const examples = [
        "Cuál es el último pedido",
        "Muestra los productos más caros",
        "Productos más baratos",
        "Lista de contactos recientes",
        "Qué métodos de pago aceptan",
        "Detalle del último pedido",
        "Productos con más stock",
        "Pedidos pendientes",
        "Total de clientes registrados"
    ];

    const container = document.createElement("div");
    container.className = "examples-container";
    container.innerHTML = "<p>Prueba con:</p><ul>" + 
        examples.map(q => `<li onclick="fillExample('${q}')">${q}</li>`).join("") +
        "</ul>";

    const chatContainer = document.getElementById("chat-container");
    if (chatContainer) chatContainer.appendChild(container);
}

// Rellenar input con ejemplo
function fillExample(text) {
    const input = document.getElementById("userInput");
    input.value = text;
    input.focus();
}

// Mostrar chatbot flotante
function mostrarChatbot() {
    const chatbot = document.getElementById("chatbot-container");
    if(chatbot) chatbot.style.display = "block";
}

// Ocultar chatbot flotante
function cerrarChatbot() {
    const chatbot = document.getElementById("chatbot-container");
    if(chatbot) chatbot.style.display = "none";
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
