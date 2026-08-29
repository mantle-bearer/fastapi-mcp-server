"""Dynamic module inspector and schema extractor for FastAPI and Pydantic targets."""

import importlib
import sys
import traceback
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel
from starlette.routing import Mount, Route, WebSocketRoute


def normalize_import_path(
    target_str: str, project_dir: str | None = None
) -> tuple[str, str, Path | None]:
    """
    Parse a target string into (module_name, attribute_name, directory_to_add_to_sys_path).

    Supports formats:
      - 'main:app'
      - 'src.api.main:app'
      - 'src/api/main.py:app'
      - '.\\src\\main.py:app'
    """
    if ":" not in target_str:
        raise ValueError(
            f"Invalid target format: '{target_str}'. Expected format is 'module:attribute' (e.g. 'main:app' or 'src/app.py:app')."
        )

    module_part, attr_name = target_str.split(":", 1)
    module_part = module_part.strip()
    attr_name = attr_name.strip()

    if not module_part or not attr_name:
        raise ValueError(
            f"Invalid target format: '{target_str}'. Both module and attribute must be non-empty."
        )

    # Determine base directory
    base_dir = Path(project_dir).resolve() if project_dir else Path.cwd().resolve()

    # Check if module_part is a file path (contains slashes or ends with .py)
    is_file_path = (
        "/" in module_part or "\\" in module_part or module_part.endswith(".py")
    )

    if is_file_path:
        # Convert path to resolved Path object
        file_path = (
            (base_dir / module_part).resolve()
            if not Path(module_part).is_absolute()
            else Path(module_part).resolve()
        )

        if not file_path.exists():
            raise FileNotFoundError(f"File not found at resolved path: {file_path}")

        # Compute relative module or directory to add to sys.path
        dir_to_add = file_path.parent
        module_name = file_path.stem
        return module_name, attr_name, dir_to_add
    else:
        # Standard python dot-notation
        return module_part, attr_name, base_dir


# Backward compatibility alias
_normalize_import_path = normalize_import_path


def resolve_target(target_str: str, project_dir: str | None = None) -> Any:
    """
    Dynamically import and resolve the target object from target_str.

    Guarantees cross-platform sys.path inclusion for the specified project directory.
    """
    module_name, attr_name, sys_dir = normalize_import_path(target_str, project_dir)

    if sys_dir:
        sys_dir_str = str(sys_dir)
        if sys_dir_str not in sys.path:
            sys.path.insert(0, sys_dir_str)

    # Ensure current working directory is also in sys.path
    cwd_str = str(Path.cwd().resolve())
    if cwd_str not in sys.path:
        sys.path.insert(1, cwd_str)

    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            f"Failed to import module '{module_name}'. Searched in sys.path: {sys.path[:5]}... Original error: {e}"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Error occurred while executing module '{module_name}': {e}\n{traceback.format_exc()}"
        ) from e

    if not hasattr(mod, attr_name):
        available_attrs = [a for a in dir(mod) if not a.startswith("_")]
        raise AttributeError(
            f"Module '{module_name}' has no attribute '{attr_name}'. Available attributes: {available_attrs}"
        )

    return getattr(mod, attr_name)


def extract_openapi(app_path: str, project_dir: str | None = None) -> dict[str, Any]:
    """Extract the OpenAPI specification dictionary from a FastAPI instance."""
    try:
        target = resolve_target(app_path, project_dir)
        app: FastAPI | None = None

        if isinstance(target, FastAPI):
            app = target
        elif callable(target) and not isinstance(target, type):
            # If it's a factory function, invoke it to obtain the FastAPI app
            potential_app = target()
            if isinstance(potential_app, FastAPI):
                app = potential_app

        if app is None:
            return {
                "error": "TypeError",
                "detail": f"Target '{app_path}' is {type(target).__name__}, expected a fastapi.FastAPI instance or factory function.",
            }

        return app.openapi()
    except Exception as e:  # noqa: BLE001
        return {
            "error": type(e).__name__,
            "detail": str(e),
        }


