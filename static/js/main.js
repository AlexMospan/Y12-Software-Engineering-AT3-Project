const toggleBtn = document.getElementById('toggleBtn');
const sidebar = document.getElementById('sidebar');

if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('hidden');
      toggleBtn.classList.toggle('sidebar-hidden'); 
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const chatInput = document.getElementById("chat-input");
    const mainContent = document.getElementById("main-content");
    const messagesContainer = document.getElementById("chat-messages");
    const recentListContainer = document.getElementById("recent-list-container");
    const newChatBtn = document.getElementById("new-chat-sidebar-btn");

    // Tracks which conversation thread is currently viewed on screen
    let currentChatId = null;

    function appendMessage(text, sender) {
        if (!messagesContainer) return;

        const wrapper = document.createElement("div");
        wrapper.classList.add("message-wrapper", sender);

        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble");
        bubble.textContent = text;

        wrapper.appendChild(bubble);
        messagesContainer.appendChild(wrapper);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Loads a selected thread's database message history onto browser screen
    async function loadChatThread(chatId) {
        currentChatId = chatId;
        if (!messagesContainer || !mainContent) return;

        messagesContainer.innerHTML = "";
        mainContent.classList.add("has-searched");

        try {
            const response = await fetch(`/chat/${chatId}/messages`);
            const data = await response.json();
            
            if (data.status === "success") {
                data.messages.forEach(msg => {
                    appendMessage(msg.content, msg.sender);
                });
                
                // Highlight the active conversation element in the sidebar list
                document.querySelectorAll(".recent-item-btn").forEach(btn => {
                    btn.classList.toggle("active-btn", btn.getAttribute("data-chat-id") == chatId);
                });
            }
        } catch (error) {
            console.error("Error fetching history frames:", error);
        }
    }

    // Handles user selection
    if (recentListContainer) {
        recentListContainer.addEventListener("click", (event) => {
            const targetButton = event.target.closest(".recent-item-btn");
            if (targetButton) {
                const chatId = targetButton.getAttribute("data-chat-id");
                loadChatThread(chatId);
            }
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener("click", () => {
            currentChatId = null;
            if (messagesContainer) messagesContainer.innerHTML = "";
            if (mainContent) mainContent.classList.remove("has-searched");
            document.querySelectorAll(".recent-item-btn").forEach(btn => btn.classList.remove("active-btn"));
            chatInput.focus();
        });
    }

    if (chatInput && mainContent) {
        chatInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault(); 
                
                const textValue = chatInput.value.trim();
                if (textValue !== "") {
                    mainContent.classList.add("has-searched");
                    appendMessage(textValue, "user");
                    chatInput.value = "";

                    const projectData = {
                        chatInput: textValue,
                        chatId: currentChatId
                    };

                    fetch('http://localhost:5000/save-input', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(projectData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === "success") {
                            if (!currentChatId && data.chat_id) {
                                currentChatId = data.chat_id;
                                const newBtn = document.createElement("button");
                                newBtn.classList.add("recent-item-btn", "active-btn");
                                newBtn.setAttribute("data-chat-id", data.chat_id);
                                newBtn.textContent = textValue.substring(0, 20) || "New Chat";
                                if (recentListContainer) {
                                    recentListContainer.insertBefore(newBtn, recentListContainer.firstChild);
                                }
                            }
                            
                            if (data.reply) {
                                appendMessage(data.reply, "bot");
                            }
                        }
                    })
                    .catch(error => console.error('Error handling interaction loop:', error));
                }
            }
        });
    }
});