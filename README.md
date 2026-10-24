# ChatGPT UPI QR Tool (Standalone)

`session.json` → ChatGPT Plus India **plus-1-month-free** UPI QR

Pure-HTTP FastAPI tool (no browser). Ready for Render.

## What it does

1. Reads `accessToken` + cookies from session.json
2. POST ChatGPT checkout (`plus-1-month-free`, country IN)
3. Stripe init → elements → confirm (UPI QR variants)
4. ChatGPT approve poll
5. Extracts `upi://...` and builds QR PNG

## Local run

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080
```

Open http://127.0.0.1:8080

## API

`POST /generate`

```json
{
  "session": {
    "accessToken": "eyJhbGciOi...",
    "cookies": "oai-did=...; __Secure-next-auth.session-token=..."
  },
  "proxy": "http://user:pass@india-residential-proxy:port",
  "vpa": "test@oksbi",
  "approve_retries": 30,
  "approve_delay": 3.0
}
```

## Render deploy

1. Connect this repo on Render → New Web Service
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Or use `render.yaml` Blueprint

## Important

- India **residential proxy** strongly recommended
- Valid fresh session required
- Pure HTTP may fail if Stripe requires browser captcha tokens
- You are responsible for OpenAI ToS compliance

## Files

- `app.py` – FastAPI UI + API
- `upi_flow.py` – checkout → QR logic
- `stripe_tokens.py` – js_checksum helpers
- `requirements.txt`
- `render.yaml`
