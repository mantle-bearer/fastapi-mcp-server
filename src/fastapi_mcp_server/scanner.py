"""AST-based zero-execution project scanner to discover FastAPI apps, APIRouters, and Pydantic models."""

import ast
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "node_modules",
    ".idea",
    ".vscode",
}


def discover_project(project_dir: str | None = None) -> dict[str, Any]:
    """
    Scans Python files in the given directory using the AST (without executing code)
    to discover all FastAPI instances, APIRouters, and Pydantic BaseModel definitions.
    """
    base_path = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()

    if not base_path.exists() or not base_path.is_dir():
        return {
            "error": "DirectoryNotFound",
            "detail": f"Directory not found at resolved path: {base_path}",
        }

    apps: list[dict[str, str]] = []
    routers: list[dict[str, str]] = []
    models: list[dict[str, str]] = []

    for file_path in base_path.rglob("*.py"):
        # Check if any parent part is in ignored dirs
        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError, OSError) as e:
            logger.debug("Skipping unparseable file %s: %s", file_path, e)
            continue

        rel_path = file_path.relative_to(base_path)
        posix_rel = rel_path.as_posix()

        # Dot-notation module path candidate (e.g. src.api.routes)
        parts = list(rel_path.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts.pop()
        dot_module = ".".join(parts) if parts else rel_path.stem

        for node in ast.walk(tree):
            # 1. Look for assignments: app = FastAPI(...) or router = APIRouter(...)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(
                        node.value, ast.Call
                    ):
                        var_name = target.id
                        func_name = _get_func_name(node.value.func)
                        if func_name == "FastAPI":
                            apps.append(
                                {
                                    "target": f"{dot_module}:{var_name}",
                                    "file_target": f"{posix_rel}:{var_name}",
                                    "variable": var_name,
                                    "file": posix_rel,
                                    "type": "FastAPI",
                                }
                            )
                        elif func_name == "APIRouter":
                            routers.append(
                                {
                                    "target": f"{dot_module}:{var_name}",
                                    "file_target": f"{posix_rel}:{var_name}",
                                    "variable": var_name,
                                    "file": posix_rel,
                                    "type": "APIRouter",
                                }
                            )

            # 2. Look for factory functions returning FastAPI: def create_app() -> FastAPI:
            elif isinstance(node, ast.FunctionDef) and _is_fastapi_factory(node):
                apps.append(
                    {
                        "target": f"{dot_module}:{node.name}",
                        "file_target": f"{posix_rel}:{node.name}",
                        "variable": node.name,
                        "file": posix_rel,
                        "type": "FastAPIFactory",
                    }
                )

            # 3. Look for Pydantic classes: class User(BaseModel):
            elif isinstance(node, ast.ClassDef) and _inherits_from_base_model(node):
                models.append(
                    {
                        "target": f"{dot_module}:{node.name}",
                        "file_target": f"{posix_rel}:{node.name}",
                        "class": node.name,
                        "file": posix_rel,
                        "type": "PydanticModel",
                    }
                )

    return {
        "project_dir": str(base_path),
        "apps": apps,
        "routers": routers,
        "models": models,
        "summary": {
            "total_apps": len(apps),
            "total_routers": len(routers),
            "total_models": len(models),
        },
    }


def _get_func_name(node: ast.AST) -> str:
    """Extract name of called function (e.g. FastAPI or fastapi.FastAPI)."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _is_fastapi_factory(node: ast.FunctionDef) -> bool:
    """Detect if a function returns or creates a FastAPI instance."""
    # Check return annotation
    if node.returns:
        ret_name = _get_func_name(node.returns)
        if ret_name == "FastAPI":
            return True

    # Check function body for return FastAPI(...)
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Return)
            and child.value
            and isinstance(child.value, ast.Call)
            and _get_func_name(child.value.func) == "FastAPI"
        ):
            return True
    return False


def _inherits_from_base_model(node: ast.ClassDef) -> bool:
    """Check if class inherits from BaseModel or similar schema classes."""
    for base in node.bases:
        base_name = _get_func_name(base)
        if base_name in ("BaseModel", "SQLModel"):
            return True
    return False
