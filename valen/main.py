"""Ponto de entrada da API VALEN (FastAPI + WebSocket).

Monta o Kernel no startup, expõe as rotas REST, o WebSocket de chat e uma
interface visual mínima (núcleo neural) em `/`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse

from valen import __version__
from valen.domains.observability import metrics
from valen.domains.observability.logging import get_logger
from valen.interfaces.api.routes import agents, health, memory
from valen.interfaces.api.websocket import chat as ws_chat
from valen.kernel import Kernel

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa o Kernel no startup e o disponibiliza via app.state."""
    app.state.kernel = Kernel()
    log.info(
        "valen_started",
        version=__version__,
        providers=app.state.kernel.providers.names,
        tools=app.state.kernel.tools.names,
    )
    yield
    log.info("valen_stopped")


app = FastAPI(title="VALEN", version=__version__, lifespan=lifespan)

app.include_router(health.router)
app.include_router(agents.router)
app.include_router(memory.router)
app.include_router(ws_chat.router)


_INDEX_HTML = """<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>VALEN · Núcleo Neural</title>
<style>
 body{background:#07090f;color:#cfe;font-family:ui-monospace,monospace;margin:0;padding:24px}
 h1{color:#6ef;letter-spacing:3px}
 .agents{display:flex;gap:16px;margin:16px 0}
 .a{border:1px solid #1b3;border-radius:8px;padding:10px 14px;background:#0c1320}
 .sym{font-size:22px}
 #log{height:48vh;overflow:auto;border:1px solid #123;border-radius:8px;padding:12px;background:#0a0e17}
 .u{color:#8df} .v{color:#9fe;margin:6px 0}
 input,select{background:#0c1320;color:#cfe;border:1px solid #245;border-radius:6px;padding:8px}
 input{width:60%} button{background:#0a6;color:#012;border:0;border-radius:6px;padding:8px 16px;cursor:pointer}
</style></head><body>
<h1>♛ VALEN — NÚCLEO NEURAL</h1>
<div class="agents">
 <div class="a"><span class="sym">♛</span> CEO</div>
 <div class="a"><span class="sym">⚒</span> Forge</div>
 <div class="a"><span class="sym">⬢</span> Nexus</div>
 <div class="a"><span class="sym">◇</span> Analyst</div>
</div>
<div id="log"></div>
<p>
 <select id="agent"><option>CEO</option><option>Forge</option><option>Nexus</option><option>Analyst</option></select>
 <input id="msg" placeholder="Fale com o agente..." autofocus>
 <button onclick="send()">Enviar</button>
</p>
<script>
 const log=document.getElementById('log');
 const proto=location.protocol==='https:'?'wss':'ws';
 const ws=new WebSocket(proto+'://'+location.host+'/ws/chat');
 function add(c,t){const d=document.createElement('div');d.className=c;d.textContent=t;log.appendChild(d);log.scrollTop=log.scrollHeight;}
 ws.onmessage=e=>{const m=JSON.parse(e.data);add('v',(m.symbol||'')+' '+(m.reply||m.error||''));};
 function send(){const a=document.getElementById('agent').value;const i=document.getElementById('msg');
  if(!i.value)return;add('u','› '+i.value);ws.send(JSON.stringify({agent:a,message:i.value}));i.value='';}
 document.getElementById('msg').addEventListener('keydown',e=>{if(e.key==='Enter')send();});
</script></body></html>"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index() -> str:
    """Interface visual mínima do núcleo neural."""
    return _INDEX_HTML


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    """Métricas no formato Prometheus."""
    payload, content_type = metrics.render()
    return Response(content=payload, media_type=content_type)
