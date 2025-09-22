// document.addEventListener("DOMContentLoaded", () => {
//   const ws = new WebSocket(
//     "ws://" +
//       window.location.host +
//       "/ws/chat/" +
//       encodeURIComponent(conversationId) +
//       "/"
//   );

//   ws.onopen = () => console.log("Connected to chat");

//   ws.onmessage = (event) => {
//     const data = JSON.parse(event.data);
//     if (data.type === "historical_messages") {
//       data.messages.forEach(displayMessage);
//     } else if (data.type === "message") {
//       displayMessage(data.message);
//     }
//   };

//   function displayMessage(message) {
//     const messageDiv = document.createElement("div");
//     messageDiv.textContent = `${message.user}: ${message.content}`;
//     document.getElementById("messages").appendChild(messageDiv);
//   }

//   document.getElementById("message-form").onsubmit = (e) => {
//     e.preventDefault();
//     const content = document.getElementById("message-content").value;
//     if (content.trim()) {
//       ws.send(JSON.stringify({ type: "message", content }));
//       document.getElementById("message-content").value = "";
//     }
//     return false;
//   };
// });
