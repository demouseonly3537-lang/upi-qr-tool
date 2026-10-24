"""UPI QR Generator API - session.json to ChatGPT Plus India UPI QR"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from upi_flow import UpiQrGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="ChatGPT UPI QR Tool",
    description="session.json to UPI QR for ChatGPT Plus India (plus-1-month-free)",
    version="1.0.0",
)


class GenerateRequest(BaseModel):
    session: dict[str, Any] = Field(..., description="Full session.json object")
    proxy: Optional[str] = Field(None, description="India residential proxy")
    vpa: Optional[str] = Field("test@oksbi")
    approve_retries: int = Field(30, ge=1, le=200)
    approve_delay: float = Field(3.0, ge=1.0, le=15.0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html lang="hi"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ChatGPT UPI QR</title>
<style>
body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;background:#0b0f14;color:#e6edf3}
label{display:block;margin-top:14px;color:#9fb0c0}
input,textarea{width:100%;box-sizing:border-box;margin-top:6px;padding:10px;border-radius:8px;border:1px solid #30363d;background:#161b22;color:#e6edf3}
button{margin-top:18px;padding:12px 20px;border:0;border-radius:8px;background:#238636;color:#fff;font-weight:600;cursor:pointer}
#out{margin-top:24px;white-space:pre-wrap;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;font-size:0.85rem}
#qr{margin-top:16px;text-align:center}#qr img{max-width:280px;background:#fff;padding:12px;border-radius:8px}
.hint{color:#8b949e;font-size:0.85rem}
</style></head><body>
<h1>ChatGPT Plus · UPI QR</h1>
<p class="hint">Paste session.json (accessToken + cookies). India residential proxy recommended.</p>
<label>session.json</label>
<textarea id="session" rows="12" placeholder='{"accessToken":"...","cookies":"..."}'></textarea>
<label>India Proxy (optional)</label>
<input id="proxy" placeholder="http://user:pass@host:port"/>
<label>VPA (optional)</label>
<input id="vpa" value="test@oksbi"/>
<button id="btn" onclick="run()">Generate QR</button>
<div id="qr"></div><div id="out"></div>
<script>
async function run(){
  const btn=document.getElementById('btn'); const out=document.getElementById('out'); const qr=document.getElementById('qr');
  btn.disabled=true; out.textContent='Running...'; qr.innerHTML='';
  let session; try{session=JSON.parse(document.getElementById('session').value);}catch(e){out.textContent='Invalid JSON: '+e;btn.disabled=false;return;}
  const body={session, proxy:document.getElementById('proxy').value||null, vpa:document.getElementById('vpa').value||'test@oksbi', approve_retries:30, approve_delay:3};
  try{
    const r=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await r.json();
    out.textContent=JSON.stringify({ok:data.ok,upi_uri:data.upi_uri,qr_image_url:data.qr_image_url,checkout_session_id:data.checkout_session_id,error:data.error,logs:data.logs},null,2);
    if(data.qr_png_b64){qr.innerHTML='<img alt="UPI QR" src="data:image/png;base64,'+data.qr_png_b64+'"/><p class="hint">Scan with PhonePe / GPay / Paytm</p>';}
  }catch(e){out.textContent=String(e);} btn.disabled=false;
}
</script></body></html>"""


@app.post("/generate")
async def generate(req: GenerateRequest):
    gen = UpiQrGenerator(session=req.session, proxy=req.proxy, vpa=req.vpa)
    result = gen.run(approve_retries=req.approve_retries, approve_delay=req.approve_delay)
    return JSONResponse(result)


@app.post("/generate-file")
async def generate_file(
    file: UploadFile = File(...),
    proxy: Optional[str] = Form(None),
    vpa: Optional[str] = Form("test@oksbi"),
):
    raw = await file.read()
    try:
        session = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise HTTPException(400, f"Invalid session.json: {e}")
    gen = UpiQrGenerator(session=session, proxy=proxy, vpa=vpa or "test@oksbi")
    return JSONResponse(gen.run())


@app.post("/generate-png")
async def generate_png(req: GenerateRequest):
    gen = UpiQrGenerator(session=req.session, proxy=req.proxy, vpa=req.vpa)
    result = gen.run(approve_retries=req.approve_retries, approve_delay=req.approve_delay)
    if not result.get("qr_png_b64"):
        raise HTTPException(422, detail={"error": result.get("error") or "QR not generated", "logs": result.get("logs")})
    return Response(content=base64.b64decode(result["qr_png_b64"]), media_type="image/png")
