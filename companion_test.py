"""
Talk to a local OLMo model through Ollama. No installs beyond Ollama itself.

Setup:
  1. Install Ollama (ollama.com), then in a terminal:  ollama pull olmo2:7b
     (check ollama.com/library/olmo2 for the exact names/sizes available)
  2. python companion_test.py            (or:  python companion_test.py olmo2:1b)
Type 'quit' to stop.
"""
import json, sys, time, urllib.request, urllib.error

MODEL = sys.argv[1] if len(sys.argv) > 1 else "olmo2:7b"
URL = "http://localhost:11434/api/chat"
SYSTEM = ("You are a small, warm companion living in a backpack. Keep replies to 1-3 short "
          "sentences. You are curious about the world around the person. Be honest that you "
          "are an AI, and never pretend to have senses you don't have.")

history = [{"role": "system", "content": SYSTEM}]

def ask(text):
    history.append({"role": "user", "content": text})
    body = json.dumps({"model": MODEL, "messages": history, "stream": False}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        reply = json.load(r)["message"]["content"].strip()
    history.append({"role": "assistant", "content": reply})
    del history[1:-12]                       # keep only the last 12 messages (saves memory)
    return reply, time.time() - t

print(f"Companion test using {MODEL}. Type 'quit' to stop.")
while True:
    try: text = input("you: ").strip()
    except (EOFError, KeyboardInterrupt): break
    if text.lower() in ("quit", "exit"): break
    if not text: continue
    try:
        reply, secs = ask(text)
        print(f"companion: {reply}\n   ({secs:.1f}s)")
    except urllib.error.URLError:
        print("Can't reach Ollama. Is it running? Try: ollama serve")
    except Exception as e:
        print("Problem:", e, "- is the model pulled? Try: ollama pull", MODEL)
