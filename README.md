# fastapi-mcp-server

A Model Context Protocol (MCP) server designed to give AI coding assistants direct, accurate introspection into local FastAPI applications and Pydantic models.

---

## Why this exists

When AI assistants generate API clients, write test cases, or add new endpoints, they often guess request bodies, query parameters, and route paths based on outdated training data or partial file views.

`fastapi-mcp-server` solves this by introspecting your actual running code structure on disk:

1. **OpenAPI Schema Introspection:** Generates the exact OpenAPI 3.1.0/3.0.x schema from your local `FastAPI` instance.
2. **Pydantic Model Schema Extraction:** Produces full JSON Schema definitions for any `BaseModel` class (supporting both Pydantic v2 and v1).
3. **Route Discovery:** Traverses full route trees, nested `APIRouter` instances, Starlette `Mount`s, and WebSocket endpoints.
4. **Resilient Module Resolution:** Handles both Python module notation (`app.main:app`) and direct filesystem paths (`src/api/server.py:app` / `.\src\app.py:app`), automatically resolving imports and `sys.path`.

---

## Installation & Running

### Using `uvx` (No installation needed)

```bash
uvx fastapi-mcp-server
```

### Using `pip`

```bash
pip install fastapi-mcp-server
```

### Running from source / development

```bash
git clone https://github.com/username/fastapi-mcp-server.git
cd fastapi-mcp-server
uv sync
uv run fastapi-mcp-server
```

---

## Editor & Client Configuration

### Zed IDE

Add to your Zed `settings.json` (`Ctrl + ,` or `Cmd + ,`):

```json
{
  "context_servers": {
    "fastapi-mcp-server": {
      "command": {
        "path": "uvx",
        "args": ["fastapi-mcp-server"]
      }
    }
  }
}
```

_For local workspace development without publishing:_

```json
{
  "context_servers": {
    "fastapi-mcp-server": {
      "command": {
        "path": "uv",
        "args": [
          "run",
          "--directory",
          "/path/to/fastapi-mcp-server",
          "fastapi-mcp-server"
        ]
      }
    }
  }
}
```

### Cursor

Go to **Cursor Settings** > **Features** > **MCP Servers** > **+ Add New MCP Server**:

- **Name:** `fastapi-mcp-server`
- **Type:** `command`
- **Command:** `uvx fastapi-mcp-server`

### VS Code (with MCP / Copilot)

Add to your VS Code user or workspace settings (`settings.json`):

```json
{
  "mcp": {
    "servers": {
      "fastapi-mcp-server": {
        "command": "uvx",
        "args": ["fastapi-mcp-server"]
      }
    }
  }
}
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fastapi-mcp-server": {
      "command": "uvx",
      "args": ["fastapi-mcp-server"]
    }
  }
}
```

---

## Available Tools

### 1. `get_openapi_schema`

Extracts the complete OpenAPI JSON schema from a local FastAPI app instance.

**Arguments:**

- `app_path` _(str, required)_: Path to the FastAPI instance or factory function.
  - Examples: `"main:app"`, `"src.api:app"`, `"src/api/server.py:app"`, `"app.factory:create_app"`
- `project_dir` _(str, optional)_: Absolute or relative path to the project root directory. Defaults to current working directory.

### 2. `get_pydantic_schema`

Extracts the JSON Schema from a Pydantic `BaseModel` class definition.

**Arguments:**

- `model_path` _(str, required)_: Path to the Pydantic model class.
  - Examples: `"models.user:UserCreate"`, `"src/schemas.py:Item"`
- `project_dir` _(str, optional)_: Path to the project root directory.

### 3. `list_registered_routes`

Provides a clean, structured summary of all registered routes, HTTP methods, operation IDs, summaries, and tags.

**Arguments:**

- `app_path` _(str, required)_: Path to the FastAPI instance.
- `project_dir` _(str, optional)_: Path to the project root directory.

---

## Error Handling

All tools return clean structured dictionaries rather than raising unhandled exceptions or crashing the MCP connection. If an import fails, a file is missing, or a target isn't a valid FastAPI app, the tool responds with:

```json
{
  "error": "ModuleNotFoundError",
  "detail": "Failed to import module 'src.main'. Searched in sys.path: [...]"
}
```

---

## Development & Testing

```bash
# Clone the repository
git clone https://github.com/username/fastapi-mcp-server.git
cd fastapi-mcp-server

# Install dependencies and setup environment
uv sync

# Run tests
uv run pytest

# Run type checker and linter
uv run basedpyright
uv run ruff check src tests
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
