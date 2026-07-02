const toggleBtn = document.getElementById('toggleBtn');
const sidebar = document.getElementById('sidebar');

toggleBtn.addEventListener('click', () => {
  sidebar.classList.toggle('hidden');
  toggleBtn.classList.toggle('sidebar-hidden'); 
});

document.addEventListener("DOMContentLoaded", () => {
    const chatInput = document.getElementById("chat-input");
    const mainContent = document.getElementById("main-content");

    if (chatInput && mainContent) {
        chatInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                const textValue = chatInput.value.trim();
                
                if (textValue !== "") {
                    mainContent.classList.add("has-searched");
                    console.log("Submitted query:", textValue);

                    // 1. Pack the variable into an object
                    const projectData = {
                        chatInput: textValue
                    };

                    // 2. Send the data to Python backend application
                    fetch('http://localhost:5000/save-input', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(projectData)
                    })
                    .then(response => response.json())
                    .then(data => console.log('Successfully saved to JSON via Python:', data))
                    .catch(error => console.error('Error sending data:', error));
                }
            }
        });
    }
});
