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
)

# Initialize MCP Server
mcp = FastMCP(
    "fastapi-mcp-server",
    instructions="A Model Context Protocol server that introspects local FastAPI applications and Pydantic schemas.",
)


@mcp.tool()
def get_openapi_schema(app_path: str, project_dir: str | None = None) -> Any:
    """
    Extract the complete OpenAPI schema (paths, components, schemas) from a local FastAPI app instance.

    Args:
        app_path: Import string pointing to the FastAPI instance (e.g. 'main:app', 'src.api:app', 'app/main.py:app').
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
    List all registered HTTP routes, methods, operation IDs, summaries, and tags from a local FastAPI app.

    Args:
        app_path: Import string pointing to the FastAPI instance (e.g. 'main:app', 'src.api:app', 'app/main.py:app').
        project_dir: Optional path to the project root directory. Defaults to current working directory.

    Returns:
        A list of registered routes or an error dictionary.
    """
    return extract_routes(app_path, project_dir)
