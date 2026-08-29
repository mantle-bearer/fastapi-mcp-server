"""FastMCP / MCPServer definition and registered tools for FastAPI codebase introspection."""

from typing import Any

# Robust cross-version compatibility for MCP SDK v1 and v2
try:
    from mcp.server.mcpserver import MCPServer as _FastMCPServer

    FastMCP: Any = _FastMCPServer
except (ImportError, ModuleNotFoundError, AttributeError):
    try:
        from mcp.server.fastmcp import (
            FastMCP as _FastMCPV1,  # type: ignore[attr-defined,no-redef]
        )

        FastMCP = _FastMCPV1
    except (ImportError, ModuleNotFoundError, AttributeError):
        from mcp.server import (
            FastMCP as _FastMCPFallback,  # type: ignore[attr-defined,no-redef]
        )

        FastMCP = _FastMCPFallback

from fastapi_mcp_server.inspector import (
    extract_openapi,
    extract_pydantic_schema,
    extract_routes,
    extract_typescript,
    extract_zod,
)
from fastapi_mcp_server.scanner import discover_project

# Initialize MCP Server
mcp = FastMCP(
    "fastapi-mcp-server",
    instructions="A Model Context Protocol server that introspects local FastAPI applications, APIRouters, live OpenAPI endpoints, and Pydantic schemas.",
)


@mcp.tool()
def get_openapi_schema(app_path: str, project_dir: str | None = None) -> Any:
    """
    Extract the complete OpenAPI schema from a local FastAPI app, APIRouter, factory function, or live HTTP URL.

    Args:
        app_path: Import string pointing to the target (e.g. 'main:app', 'routers.users:router', 'https://api.example.com/openapi.json').
        project_dir: Optional path to the project root directory. Defaults to current working directory.

    Returns:
        The OpenAPI specification dictionary or an error dictionary.
    """
    return extract_openapi(app_path, project_dir)


@mcp.tool()
def get_pydantic_schema(model_path: str, project_dir: str | None = None) -> Any:
    """
    Extract the JSON Schema from a local Pydantic BaseModel class definition.

    Args:
        model_path: Import string pointing to the Pydantic model (e.g. 'models.user:UserCreate', 'src/schemas.py:Item').
        project_dir: Optional path to the project root directory. Defaults to current working directory.

    Returns:
        The JSON schema dictionary for the Pydantic model or an error dictionary.
    """
    return extract_pydantic_schema(model_path, project_dir)


@mcp.tool()
def list_registered_routes(app_path: str, project_dir: str | None = None) -> Any:
    """
    List all registered HTTP routes, methods, operation IDs, summaries, and tags from a FastAPI app, APIRouter, or live URL.

    Args:
        app_path: Import string pointing to the target (e.g. 'main:app', 'routers.items:router', 'http://localhost:8000/docs').
        project_dir: Optional path to the project root directory. Defaults to current working directory.

    Returns:
        A list of registered routes or an error dictionary.
    """
    return extract_routes(app_path, project_dir)


@mcp.tool()
def get_typescript_definition(target: str, project_dir: str | None = None) -> Any:
    """
    Generate strict TypeScript interfaces and types from a Pydantic model, FastAPI app, or live OpenAPI URL.

    Args:
        target: Target identifier (e.g. 'models.user:UserProfile', 'main:app', 'https://api.example.com/openapi.json').
        project_dir: Optional path to the project root directory.

    Returns:
        TypeScript interface/type definitions code as a string, or an error dictionary.
    """
    return extract_typescript(target, project_dir)


@mcp.tool()
def get_zod_schema(target: str, project_dir: str | None = None) -> Any:
    """
    Generate Zod validation schemas with inferred TypeScript types from a Pydantic model, FastAPI app, or live OpenAPI URL.

    Args:
        target: Target identifier (e.g. 'models.user:UserProfile', 'main:app', 'https://api.example.com/openapi.json').
        project_dir: Optional path to the project root directory.

    Returns:
        Zod schema definition code as a string, or an error dictionary.
    """
    return extract_zod(target, project_dir)


@mcp.tool()
def discover_fastapi_project(project_dir: str | None = None) -> Any:
    """
    Automatically scan a project directory to discover all FastAPI apps, APIRouters, and Pydantic models.

    Args:
        project_dir: Optional path to the project root directory. Defaults to current working directory.

    Returns:
        A structured catalog listing all discovered apps, routers, and models with import target strings.
    """
    return discover_project(project_dir)
