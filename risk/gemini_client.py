
import json, os, time, random, urllib.request

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
API_KEY_ENV = "GEMINI_API_KEY"

def ask_gemini(prompt: str, retries: int = 3, timeout: int = 40) -> str:
    body = {"contents":[{"parts":[{"text": prompt}]}]}
    data = json.dumps(body).encode()
    for i in range(retries):
        try:
            req = urllib.request.Request(GEMINI_ENDPOINT, data=data, method="POST")
            req.add_header("x-goog-api-key", os.environ[API_KEY_ENV])
            req.add_header("Content-Type","application/json")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
            text = "".join(
                p.get("text","")
                for c in resp.get("candidates", [])
                for p in c.get("content", {}).get("parts", [])
            )
            return text.strip() or "No response."
        except Exception:
            time.sleep(min((2**i) + random.random(), 10))
    return "Gemini unavailable."
