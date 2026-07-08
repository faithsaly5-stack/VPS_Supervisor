document.addEventListener("DOMContentLoaded", () => {
    const setupWizard = document.getElementById("setup-wizard");
    const appContainer = document.getElementById("app-container");
    const chatContainer = document.getElementById("chat-container");
    const messagesDiv = document.getElementById("messages");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const approvalModal = document.getElementById("approval-modal");
    const proposedCommandEl = document.getElementById("proposed-command");
    
    let pendingExecution = null;

    // Check Environment
    fetch("/api/check_env")
        .then(r => r.json())
        .then(data => {
            if (data.valid) {
                appContainer.classList.remove("hidden");
                loadHistory();
            } else {
                setupWizard.classList.remove("hidden");
            }
        });

    // Setup Wizard Save
    document.getElementById("save-setup-btn").addEventListener("click", () => {
        const ip = document.getElementById("setup-ip").value;
        const user = document.getElementById("setup-user").value;
        const password = document.getElementById("setup-pass").value;
        const api_keys = document.getElementById("setup-keys").value;

        fetch("/api/setup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ip, user, password, api_keys })
        }).then(() => {
            setupWizard.classList.add("hidden");
            appContainer.classList.remove("hidden");
            loadHistory();
        });
    });

    function addMessage(role, text, isCode = false) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role}`;
        msgDiv.setAttribute("dir", "auto"); // Vital for Farsi RTL
        
        const bubble = document.createElement("div");
        bubble.className = "bubble";
        
        if (isCode) {
            const pre = document.createElement("pre");
            pre.textContent = text;
            pre.setAttribute("dir", "ltr");
            bubble.appendChild(pre);
        } else {
            // Use marked.js for full markdown parsing
            bubble.innerHTML = marked.parse(text);
        }

        msgDiv.appendChild(bubble);
        messagesDiv.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function loadHistory() {
        fetch("/api/history")
            .then(r => r.json())
            .then(data => {
                if(data.memory) {
                    data.memory.forEach(msg => {
                        // Very rough heuristic to decide if it's code
                        const isCode = msg.role === 'model' && msg.text.match(/^[a-z0-9_-]+ /i);
                        addMessage(msg.role, msg.text, isCode);
                    });
                }
            });
    }

    function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        userInput.value = "";
        addMessage("user", text);

        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                addMessage("system", "Error: " + data.error);
                return;
            }
            if (data.type === "message") {
                if (data.explanation) {
                    addMessage("model", data.explanation);
                }
            } else if (data.type === "approval") {
                pendingExecution = data;
                
                if (data.explanation) {
                    addMessage("model", data.explanation);
                }
                
                proposedCommandEl.textContent = data.command;
                approvalModal.classList.remove("hidden");
            }
        });
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    document.getElementById("approve-btn").addEventListener("click", () => {
        approvalModal.classList.add("hidden");
        if (!pendingExecution) return;

        const cmd = pendingExecution.command;
        addMessage("model", cmd, true);

        fetch("/api/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(pendingExecution)
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                addMessage("system", data.error);
            } else {
                let out = "";
                if(data.stdout) out += data.stdout + "\n";
                if(data.stderr) out += data.stderr + "\n";
                if(out) addMessage("system", "خروجی:\n" + out, true);
                
                addMessage("model", data.verification);
            }
            pendingExecution = null;
        });
    });

    document.getElementById("reject-btn").addEventListener("click", () => {
        approvalModal.classList.add("hidden");
        addMessage("system", "اجرای دستور توسط کاربر لغو شد.");
        pendingExecution = null;
    });
});

    const viewMemoryBtn = document.getElementById("view-memory-btn");
    const closeMemoryBtn = document.getElementById("close-memory-btn");
    const memoryModal = document.getElementById("memory-modal");
    
    viewMemoryBtn.addEventListener("click", () => {
        fetch("/api/memory_status")
            .then(r => r.json())
            .then(data => {
                document.getElementById("long-memory-view").textContent = data.long_memory || "هنوز حافظه بلندمدتی فشرده نشده است.";
                document.getElementById("short-memory-count").textContent = data.short_memory_count;
                document.getElementById("short-memory-view").textContent = JSON.stringify(data.short_memory, null, 2) || "حافظه کوتاه‌مدت خالی است.";
                memoryModal.classList.remove("hidden");
            });
    });

    closeMemoryBtn.addEventListener("click", () => {
        memoryModal.classList.add("hidden");
    });
    
    const shutdownBtn = document.getElementById("shutdown-btn");
    if (shutdownBtn) {
        shutdownBtn.addEventListener("click", () => {
            if (confirm("آیا مطمئن هستید که می‌خواهید ارتباط را قطع و سرور را خاموش کنید؟")) {
                fetch("/api/shutdown", { method: "POST" })
                    .then(() => {
                        document.body.innerHTML = "<div style='text-align: center; margin-top: 20%; color: white; font-family: Tahoma;'><h2>ارتباط با موفقیت قطع شد</h2><p>می‌توانید این پنجره را ببندید.</p></div>";
                    })
                    .catch(() => {
                        document.body.innerHTML = "<div style='text-align: center; margin-top: 20%; color: white; font-family: Tahoma;'><h2>ارتباط با موفقیت قطع شد</h2><p>می‌توانید این پنجره را ببندید.</p></div>";
                    });
            }
        });
    }
