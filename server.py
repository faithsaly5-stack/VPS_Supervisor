from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from ai_core import load_memory, generate_command, execute_and_verify, add_to_memory

app = Flask(__name__)

def is_env_valid():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    if not os.path.exists(env_path):
        return False
        
    config = {"VPS_IP": None, "VPS_USER": None, "VPS_PASS": None, "GEMINI_API_KEYS": None}
    with open(env_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                if key in config:
                    config[key] = val
                    
    return all(config.values())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/check_env")
def check_env():
    return jsonify({"valid": is_env_valid()})

@app.route("/api/setup", methods=["POST"])
def setup():
    data = request.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    with open(env_path, "w") as f:
        f.write(f"VPS_IP={data.get('ip', '')}\n")
        f.write(f"VPS_USER={data.get('user', 'root')}\n")
        f.write(f"VPS_PASS={data.get('password', '')}\n")
        f.write(f"GEMINI_API_KEYS={data.get('api_keys', '')}\n")
    return jsonify({"success": True})

@app.route("/api/history")
def history():
    return jsonify({"memory": load_memory()})

@app.route("/api/memory_status")
def memory_status():
    from ai_core import load_long_memory
    short_mem = load_memory()
    long_mem = load_long_memory()
    return jsonify({"short_memory_count": len(short_mem), "short_memory": short_mem, "long_memory": long_mem})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message")
    if not user_input:
        return jsonify({"error": "No message provided"})
        
    res = generate_command(user_input)
    if "error" in res:
        return jsonify({"error": res["error"]})
        
    if not res.get("command"):
        add_to_memory(user_input, res.get("explanation", ""))
        return jsonify({
            "type": "message",
            "explanation": res.get("explanation", ""),
            "user_msg": res["user_msg"]
        })
    else:
        return jsonify({
            "type": "approval",
            "command": res["command"],
            "explanation": res.get("explanation", ""),
            "user_msg": res["user_msg"]
        })

@app.route("/api/execute", methods=["POST"])
def execute():
    data = request.json
    command = data.get("command")
    user_msg = data.get("user_msg")
    
    if not command or not user_msg:
        return jsonify({"error": "Missing command or user message"})
        
    explanation = data.get("explanation", "")
    res = execute_and_verify(command, user_msg, explanation)
    return jsonify(res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
