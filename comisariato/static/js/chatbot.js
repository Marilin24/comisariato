// Función principal para enviar mensajes
async function sendMessage() {
    const userInput = document.getElementById("userInput");
    const userMessage = userInput.value.trim();
    const chatHistory = document.getElementById("chat-history");

    if (!userMessage) {
        showMessage("Por favor escribe un mensaje", "error");
        return;
    }

    // Mostrar mensaje del usuario
    showMessage(userMessage, "user");

    // Mostrar que el bot está pensando
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

        // Eliminar el indicador "Pensando..."
        removeThinkingIndicator(thinkingId);

        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${await response.text()}`);
        }

        const data = await response.json();
        
        if (data.response) {
            showMessage(data.response, "bot");
        } else if (data.error) {
            showMessage(`Error: ${data.error}`, "error");
        } else {
            throw new Error("Respuesta inesperada del servidor");
        }
        
    } catch (error) {
        console.error("Error:", error);
        showMessage(`Error al comunicarse con el chatbot: ${error.message}`, "error");
    } finally {
        userInput.value = "";
        userInput.focus();
        scrollChatToBottom();
    }
}

// Mostrar mensaje en el chat
function showMessage(message, type) {
    const chatHistory = document.getElementById("chat-history");
    const messageDiv = document.createElement("div");
    
    messageDiv.className = `message ${type}`;
    
    if (type === "user") {
        messageDiv.innerHTML = `<strong>Tú:</strong> ${message}`;
    } else {
        // Formatear respuesta del bot (convertir \n en <br>)
        const formattedMessage = message.replace(/\n/g, '<br>');
        messageDiv.innerHTML = `<strong>Chatbot:</strong> ${formattedMessage}`;
    }
    
    chatHistory.appendChild(messageDiv);
    scrollChatToBottom();
}

// Mostrar indicador "Pensando..."
function showThinkingIndicator() {
    const chatHistory = document.getElementById("chat-history");
    const thinkingDiv = document.createElement("div");
    const thinkingId = "thinking-" + Date.now();
    
    thinkingDiv.id = thinkingId;
    thinkingDiv.className = "message thinking";
    thinkingDiv.innerHTML = '<strong>Chatbot:</strong> <em>Pensando...</em>';
    
    chatHistory.appendChild(thinkingDiv);
    scrollChatToBottom();
    
    return thinkingId;
}

// Eliminar indicador "Pensando..."
function removeThinkingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// Scroll automático al final del chat
function scrollChatToBottom() {
    const chatHistory = document.getElementById("chat-history");
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

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

// Enviar mensaje al presionar Enter
document.getElementById("userInput").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

// Ejemplos de preguntas para mostrar al usuario
function showExampleQuestions() {
    const examples = [
        "Cuál es el último pedido",
        "Muestra los productos más caros",
        "productos más baratos",
        "Lista de contactos recientes",
        "Qué métodos de pago aceptan",
        "Detalle del último pedido",
        "Productos con más stock",
        "Pedidos pendientes",
        "Total de clientes registrados"
    ];

    const examplesContainer = document.createElement("div");
    examplesContainer.className = "examples-container";
    examplesContainer.innerHTML = "<p>Prueba con:</p><ul>" + 
        examples.map(ex => `<li onclick="fillExample('${ex}')">${ex}</li>`).join("") + 
        "</ul>";

    document.getElementById("chat-container").appendChild(examplesContainer);
}

// Rellenar un ejemplo en el input
function fillExample(question) {
    document.getElementById("userInput").value = question;
    document.getElementById("userInput").focus();
}

// Mostrar ejemplos cuando la página cargue
window.onload = function() {
    showExampleQuestions();
};