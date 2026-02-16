let currentChatId = null;

const API = "http://127.0.0.1:8000";


// Load history on startup
window.onload = function () {
    loadHistory();
};


// Create new chat
function newChat() {

    currentChatId = "chat_" + Date.now();

    document.getElementById("chatbox").innerHTML = "";

    loadHistory();
}


// Send message
async function sendMessage() {

    const input = document.getElementById("message");

    const message = input.value;

    if (!message) return;


    // Show user message
    addMessage("You", message);

    input.value = "";


    const response = await fetch(API + "/chat", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            chat_id: currentChatId,
            message: message
        })

    });


    const data = await response.json();

    console.log(data); // debug


    addMessage("Bot", data.answer);


    loadHistory();
}


// Add message to UI
function addMessage(sender, text) {

    const chatbox = document.getElementById("chatbox");

    const div = document.createElement("div");

    div.innerHTML = "<b>" + sender + ":</b> " + text;

    chatbox.appendChild(div);

}


// Load chat history list
async function loadHistory() {

    const res = await fetch(API + "/history");

    const data = await res.json();

    const chatList = document.getElementById("chatList");

    chatList.innerHTML = "";


    data.forEach(chat => {

        const div = document.createElement("div");

        div.className = "chatItem";

        div.innerText = chat.title;

        div.onclick = () => loadChat(chat.chat_id);

        chatList.appendChild(div);

    });

}


// Load specific chat
async function loadChat(chat_id) {

    currentChatId = chat_id;

    const res = await fetch(API + "/chat/" + chat_id);

    const messages = await res.json();

    const chatbox = document.getElementById("chatbox");

    chatbox.innerHTML = "";


    messages.forEach(msg => {

        addMessage("You", msg.user_message);

        addMessage("Bot", msg.bot_response);

    });

}
