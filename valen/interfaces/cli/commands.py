"""CLI VALEN (typer + rich) — status, chat e operações.

Uso:
    uv run valen status
    uv run valen agents
    uv run valen chat CEO "olá, meu rei?"
    uv run valen serve
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from valen import __version__
from valen.kernel import Kernel

app = typer.Typer(help="VALEN — CLI de operações.", no_args_is_help=True)
console = Console()


@app.command()
def version() -> None:
    """Mostra a versão do VALEN."""
    console.print(f"[bold cyan]VALEN[/] v{__version__}")


@app.command()
def status() -> None:
    """Mostra agentes, tools e providers ativos."""
    kernel = Kernel()
    console.print(f"[bold cyan]VALEN[/] v{__version__} · env={kernel.settings.valen_env}")
    console.print(f"providers: [green]{', '.join(kernel.providers.names)}[/]")
    console.print(f"tools: [green]{', '.join(kernel.tools.names)}[/]")


@app.command()
def agents() -> None:
    """Lista os 4 agentes."""
    kernel = Kernel()
    table = Table("Símbolo", "ID", "Papel", "Sandbox", "Tools")
    for a in kernel.orchestrator.list_agents():
        table.add_row(a.symbol, a.id, a.role, a.sandbox_mode, ", ".join(a.tools))
    console.print(table)


@app.command()
def chat(agent: str, message: str) -> None:
    """Conversa com um agente."""
    kernel = Kernel()

    async def _run() -> dict:
        return await kernel.orchestrator.chat(agent, message)

    res = asyncio.run(_run())
    console.print(f"[bold magenta]{res['symbol']} {res['agent']}[/]: {res['reply']}")


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Sobe a API FastAPI (uvicorn)."""
    import uvicorn

    uvicorn.run("valen.main:app", host=host, port=port)


if __name__ == "__main__":
    app()
