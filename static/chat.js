const chatBox = document.getElementById("chatBox");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  // Add user message
  const userDiv = document.createElement("div");
  userDiv.textContent = "🧑: " + text;
  chatBox.appendChild(userDiv);

  // Scroll to bottom
  chatBox.scrollTop = chatBox.scrollHeight;

  // Clear input
  input.value = "";

  // Send to backend
  fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  })
    .then(res => res.json())
    .then(data => {
      const botDiv = document.createElement("div");
      botDiv.textContent = "🤖: " + data.response;
      chatBox.appendChild(botDiv);
      chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => {
      const errDiv = document.createElement("div");
      errDiv.textContent = "⚠ Error: " + err.message;
      chatBox.appendChild(errDiv);
    });
}

sendBtn.addEventListener("click", sendMessage);

// ✅ Enter to send, Shift+Enter for new line
input.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault(); // Prevent newline
    sendMessage();
  }
});
