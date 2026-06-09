"""FilesystemTool — leitura e escrita de arquivos.

Ações: read, write, append, list, mkdir, delete, exists, stat.
Confinada a uma raiz (`root`); qualquer caminho fora dela é rejeitado.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from valen.domains.tools.base import ToolBase, ToolContext, ToolError
from valen.domains.tools.sandbox import ExecutionTier

_TIER_BY_ACTION = {
    "read": ExecutionTier.READ_ONLY,
    "list": ExecutionTier.READ_ONLY,
    "exists": ExecutionTier.READ_ONLY,
    "stat": ExecutionTier.READ_ONLY,
    "write": ExecutionTier.REVERSIBLE,
    "append": ExecutionTier.REVERSIBLE,
    "mkdir": ExecutionTier.REVERSIBLE,
    "delete": ExecutionTier.DESTRUCTIVE,
}


class FilesystemTool(ToolBase):
    """Leitura/escrita de arquivos confinada a uma raiz."""

    name = "FilesystemTool"
    description = "Leitura e escrita de arquivos dentro de uma raiz controlada."
    required_permissions = {"read"}
    risk_level = "high"
    default_tier = ExecutionTier.REVERSIBLE

    def __init__(self, root: str | Path = ".", audit=None) -> None:
        super().__init__(audit=audit)
        self.root = Path(root).resolve()

    def tier_for(self, action: str, args: dict) -> ExecutionTier:
        return _TIER_BY_ACTION.get(action, ExecutionTier.SYSTEM_LEVEL)

    def _resolve(self, raw: str) -> Path:
        """Resolve um caminho garantindo que fique dentro da raiz."""
        if not raw:
            raise ToolError("argumento 'path' obrigatório")
        target = (self.root / raw).resolve()
        if target != self.root and self.root not in target.parents:
            raise ToolError(f"caminho fora da raiz permitida: {raw}")
        return target

    async def _run(self, action: str, args: dict, context: ToolContext) -> Any:
        path = args.get("path", "")

        if action == "read":
            target = self._resolve(path)
            if not target.is_file():
                raise ToolError(f"arquivo não encontrado: {path}")
            return target.read_text(encoding="utf-8")

        if action == "write":
            target = self._resolve(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            content = args.get("content", "")
            target.write_text(content, encoding="utf-8")
            return {"written": len(content), "path": str(target)}

        if action == "append":
            target = self._resolve(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            content = args.get("content", "")
            with target.open("a", encoding="utf-8") as fh:
                fh.write(content)
            return {"appended": len(content), "path": str(target)}

        if action == "list":
            target = self._resolve(path or ".")
            if not target.is_dir():
                raise ToolError(f"diretório não encontrado: {path}")
            return sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())

        if action == "mkdir":
            target = self._resolve(path)
            target.mkdir(parents=True, exist_ok=True)
            return {"created": str(target)}

        if action == "delete":
            target = self._resolve(path)
            if target.is_dir():
                raise ToolError("delete de diretório não suportado (use rm via Terminal)")
            if not target.exists():
                raise ToolError(f"arquivo não encontrado: {path}")
            target.unlink()
            return {"deleted": str(target)}

        if action == "exists":
            return self._resolve(path).exists()

        if action == "stat":
            target = self._resolve(path)
            if not target.exists():
                raise ToolError(f"caminho não encontrado: {path}")
            st = target.stat()
            return {"size": st.st_size, "is_dir": target.is_dir(), "mtime": st.st_mtime}

        raise ToolError(f"ação desconhecida: {action}")
