import os
import json
import random
import threading
from ssh_client import SSHClient
from config import load_config
from google import genai
from google.genai import types

memory_lock = threading.Lock()

def load_memory():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mem_path = os.path.join(script_dir, ".ai_memory.json")
    with memory_lock:
        if os.path.exists(mem_path):
            try:
                with open(mem_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

def save_memory(memory):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mem_path = os.path.join(script_dir, ".ai_memory.json")
    with memory_lock:
        with open(mem_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4, ensure_ascii=False)

def load_long_memory():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mem_path = os.path.join(script_dir, ".ai_long_memory.txt")
    with memory_lock:
        if os.path.exists(mem_path):
            try:
                with open(mem_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                return ""
        return ""

def save_long_memory(text):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mem_path = os.path.join(script_dir, ".ai_long_memory.txt")
    with memory_lock:
        with open(mem_path, "w", encoding="utf-8") as f:
            f.write(text)

def add_to_memory(user_msg, ai_response):
    memory = load_memory()
    memory.append({"role": "user", "text": user_msg})
    memory.append({"role": "model", "text": ai_response})
    save_memory(memory)

def get_api_keys():
    config = load_config()
    content_keys = config.get("GEMINI_API_KEYS")
    if not content_keys:
        return []
        
    api_keys = [k.strip() for k in content_keys.split(",") if k.strip()]
    random.shuffle(api_keys)
    return api_keys

def generate_command(user_input):
    api_keys = get_api_keys()
    if not api_keys:
        return {"error": "API Keys not configured or invalid."}
        
    long_memory_text = load_long_memory()
    system_instruction = f"""You are a Linux VPS administrator. The user may ask you to perform a task on their server or just ask a conversational question. 
You MUST respond with a JSON object containing exactly two keys:
1. "command": The exact raw bash command to execute (prioritize non-interactive commands). IF the user is just asking a question and NO command execution is needed, leave this as an empty string "".
2. "explanation": A natural language explanation of the command, OR the answer to the user's question if no command is needed. If the user speaks Farsi, this MUST be in Farsi.

Output ONLY valid JSON. Do not wrap it in markdown formatting like ```json.

### LONG-TERM KNOWLEDGE BASE ###
{long_memory_text}"""
    
    memory = load_memory()
    contents = []
    for msg in memory:
        contents.append(
            types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["text"])])
        )
        
    new_user_msg = f"User Request: {user_input}"
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=new_user_msg)])
    )
    
    if contents:
        contents[0].parts[0].text = f"System Instruction: {system_instruction}\\n\\n" + contents[0].parts[0].text
        
    last_error = "Unknown error"
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=contents
            )
            output_text = response.text.strip()
            
            if output_text.startswith("```json"):
                output_text = output_text[7:]
            elif output_text.startswith("```"):
                output_text = output_text[3:]
            if output_text.endswith("```"):
                output_text = output_text[:-3]
            output_text = output_text.strip()
            
            try:
                parsed = json.loads(output_text)
                command_to_run = parsed.get("command", "").strip()
                explanation = parsed.get("explanation", "").strip()
            except json.JSONDecodeError:
                command_to_run = output_text
                explanation = "Failed to parse explanation, but received output."
            
            return {"command": command_to_run, "explanation": explanation, "user_msg": new_user_msg}
        except Exception as e:
            last_error = str(e)
            continue
            
    return {"error": last_error}

def execute_and_verify(command_to_run, user_msg, explanation=""):
    config = load_config()
    client = SSHClient(hostname=config.get("VPS_IP"), username=config.get("VPS_USER"))
    client.connect(password=config.get("VPS_PASS"))
    code, out, err = client.execute_command(command_to_run, interactive=False)
    client.close()
    
    memory = load_memory()
    memory.append({"role": "user", "text": user_msg})
    
    ai_context = f"Explanation: {explanation}\nCommand: {command_to_run}" if explanation else command_to_run
    memory.append({"role": "model", "text": ai_context})
    
    verify_input = f"Command Executed: {command_to_run}\\nExit Code: {code}\\nStdout: {out}\\nStderr: {err}"
    memory.append({"role": "user", "text": f"Execution Result: {verify_input}"})
    
    api_keys = get_api_keys()
    verify_output = "Unable to verify."
    if api_keys:
        verify_instruction = "You are a Linux VPS administrator. The user executed a command you suggested. Analyze the exit code, stdout, and stderr. Provide a short, natural language summary of whether the command succeeded and what the result means. If the user speaks Farsi, you MUST respond in Farsi."
        verify_contents = []
        for msg in memory:
            verify_contents.append(types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["text"])]))
            
        if verify_contents:
            verify_contents[0].parts[0].text = f"System Instruction: {verify_instruction}\\n\\n" + verify_contents[0].parts[0].text
            
        for key in api_keys:
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=verify_contents
                )
                verify_output = response.text.strip()
                break
            except Exception:
                continue
            
    memory.append({"role": "model", "text": verify_output})
    save_memory(memory)
    
    check_compaction()
    
    return {"verification": verify_output, "stdout": out, "stderr": err, "code": code}

def check_compaction():
    config = load_config()
    threshold = int(config.get("MEMORY_COMPACTION_THRESHOLD", 80))
    chunk_size = int(config.get("MEMORY_COMPACTION_CHUNK", 20))
    
    memory = load_memory()
    if len(memory) < threshold:
        return
        
    messages_to_compact = memory[:chunk_size]
    api_keys = get_api_keys()
    if not api_keys:
        return
        
    long_memory_text = load_long_memory()
    compaction_instruction = "You are a highly intelligent memory manager. You will be provided with the current LONG-TERM KNOWLEDGE BASE and a recent SHORT-TERM CONVERSATION. Your task is to extract any new, important, and persistent facts (like installed software, user preferences, configurations, architecture details) from the short-term conversation. Update the long-term knowledge base. DO NOT duplicate existing facts. Ignore transient or unimportant details. Output ONLY the updated long-term knowledge base as a clean, concise bulleted list."
    compaction_prompt = f"### CURRENT LONG-TERM KNOWLEDGE BASE ###\n{long_memory_text}\n\n### RECENT SHORT-TERM CONVERSATION ###\n" + json.dumps(messages_to_compact, indent=2)
    
    comp_contents = [types.Content(role="user", parts=[types.Part.from_text(text=compaction_instruction + "\n\n" + compaction_prompt)])]
    
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=comp_contents
            )
            new_long_memory = response.text.strip()
            if new_long_memory:
                if new_long_memory.startswith("```"):
                    new_long_memory = new_long_memory.split("\n", 1)[-1]
                if new_long_memory.endswith("```"):
                    new_long_memory = new_long_memory.rsplit("\n", 1)[0]
                    
                save_long_memory(new_long_memory.strip())
                current_memory = load_memory()
                save_memory(current_memory[chunk_size:])
            break
        except Exception:
            continue