def extract_pydantic_schema(
    model_path: str, project_dir: str | None = None
) -> dict[str, Any]:
    """
    Extract the JSON Schema from a Pydantic BaseModel class.

    Compatible with both Pydantic v2 (model_json_schema) and v1 (schema).
    """
    try:
        model = resolve_target(model_path, project_dir)
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            return {
                "error": "TypeError",
                "detail": f"Target '{model_path}' is {type(model).__name__}, expected a subclass of pydantic.BaseModel.",
            }

        # Pydantic v2
        if hasattr(model, "model_json_schema"):
            return model.model_json_schema()
        # Pydantic v1 fallback
        elif hasattr(model, "schema"):
            return model.schema()
        else:
            return {
                "error": "SchemaGenerationError",
                "detail": f"Could not generate schema for model {model.__name__}.",
            }
    except Exception as e:  # noqa: BLE001
        return {
            "error": type(e).__name__,
            "detail": str(e),
        }


def extract_routes(
    app_path: str, project_dir: str | None = None
) -> list[dict[str, Any]] | dict[str, Any]:
    """Extract a simplified, structured list of all registered routes in a FastAPI application."""
    try:
        target = resolve_target(app_path, project_dir)
        app: FastAPI | None = None

        if isinstance(target, FastAPI):
            app = target
        elif callable(target) and not isinstance(target, type):
            potential_app = target()
            if isinstance(potential_app, FastAPI):
                app = potential_app

        if app is None:
            return {
                "error": "TypeError",
                "detail": f"Target '{app_path}' is {type(target).__name__}, expected a fastapi.FastAPI instance or factory function.",
            }

        routes_info: list[dict[str, Any]] = []

        def _traverse_routes(routes: Any, prefix: str = "") -> None:
            for route in routes:
                # Check for FastAPI 0.115+ _IncludedRouter
                if hasattr(route, "original_router") and hasattr(
                    route.original_router, "routes"
                ):
                    sub_prefix = prefix
                    include_ctx = getattr(route, "include_context", None)
                    if (
                        include_ctx is not None
                        and hasattr(include_ctx, "prefix")
                        and include_ctx.prefix
                    ):
                        sub_prefix = prefix + str(include_ctx.prefix)
                    _traverse_routes(route.original_router.routes, prefix=sub_prefix)
                    continue

                if isinstance(route, APIRoute):
                    route_path = prefix + (
                        route.path if route.path != "/" or not prefix else ""
                    )
                    routes_info.append(
                        {
                            "path": route_path or "/",
                            "name": route.name,
                            "methods": sorted(route.methods or []),
                            "operation_id": route.operation_id,
                            "summary": route.summary or "",
                            "description": route.description or "",
                            "tags": route.tags or [],
                            "deprecated": bool(route.deprecated),
                            "type": "HTTP",
                        }
                    )
                elif isinstance(route, WebSocketRoute):
                    route_path = prefix + (
                        route.path if route.path != "/" or not prefix else ""
                    )
                    routes_info.append(
                        {
                            "path": route_path or "/",
                            "name": route.name,
                            "methods": ["WEBSOCKET"],
                            "operation_id": getattr(route, "operation_id", None),
                            "summary": getattr(route, "summary", ""),
                            "tags": getattr(route, "tags", []),
                            "type": "WebSocket",
                        }
                    )
                elif isinstance(route, Mount):
                    mount_path = prefix + (route.path if route.path != "/" else "")
                    sub_routes = getattr(route, "routes", None)
                    app_routes = getattr(route.app, "routes", None)
                    if sub_routes:
                        _traverse_routes(sub_routes, prefix=mount_path)
                    elif app_routes:
                        _traverse_routes(app_routes, prefix=mount_path)
                    else:
                        routes_info.append(
                            {
                                "path": mount_path or "/",
                                "name": getattr(route, "name", "mount"),
                                "methods": ["ALL"],
                                "type": "Mount",
                            }
                        )
                elif isinstance(route, Route):
                    route_path = prefix + (
                        route.path if route.path != "/" or not prefix else ""
                    )
                    routes_info.append(
                        {
                            "path": route_path or "/",
                            "name": route.name,
                            "methods": sorted(route.methods or []),
                            "type": "StarletteRoute",
                        }
                    )

        _traverse_routes(app.routes)
        return routes_info
    except Exception as e:  # noqa: BLE001
        return {
            "error": type(e).__name__,
            "detail": str(e),
        }
