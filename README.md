# Master VPS Supervisor - Pro Edition 🚀

An incredibly powerful, AI-driven Linux VPS Administration Console powered by Google Gemini 3.1 Flash. Features a stunning glassmorphism Web Dashboard with native Farsi (RTL) support.

## ✨ Features
- **Conversational AI Admin**: Chat with your server. Ask for status, explain configurations, or request architectural changes.
- **Auto-Execution**: The AI proposes exact bash commands and safely queues them for your approval before execution over SSH.
- **Neural Memory**: Uses a sophisticated sliding-window memory algorithm to maintain short-term context, automatically extracting and compressing permanent infrastructure facts into a Long-Term Knowledge Base.
- **Failover APIs**: Provide a comma-separated list of Gemini API keys. If one fails (e.g. rate limit or 403), the engine instantly fails over to the next key.
- **Native Farsi Support**: Fully localized to Farsi with proper Right-To-Left UI mechanics.

## 🛠 Installation & Setup

1. **Clone the Repository**
2. **Install Requirements**:
   Ensure you have Python 3 installed.
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Dashboard**:
   Simply double-click the `Run_Dashboard.bat` file! 
   This will automatically bypass execution policies, start the Flask backend, and open your browser.

## 🔒 Security & Privacy (The Setup Wizard)
All sensitive data (VPS IPs, passwords, and API Keys) is strictly isolated and **NEVER** hardcoded. 
If the application does not find an `.env` file on launch, it will present a beautiful GUI **Setup Wizard** in your browser, asking for your credentials and safely generating the `.env` file locally. 

Because of `.gitignore`, your `.env` and `.ai_memory.json` files will never be uploaded to GitHub.
