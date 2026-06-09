"""WebSocket de chat com os agentes (núcleo neural em tempo real).

Protocolo: cliente envia JSON {"agent": "CEO", "message": "..."}; servidor
responde {"agent", "symbol", "reply", "model"}. Erros viram {"error": "..."}.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from valen.domains.agents.services.orchestration import AgentNotFound
from valen.domains.observability.logging import get_logger

router = APIRouter()
log = get_logger(__name__)


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket) -> None:
    """Loop de chat: uma mensagem do usuário → uma resposta do agente."""
    kernel = websocket.app.state.kernel
    await websocket.accept()
    await websocket.send_json(
        {"agent": "CEO", "symbol": "♛", "reply": "Sistemas online, meu rei."}
    )
    try:
        while True:
            data = await websocket.receive_json()
            agent_id = data.get("agent", "CEO")
            message = data.get("message", "")
            if not message:
                await websocket.send_json({"error": "mensagem vazia"})
                continue
            try:
                res = await kernel.orchestrator.chat(agent_id, message)
                await websocket.send_json(res)
            except AgentNotFound as exc:
                await websocket.send_json({"error": str(exc)})
            except Exception as exc:  # noqa: BLE001
                log.error("ws_chat_error", error=str(exc))
                await websocket.send_json({"error": f"falha interna: {exc}"})
    except WebSocketDisconnect:
        log.info("ws_chat_disconnect")
